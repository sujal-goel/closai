"""
Blueprint route — handles architecture retrieval, refinement & native service mapping.
"""
import uuid
import json
import logging
import re
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from routes.auth import get_current_user
from config import get_settings

from models.schemas import (
    BlueprintUpdateRequest, NativeMappingRequest,
    BlueprintResponse, NativeMappingResponse,
)
from services.gemini_service import call_gemini, score_providers, generate_explanation
from services.database import blueprints_collection, chats_collection, is_connected
from services.tavily_service import bulk_enrich_for_blueprint
from services.live_pricing_service import fetch_live_price_record

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_budget_inr(raw_budget) -> float | None:
    if raw_budget is None:
        return None
    if isinstance(raw_budget, (int, float)):
        return float(raw_budget)

    text = str(raw_budget).strip().lower().replace(",", "")
    if not text:
        return None

    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None

    value = float(match.group(1))
    if "k" in text:
        value *= 1000
    elif "lakh" in text:
        value *= 100000
    elif "million" in text:
        value *= 1000000

    return value


NATIVE_MAPPING_PROMPT = """
You are a cloud infrastructure specialist.
Given a generic architecture blueprint and a target cloud provider,
map each generic component to the BEST-FIT native service.

For each node, provide:
- native_service: The specific provider service name
- sku: The recommended SKU/tier hint (e.g., "t3.micro", "e2-micro", "Standard_B1s")
- estimated_monthly_cost_inr: null (will be filled by live pricing APIs)
- estimated_latency_ms: Typical latency/processing time (number, optional)
- sla_percentage: Availability SLA (e.g., "99.99")
- region_available: boolean
- notes: Any relevant caveats

Return JSON:
{
  "provider": "aws",
  "mappings": [
    {
      "generic_id": "n1",
      "generic_type": "api_gateway",
      "native_service": "Amazon API Gateway",
      "sku": "REST API",
      "estimated_monthly_cost_inr": null,
      "estimated_latency_ms": 15,
      "sla_percentage": "99.95",
      "region_available": true,
      "notes": "Includes 1M API calls/month in free tier"
    }
  ],
  "total_estimated_monthly_cost_inr": null,
  "validation_warnings": ["Some GPU instances may have limited availability in eu-west-1"]
}
"""


def _provider_label(provider: str) -> str:
    p = (provider or "").strip().lower()
    if p == "aws":
        return "AWS"
    if p == "gcp":
        return "GCP"
    if p == "azure":
        return "AZURE"
    return provider.upper()


def _live_price_target(provider: str, item: dict) -> tuple[str, str]:
    generic_type = (item.get("generic_type") or "").strip().lower()
    sku_hint = (item.get("sku") or "").strip()
    native_service = (item.get("native_service") or "").strip().lower()

    def pick_sku(default_value: str) -> str:
        # LLMs may return non-SKU labels (e.g., "REST API"). Keep only SKU-like hints.
        if re.search(r"[a-z]\d|standard_|db\.|micro|small|medium|large|xlarge", sku_hint.lower()):
            return sku_hint
        return default_value

    if provider == "AWS":
        if "rds" in native_service or "aurora" in native_service:
            return ("RDS", pick_sku("db.t3.micro"))
        if "s3" in native_service:
            return ("S3", "Standard")
        if generic_type in {"api_server", "gpu_worker", "background_worker"}:
            return ("EC2", pick_sku("t3.micro"))
        if generic_type in {"relational_database", "document_store"}:
            return ("RDS", pick_sku("db.t3.micro"))
        if generic_type in {"object_storage", "cdn"}:
            return ("S3", sku_hint or "Standard")
        return ("EC2", pick_sku("t3.micro"))

    if provider == "GCP":
        if "cloud sql" in native_service or "alloydb" in native_service:
            return ("Cloud SQL", pick_sku("db-f1-micro"))
        if "cloud storage" in native_service:
            return ("Cloud Storage", "Standard")
        if "run" in native_service or "app engine" in native_service:
            return ("Cloud Run", "Fully Managed")
        if "functions" in native_service:
            return ("Cloud Functions", "Tier 1")
        if generic_type in {"api_server", "gpu_worker", "background_worker"}:
            return ("Compute Engine", pick_sku("e2-micro"))
        if generic_type in {"relational_database", "document_store"}:
            return ("Cloud SQL", pick_sku("db-f1-micro"))
        if generic_type in {"object_storage", "cdn"}:
            return ("Cloud Storage", sku_hint or "Standard")
        return ("Compute Engine", pick_sku("e2-micro"))

    if provider == "AZURE":
        if "sql" in native_service:
            return ("Azure SQL", "Basic")
        if "blob" in native_service or "storage" in native_service:
            return ("Blob Storage", "Hot")
        if generic_type in {"api_server", "gpu_worker", "background_worker"}:
            return ("Virtual Machines", pick_sku("Standard_B1s"))
        if generic_type in {"relational_database", "document_store"}:
            return ("Azure SQL", sku_hint or "Basic")
        if generic_type in {"object_storage", "cdn"}:
            return ("Blob Storage", sku_hint or "Hot")
        return ("Virtual Machines", pick_sku("Standard_B1s"))

    return ("Compute", sku_hint or "default")


def _normalize_region_for_provider(provider: str, region: str) -> str:
    p = (provider or "").upper()
    r = (region or "").strip().lower()
    if not r:
        return region

    if p == "AWS":
        aws_map = {
            "eastus": "us-east-1",
            "westus2": "us-west-2",
            "westeurope": "eu-west-1",
            "asia-south1": "ap-south-1",
        }
        return aws_map.get(r, region)

    if p == "GCP":
        gcp_map = {
            "ap-south-1": "asia-south1",
            "us-east-1": "us-east1",
            "us-west-2": "us-west2",
            "eu-west-1": "europe-west1",
            "eastus": "us-east1",
            "westus2": "us-west2",
            "westeurope": "europe-west1",
        }
        return gcp_map.get(r, region)

    if p == "AZURE":
        azure_map = {
            "ap-south-1": "centralindia",
            "us-east-1": "eastus",
            "us-west-2": "westus2",
            "eu-west-1": "westeurope",
            "asia-south1": "centralindia",
        }
        return azure_map.get(r, region)

    return region


def _get_fallback_cost(generic_type: str) -> float:
    """Provides a realistic baseline monthly cost in INR if live fetching fails."""
    t = (generic_type or "").lower()
    if any(k in t for k in ["api", "function", "lambda", "worker", "gateway"]):
        return 150.0 # Base execution fees
    if any(k in t for k in ["database", "db", "store", "cache"]):
        return 2200.0 # Standard managed DB
    if any(k in t for k in ["bucket", "storage", "cdn"]):
        return 350.0 # Baseline storage
    return 850.0 # Default compute instance cost


@router.get("/blueprint/{blueprint_id}", response_model=BlueprintResponse)
async def get_blueprint(blueprint_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve a specific blueprint by ID."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database unavailable")

    doc = await blueprints_collection().find_one({"blueprintId": blueprint_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    return BlueprintResponse(
        blueprint_id=doc["blueprintId"],
        type=doc.get("type", "generic"),
        provider=doc.get("provider", "generic"),
        nodes=doc.get("nodes", []),
        edges=doc.get("edges", []),
        scores=doc.get("scores"),
        explanation=doc.get("explanation", ""),
        native_mapping=doc.get("native_mapping"),
        created_at=doc.get("createdAt", "").isoformat() if doc.get("createdAt") else None,
    )


@router.get("/blueprints/chat/{chat_id}")
async def get_blueprints_for_chat(chat_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve all blueprints associated with a chat session."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database unavailable")

    cursor = blueprints_collection().find({"chatId": chat_id}).sort("createdAt", -1)
    results = []
    async for doc in cursor:
        results.append({
            "blueprint_id": doc["blueprintId"],
            "type": doc.get("type", "generic"),
            "provider": doc.get("provider", "generic"),
            "node_count": len(doc.get("nodes", [])),
            "created_at": doc.get("createdAt", "").isoformat() if doc.get("createdAt") else None,
        })

    return {"chat_id": chat_id, "blueprints": results}


@router.post("/blueprint/update")
async def update_blueprint(req: BlueprintUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Step 11: User modifies generic architecture → re-score."""
    try:
        if not is_connected():
            raise HTTPException(status_code=503, detail="Database unavailable")

        blueprints = blueprints_collection()
        existing = await blueprints.find_one({"blueprintId": req.blueprint_id})

        if not existing:
            raise HTTPException(status_code=404, detail="Blueprint not found")

        # Re-score with updated nodes
        blueprint = {"nodes": req.nodes, "edges": req.edges}
        constraints = existing.get("constraints", {})
        scoring = await score_providers(blueprint, constraints)
        scoring.sort(key=lambda p: p.get("totalScore", 0), reverse=True)

        explanation = await generate_explanation(blueprint, constraints=constraints)

        await blueprints.update_one(
            {"blueprintId": req.blueprint_id},
            {
                "$set": {
                    "nodes": req.nodes,
                    "edges": req.edges,
                    "scores": {p["id"]: p for p in scoring},
                    "explanation": explanation,
                    "updatedAt": datetime.now(timezone.utc),
                }
            },
        )

        return {
            "blueprint_id": req.blueprint_id,
            "scoring": scoring,
            "explanation": explanation,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Blueprint update error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/blueprint/map-native", response_model=NativeMappingResponse)
async def map_to_native(req: NativeMappingRequest, current_user: dict = Depends(get_current_user)):
    """Steps 13-15: Native Translation → Service Mapping → Final Validation."""
    try:
        if not is_connected():
            raise HTTPException(status_code=503, detail="Database unavailable")

        blueprints = blueprints_collection()

        # Try finding by blueprintId first, then fall back to chatId
        existing = await blueprints.find_one({"blueprintId": req.blueprint_id})
        if not existing:
            # Fallback: find the latest blueprint for this chat
            existing = await blueprints.find_one(
                {"chatId": req.blueprint_id, "type": "generic"},
                sort=[("createdAt", -1)],
            )
        if not existing:
            raise HTTPException(status_code=404, detail="Blueprint not found")

        nodes = existing.get("nodes", [])

        # Enrich with latest market intel via Tavily
        market_data = {}
        try:
            market_data = await bulk_enrich_for_blueprint(
                nodes, providers=[req.provider], region=req.region
            )
        except Exception as e:
            logger.warning(f"Market intel enrichment failed (non-fatal): {e}")

        # Ask Gemini to map generic → native
        query = (
            f"Provider: {req.provider}\n"
            f"Region: {req.region}\n"
            f"Blueprint nodes: {json.dumps(nodes)}\n"
            f"Market intelligence: {json.dumps(market_data) if market_data else 'Not available'}"
        )

        mapping = await call_gemini(query, NATIVE_MAPPING_PROMPT, use_json=True)

        # Replace static estimates with live provider API pricing.
        settings = get_settings()
        provider_label = _provider_label(req.provider)
        mapping_items = mapping.get("mappings", []) if isinstance(mapping, dict) else []
        live_records = []
        computed_total = 0.0

        for item in mapping_items:
            service, instance_type = _live_price_target(provider_label, item)
            provider_region = _normalize_region_for_provider(provider_label, req.region)
            
            # 1. Try Live Price
            live_record = await fetch_live_price_record(
                provider=provider_label,
                service=service,
                region=provider_region,
                instance_type=instance_type,
                gcp_api_key=settings.gcp_billing_api_key,
            )
            
            if live_record:
                monthly_cost = float(live_record["price_per_hour"]) * 730.0
                item["estimated_monthly_cost_inr"] = round(monthly_cost, 2)
                item["pricing_engine"] = "live-provider-apis"
                item["live_price_source"] = {
                    "provider": live_record["provider"],
                    "service": live_record["service"],
                    "region": live_record["region"],
                    "instance_type": live_record["instance_type"],
                    "price_per_hour": live_record["price_per_hour"],
                    "currency": live_record["currency"],
                    "last_updated": live_record["last_updated"],
                }
                live_records.append(item["live_price_source"])
                computed_total += monthly_cost
            else:
                # 2. Apply Baseline Fallback
                fallback = _get_fallback_cost(item.get("generic_type", ""))
                item["estimated_monthly_cost_inr"] = fallback
                item["pricing_engine"] = "baseline-estimate"
                item["pricing_note"] = "Regional baseline"
                computed_total += fallback

        mapping["total_estimated_monthly_cost_inr"] = round(computed_total, 2)
        if live_records:
            mapping["pricing_records"] = live_records
            mapping["pricing_engine_global"] = "mixed-live-fallback"
        else:
            mapping["pricing_engine_global"] = "baseline-estimate"

        # Save native blueprint variant
        native_blueprint_id = str(uuid.uuid4())
        await blueprints.insert_one({
            "blueprintId": native_blueprint_id,
            "chatId": existing.get("chatId"),
            "parentId": existing.get("blueprintId"),
            "type": "native",
            "provider": req.provider,
            "region": req.region,
            "nodes": nodes,
            "edges": existing.get("edges", []),
            "native_mapping": mapping,
            "createdAt": datetime.now(timezone.utc),
        })

        total_cost = mapping.get("total_estimated_monthly_cost_inr")
        total_cost_value = float(total_cost) if isinstance(total_cost, (int, float)) else None
        budget_value = _parse_budget_inr(existing.get("constraints", {}).get("budget_monthly_inr"))

        within_budget = None
        budget_gap = None
        if budget_value is not None and total_cost_value is not None:
            within_budget = total_cost_value <= budget_value
            budget_gap = max(0.0, total_cost_value - budget_value)

            mapping["budget_monthly_inr"] = budget_value
            mapping["within_budget"] = within_budget
            mapping["budget_gap_inr"] = budget_gap
            if within_budget:
                mapping["budget_note"] = (
                    f"Proposed mapping fits the monthly budget (₹{budget_value:.2f})."
                )
            else:
                mapping["budget_note"] = (
                    f"Not feasible within budget. Required: ₹{total_cost_value:.2f}/mo, "
                    f"budget: ₹{budget_value:.2f}/mo, gap: ₹{budget_gap:.2f}/mo."
                )
                mapping["required_limitations"] = [
                    "Reduce to single-region deployment and remove multi-region failover.",
                    "Use only free-tier or shared compute/database SKUs.",
                    "Disable non-critical background jobs and premium observability add-ons.",
                ]

        return NativeMappingResponse(
            native_blueprint_id=native_blueprint_id,
            provider=req.provider,
            mapping=mapping,
            total_estimated_cost=total_cost,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Native mapping error")
        raise HTTPException(status_code=500, detail=str(e))
