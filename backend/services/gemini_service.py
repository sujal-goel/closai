"""
Gemini API Wrapper with exponential backoff (1s, 2s, 4s, 8s, 16s).
Handles intent classification, constraint extraction, blueprint generation,
and architectural explanation.
"""
import httpx
import json
import asyncio
import logging
import random
import hashlib
from config import get_settings

logger = logging.getLogger(__name__)

# ── Opik Observability ─────────────────────────────
try:
    from opik import Opik, track
    opik_client = Opik()
    HAS_OPIK = True
    logger.info("✅ Opik Observability integrated.")
except ImportError:
    HAS_OPIK = False
    logger.warning("⚠️ Opik not installed. Observability disabled.")
    # No-op decorator fallback
    def track(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

GEMINI_MODEL = "gemini-3-flash-preview"
AI_SEMAPHORE = asyncio.Semaphore(2)  # Limit concurrent AI calls
QUERY_CACHE = {}  # Simple in-memory cache


def _get_cache_key(user_query: str, system_prompt: str, use_json: bool) -> str:
    payload = f"{system_prompt}|{user_query}|{use_json}"
    return hashlib.md5(payload.encode()).hexdigest()

@track(name="call_llm_with_retry", metadata={"integration": "gemini_groq"})
async def call_llm_with_retry(
    user_query: str,
    system_prompt: str,
    use_json: bool = True,
    max_retries: int = 5
) -> dict | str:
    """
    Unified LLM caller with:
    1. Local caching
    2. Concurrent request throttling (Semaphore)
    3. Randomized exponential backoff
    4. Primary/Fallback provider logic
    """
    cache_key = _get_cache_key(user_query, system_prompt, use_json)
    if cache_key in QUERY_CACHE:
        logger.info("Serving LLM response from local cache.")
        return QUERY_CACHE[cache_key]

    settings = get_settings()
    
    async with AI_SEMAPHORE:
        for attempt in range(max_retries):
            # Decide provider
            provider = "gemini" if attempt < (max_retries // 2) else "groq"
            if provider == "groq" and not settings.has_groq:
                provider = "gemini" # Fallback back to gemini if groq not config

            try:
                if provider == "gemini":
                    result = await _execute_gemini_request(user_query, system_prompt, use_json)
                else:
                    result = await _call_groq_internal(user_query, system_prompt, use_json)
                
                # Success! Cache and return
                QUERY_CACHE[cache_key] = result
                return result

            except Exception as e:
                is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
                
                if attempt == max_retries - 1:
                    logger.error(f"Final attempt failed: {e}")
                    raise

                # Calculate wait time: 2, 4, 8, 16... with jitter
                wait_time = (2 ** attempt) + (random.random() * 2)
                if is_rate_limit:
                    wait_time += 10 # Extra penalty for rate limits
                    logger.warning(f"Rate limit hit ({provider}). Waiting {wait_time:.1f}s (Attempt {attempt+1}/{max_retries})")
                else:
                    logger.warning(f"LLM Error ({provider}): {e}. Retrying in {wait_time:.1f}s...")
                
                await asyncio.sleep(wait_time)

async def _execute_gemini_request(
    user_query: str,
    system_prompt: str,
    use_json: bool = True,
) -> dict | str:
    settings = get_settings()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={settings.gemini_api_key}"
    )

    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }
    if use_json:
        payload["generationConfig"] = {"responseMimeType": "application/json"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()

        result = response.json()
        text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if not text:
            raise ValueError("Empty response from Gemini")
            
        return json.loads(text) if use_json else text

async def _call_groq_internal(
    user_query: str,
    system_prompt: str,
    use_json: bool = True,
) -> dict | str:
    settings = get_settings()
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    }
    if use_json:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.groq_api_key}"
            },
        )
        response.raise_for_status()
        result = response.json()
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not text:
            raise ValueError("Empty response from Groq")
            
        return json.loads(text) if use_json else text

async def call_gemini(user_query: str, system_prompt: str, use_json: bool = True) -> dict | str:
    """Legacy wrapper for consistency across routes."""
    return await call_llm_with_retry(user_query, system_prompt, use_json)


# ────────────────────────────────────────────────────────────
# Domain-specific prompts for the 16-step pipeline
# ────────────────────────────────────────────────────────────

INTENT_SYSTEM_PROMPT = """
You are an elite Principal Cloud Architect and System Design Expert.
Analyze the user request and extract deep infrastructure constraints and Non-Functional Requirements (NFRs).
CRITICAL: All financial discussions, budget constraints, and cost estimations MUST be in Indian Rupees (₹). Even if the user mentions $, internally convert and refer to it as ₹ (1:83).

Classification: Classify the workload into one of these categories:
web_app, ai_ml, data_pipeline, gaming, iot, ecommerce, saas, media_streaming, devops, other.

Also classify the deployment stage: development, staging, production.

Constraints & NFRs: Extract the following if mentioned:
- region (e.g., "us-east-1", "eu-west-1")
- gpu (boolean)
- scale ("low", "medium", "high", "auto")
- budget_monthly_inr (number)
- compliance (array of standards like "hipaa", "gdpr", "soc2", "pci-dss")
- availability_sla (e.g., "99.99%", "99.9%")
- rto_rpo_objective (e.g., "near-zero", "24 hours")
- preferred_provider ("aws", "gcp", "azure", or null)
- latency_budget_ms (number)

Gap Detection: For each field, assign a status:
- KNOWN: Explicitly stated by user
- INFERRED: Reasonably inferred from context
- MISSING: Not mentioned and cannot be inferred

Confidence: Assign 0.0-1.0.

Follow Up: If budget is missing, you MUST ask for it as the primary blocker. If other critical NFRs (like SLA or Scale) are missing for a production environment, ask a surgically precise question. 
Return budget_monthly_inr as a number (convert ₹ to $ at 1:83 if needed). Mark missing budget as "CRITICAL_MISSING" in the internal logic.

Return JSON:
{
  "intent": "ai_ml",
  "stage": "production",
  "constraints": {
    "region": {"value": "us-east-1", "status": "KNOWN"},
    "availability_sla": {"value": "99.99%", "status": "MISSING"}
  },
  "confidence": 0.85,
  "missing_critical": ["availability_sla"],
  "follow_up_question": "To design the cross-region failover properly, what is your target SLA (e.g., 99.99%) and RPO/RTO?"
}
"""

BLUEPRINT_SYSTEM_PROMPT = """
You are a Principal System Design Expert. Based on the workload intent and constraints,
generate an ELITE, production-grade GENERIC architecture blueprint. Do not build trivial 3-tier apps if the constraints demand high availability/high scale.

CRITICAL INSTRUCTION: Analyze any "### SYSTEM DESIGN THEORY CONTEXT ###" provided in the prompt. Internalize these principles exactly before deciding which components to place and how to wire them. 

Think deeply about:
- CAP Theorem trade-offs (e.g., using NoSQL for AP vs Relational for CP).
- Idempotency and asynchronous event choreography.
- Read replicas vs multi-region active-active clusters.
- Edge caching and CDN routing.

Available component types:
Compute: api_server, gpu_worker, background_worker, scheduler
Data: relational_database, document_store, cache, object_storage, data_warehouse
Network: api_gateway, load_balancer, cdn, message_queue
Security/Observability: auth_service, secrets_manager, logging, metrics, alerting

Category mapping for styling:
- "compute" for: api_server, gpu_worker, background_worker, scheduler
- "data" for: relational_database, document_store, cache, object_storage, data_warehouse
- "network" for: api_gateway, load_balancer, cdn, message_queue
- "security" for: auth_service, secrets_manager, logging, metrics, alerting

Layout rules:
- Place nodes on a grid. x ranges from 150 to 850, y ranges from 100 to 700.
- Network components go at the top (y: 100-200).
- Compute components in the middle (y: 250-400).
- Security/Observability (specifically auth_service) must go BEFORE data (y: 450).
- Data components go at the bottom (y: 550-650).
- Logging/Metrics can remain at the very bottom (y: 700).
- Space nodes horizontally at least 160px apart.

Return JSON:
{
  "nodes": [
    {"id": "n1", "type": "api_gateway", "category": "network", "x": 500, "y": 100, "label": "API Gateway"}
  ],
  "edges": [
    {"source": "n1", "target": "n2"}
  ]
}
"""

SUMMARY_SYSTEM_PROMPT = """
You are a conversation memory manager. 
Distill the following cloud architecture design session into a concise "Conversation State" block.
Include:
- User intent and workload type
- Confirmed constraints (region, scale, budget, etc.)
- Key architectural decisions made so far
- Remaining open questions

Output format: Concise string summary.
"""

SCORING_SYSTEM_PROMPT = """
You are an expert Cloud Cost Analyst and Principal Engineer. Given a generic architecture blueprint, workload constraints, and real-time DAILY market intelligence,
score each major cloud provider (AWS, GCP, Azure) across 7 dimensions.
CRITICAL: All cost analysis and reasoning text MUST utilize Indian Rupees (₹). Conversion factor: 1 USD = 83 INR. Do NOT use $ in the reasoning field.

CRITICAL INSTRUCTION: You MUST adjust your scores directly based on the "Market Intelligence" provided below. This data is pulled fresh every 24 hours. 
If an outage or a new VM series is mentioned, factor it into reliability or cost_efficiency immediately.

Dimensions and their weights:
1. cost_efficiency (25%) - Estimated monthly cost competitiveness
2. ops_complexity (20%) - Managed services availability, DevOps overhead
3. scalability (15%) - Auto-scaling capabilities, serverless options
4. reliability (15%) - SLA guarantees, cross-region replication
5. compliance (10%) - Certifications, data residency options
6. ecosystem (10%) - Integration breadth, marketplace, community
7. future_roadmap (5%) - Innovation pace, AI/ML investment, new features

Score each dimension from 0 to 100. Compute a weighted totalScore.

Return JSON:
{
  "providers": [
    {
      "id": "aws",
      "name": "Amazon Web Services",
      "totalScore": 87,
      "dimensions": {
        "cost_efficiency": 82, "ops_complexity": 88, "scalability": 92,
        "reliability": 95, "compliance": 90, "ecosystem": 85, "future_roadmap": 80
      },
      "reasoning": "Scored highest due to robust message queuing and DB reliability. Factored in today's pricing intel."
    }
  ]
}
"""

EXPLAINER_SYSTEM_PROMPT = """
You are a Principal System Design Expert writing for a CTO audience.
Given a cloud architecture blueprint, relevant theoretical context from our knowledge base, and DISTILLED MARKET INTELLIGENCE (actual limits, compliance, performance), provide EXACTLY 5 sentences utilizing advanced engineering terminology.

CRITICAL: You MUST use the provided Market Intelligence to state:
1. **Expected Latency**: Based on provider limits or theoretical minimums for the chosen services.
2. **Concurrency**: Estimate how many concurrent users this specific architecture can handle (e.g., "10k concurrent users").
3. **Total User Capacity**: Estimate daily/monthly total user capacity.
4. **Compliance**: State explicitly what compliance standards are met (e.g., SOC2, HIPAA).
5. **Future Scalability**: Explain how it scales (auto-scaling, horizontal shards).

CRITICAL: All cost references in the explanation MUST be in Indian Rupees (₹). conversion is 1:83.
CRITICAL BUDGET RULE: If constraints include budget_monthly_inr, you MUST explicitly validate feasibility against that budget.

1. System functionality and consistency model achieved.
2. The caching tier or data ingestion strategy, referencing specific design theory.
3. Performance profile: State EXPLICIT numbers for latency and concurrent users based on the MARKET INTELLIGENCE if provided.
4. Failover domains, chosen RTO/SLA, and COMPLIANCE status (SOC2/HIPAA/GDPR).
5. Scalability path and architectural trade-off accepted (CAP theorem implication).

CRITICAL: If "### SYSTEM DESIGN THEORY CONTEXT ###" is present, weave at least one principle from it.
CRITICAL: If "### DISTILLED MARKET INTEL ###" is present, you MUST use the concrete limits/metrics from it.

PROS: [2 concise high-level bullet points]
CONS: [2 concise high-level bullet points]
"""


@track(name="classify_intent")
async def classify_intent(user_message: str) -> dict:
    """Step 2: Intent Classification & Constraint Extraction."""
    result = await call_gemini(user_message, INTENT_SYSTEM_PROMPT, use_json=True)
    if isinstance(result, list):
        return result[0] if result else {}
    return result


@track(name="generate_blueprint")
async def generate_blueprint(intent: str, constraints: dict, theory_context: str = "") -> dict:
    """Step 8: Generic Blueprint Generation with Local RAG."""
    query = f"Workload type: {intent}\nConstraints: {json.dumps(constraints)}"
    if theory_context:
        query += f"\n\n{theory_context}"
        
    result = await call_gemini(query, BLUEPRINT_SYSTEM_PROMPT, use_json=True)
    if isinstance(result, list):
        # Fallback if Gemini just returns nodes directly in a list
        return {"nodes": result, "edges": []}
    return result


@track(name="score_providers")
async def score_providers(blueprint: dict, constraints: dict, market_intel: str = "", theory_context: str = "") -> list:
    """Step 9: Immediate Scoring across all providers."""
    query = (
        f"Blueprint: {json.dumps(blueprint)}\n"
        f"Constraints: {json.dumps(constraints)}\n"
        f"Market Intelligence: {market_intel}\n"
        f"System Design Theory Context: {theory_context}"
    )
    raw_result = await call_gemini(query, SCORING_SYSTEM_PROMPT, use_json=True)
    
    # Normalize results
    providers = []
    if isinstance(raw_result, list):
        providers = raw_result
    elif isinstance(raw_result, dict):
        providers = raw_result.get("providers", [])
    
    # Ensure each provider has an 'id'
    normalized = []
    for p in providers:
        if not isinstance(p, dict):
            continue
            
        if "id" not in p:
            # Derive ID from name if possible, or use a default
            name = p.get("name", "").lower()
            if "amazon" in name or "aws" in name:
                p["id"] = "aws"
            elif "google" in name or "gcp" in name:
                p["id"] = "gcp"
            elif "azure" in name or "microsoft" in name or "msoft" in name:
                p["id"] = "azure"
            else:
                p["id"] = name.replace(" ", "_").strip("_") or f"provider_{len(normalized)}"
        
        normalized.append(p)
    
    return normalized


async def summarize_history(history: list[dict], existing_summary: str = "") -> str:
    """Compact history into a single summary block."""
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history])
    query = f"Existing Summary: {existing_summary}\n\nRecent Messages:\n{history_text}"
    return await call_gemini(query, SUMMARY_SYSTEM_PROMPT, use_json=False)


@track(name="generate_explanation")
async def generate_explanation(blueprint: dict, constraints: dict | None = None, theory_context: str = "", market_intel: str = "") -> str:
    """Step 16: 5-sentence architectural explanation, grounded in theory and actual market limits."""
    query = f"Architecture blueprint: {json.dumps(blueprint)}"
    if constraints:
        query += f"\nConstraints: {json.dumps(constraints)}"
    if theory_context:
        query += f"\n\n### SYSTEM DESIGN THEORY CONTEXT ###\n{theory_context}"
    if market_intel:
        query += f"\n\n### DISTILLED MARKET INTEL ###\n{market_intel}"
        
    return await call_llm_with_retry(query, EXPLAINER_SYSTEM_PROMPT, use_json=False)


async def fetch_market_intel_documents(provider: str, service_names: list[str]) -> list:
    """Fetch raw distilled intelligence documents from MongoDB."""
    from services.database import market_intel_collection
    if not provider or not service_names:
        return []
    
    try:
        # Normalize provider name for regex
        provider_clean = provider.split('_')[0] # aws, gcp, azure
        query = {
            "type": "distilled_intel",
            "provider": {"$regex": provider_clean, "$options": "i"},
            "data.service": {"$in": service_names}
        }
        cursor = market_intel_collection().find(query)
        return await cursor.to_list(length=10)
    except Exception as e:
        logger.warning(f"Failed to fetch market intel docs: {e}")
        return []

async def get_relevant_market_intel(provider: str, service_names: list[str]) -> str:
    """Helper to fetch distilled intelligence from MongoDB for the prompt wrapper."""
    results = await fetch_market_intel_documents(provider, service_names)
    if not results:
        return ""
    
    intel_str = ""
    for res in results:
        data = res.get("data", {})
        intel_str += f"\n- {data.get('provider')} {data.get('service')}:\n"
        intel_str += f"  Free Tier: {data.get('free_tier_details')}\n"
        intel_str += f"  Limits: {json.dumps(data.get('usage_limits'))}\n"
        intel_str += f"  Performance: {json.dumps(data.get('performance'))}\n"
        intel_str += f"  Compliance: {json.dumps(data.get('compliance'))}\n"
        
    return intel_str
