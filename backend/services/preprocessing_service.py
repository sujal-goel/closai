"""
Preprocessing Service for Cloud Intelligence.
Uses Gemini to distill raw crawled text into structured ServiceIntel models.
"""
import hashlib
import re
import logging
from datetime import datetime, timezone
from typing import Optional

from services.gemini_service import call_gemini
from models.schemas import ServiceIntel, PerformanceMetrics, ComplianceInfo

logger = logging.getLogger(__name__)

DISTILLATION_PROMPT = """
You are a Cloud Infrastructure Analyst. Your task is to extract strictly useful structured data from the provided raw documentation or policy text.
Focus on:
1. Free Tier details (quotas, request limits, bandwidth, etc.)
2. Usage limits / Hard limits (e.g. 50 services per project, 1TB storage limit)
3. Performance metrics (latency, throughput, concurrent user capacity if mentioned)
4. Compliance (SOC2, HIPAA, GDPR, ISO)
5. Regions supported
6. Paid offering summary (what triggers the first paid tier?)

Return ONLY a JSON object adhering to this schema:
{
    "provider": "Provider Name",
    "service": "Service Name",
    "free_tier_details": "Brief summary of free tier",
    "usage_limits": { "limit_name": "value" },
    "performance": {
        "latency_ms": 100, 
        "throughput": "text description",
        "concurrent_users_limit": 1000,
        "scalability": "highly scalable / manual / etc"
    },
    "compliance": {
        "certifications": ["SOC2", "HIPAA"],
        "regions_supported": ["us-east-1", "global"]
    },
    "paid_offerings_summary": "Summary of paid triggers"
}

If a field is unknown, omit it or set to null. Do not hallucinate.
"""


def calculate_content_hash(text: str) -> str:
    """Returns MD5 hash of text for change detection."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def heuristic_distill(provider: str, service: str, text: str) -> Optional[ServiceIntel]:
    """
    Tries to extract basic cloud metrics using regex/heuristics to save API credits.
    """
    # ── 1. Compliance (SOC2, HIPAA, GDPR, PCI-DSS) ──
    certs = re.findall(r"(SOC2|HIPAA|GDPR|PCI-DSS|ISO\s\d+)", text, re.I)
    certs = list(set([c.upper() for c in certs]))

    # ── 2. Regions (Generic search for common region patterns) ──
    regions = re.findall(r"(us-[a-z]+-\d|eu-[a-z]+-\d|ap-[a-z]+-\d)", text, re.I)
    regions = list(set([r.lower() for r in regions]))

    # ── 3. Latency/Concurrency (Numbers near keywords) ──
    latency_match = re.search(r"(\d+)\s?(ms|milliseconds?)\s?(latency|response)", text, re.I)
    concurrency_match = re.search(r"(\d+)\s?(concurrent|simultaneous)\s?(users|requests)", text, re.I)

    # Heuristic: We only return if we found enough meat to be useful
    if not certs and not regions and not latency_match:
        return None

    return ServiceIntel(
        provider=provider,
        service=service,
        free_tier_details="Extracted via local heuristics",
        usage_limits={},
        performance=PerformanceMetrics(
            latency_ms=int(latency_match.group(1)) if latency_match else None,
            concurrent_users_limit=int(concurrency_match.group(1)) if concurrency_match else None,
            scalability="Auto" if "autoscaling" in text.lower() else "Unknown"
        ),
        compliance=ComplianceInfo(
            certifications=certs,
            regions_supported=regions
        ),
        paid_offerings_summary="Check official pricing for details"
    )

async def distill_service_data(provider: str, service: str, raw_text: str) -> Optional[ServiceIntel]:
    """
    Takes raw text and tries:
    1. Heuristic Distillation (Regex) -> 0 credits
    2. Gemini Distillation (LLM) -> fallback
    """
    if not raw_text or len(raw_text.strip()) < 50:
        logger.warning(f"Raw text too short for distillation for {provider}:{service}")
        return None

    # Step 1: Try Heuristics first
    heuristic_res = heuristic_distill(provider, service, raw_text)
    if heuristic_res and len(heuristic_res.compliance.certifications) > 2:
        # If we found a lot of certs, we assume heuristic is decent enough
        logger.info(f"Using heuristic distillation for {provider}:{service}")
        heuristic_res.last_updated = datetime.now(timezone.utc)
        return heuristic_res

    # Step 2: Fallback to Gemini
    try:
        user_input = f"Provider: {provider}\nService: {service}\n\nRAW TEXT:\n{raw_text[:8000]}"
        
        distilled_data = await call_gemini(
            user_query=user_input,
            system_prompt=DISTILLATION_PROMPT,
            use_json=True
        )

        if not distilled_data:
            return None

        # Ensure minimal fields
        distilled_data["provider"] = provider
        distilled_data["service"] = service
        distilled_data["last_updated"] = datetime.now(timezone.utc)

        return ServiceIntel(**distilled_data)

    except Exception as e:
        logger.error(f"Distillation failed for {provider}:{service}: {e}")
        return None
