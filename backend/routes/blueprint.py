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

from models.schemas import (
    BlueprintUpdateRequest, NativeMappingRequest,
    BlueprintResponse, NativeMappingResponse,
)
from services.gemini_service import call_gemini, score_providers, generate_explanation
from services.database import blueprints_collection, chats_collection, is_connected
from services.tavily_service import bulk_enrich_for_blueprint

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

Mapping examples:
- api_gateway → AWS: "Amazon API Gateway", GCP: "Apigee / Cloud Endpoints", Azure: "Azure API Management"
- api_server → AWS: "ECS Fargate / App Runner", GCP: "Cloud Run", Azure: "Azure Container Apps"
- gpu_worker → AWS: "EC2 P4d / SageMaker", GCP: "Vertex AI / A2 VMs", Azure: "NC-series VMs"
- relational_database → AWS: "RDS Aurora", GCP: "Cloud SQL / AlloyDB", Azure: "Azure SQL"
- message_queue → AWS: "SQS", GCP: "Pub/Sub", Azure: "Service Bus"
- object_storage → AWS: "S3", GCP: "Cloud Storage", Azure: "Blob Storage"
- cache → AWS: "ElastiCache", GCP: "Memorystore", Azure: "Azure Cache for Redis"
- auth_service → AWS: "Cognito", GCP: "Firebase Auth / Identity Platform", Azure: "Azure AD B2C"
- load_balancer → AWS: "ALB / NLB", GCP: "Cloud Load Balancing", Azure: "Azure Load Balancer"
- cdn → AWS: "CloudFront", GCP: "Cloud CDN", Azure: "Azure CDN"
- logging → AWS: "CloudWatch Logs", GCP: "Cloud Logging", Azure: "Azure Monitor Logs"
- metrics → AWS: "CloudWatch Metrics", GCP: "Cloud Monitoring", Azure: "Azure Monitor"
- alerting → AWS: "CloudWatch Alarms + SNS", GCP: "Cloud Alerting", Azure: "Azure Alerts"
- secrets_manager → AWS: "Secrets Manager", GCP: "Secret Manager", Azure: "Key Vault"
- scheduler → AWS: "EventBridge Scheduler", GCP: "Cloud Scheduler", Azure: "Logic Apps"
- background_worker → AWS: "Lambda / Step Functions", GCP: "Cloud Tasks / Workflows", Azure: "Azure Functions"
- document_store → AWS: "DynamoDB", GCP: "Firestore", Azure: "Cosmos DB"
- data_warehouse → AWS: "Redshift", GCP: "BigQuery", Azure: "Synapse Analytics"

For each node, provide:
- native_service: The specific provider service name
- sku: The recommended SKU/tier (e.g., "db.r6g.large")
- estimated_monthly_cost_inr: Best estimate
- estimated_latency_ms: Typical latency/processing time (number)
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
      "estimated_monthly_cost_inr": 35,
      "estimated_latency_ms": 15,
      "sla_percentage": "99.95",
      "region_available": true,
      "notes": "Includes 1M API calls/month in free tier"
    }
  ],
  "total_estimated_monthly_cost_inr": 1250,
  "validation_warnings": ["Some GPU instances may have limited availability in eu-west-1"]
}
"""


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
