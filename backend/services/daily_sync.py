"""
Autonomous daily synchronization service.
Dynamically discovers cloud providers, searches for their official documentation URLs, 
and leverages the Tavily Extract API to deeply crawl their raw policies and SLA limits.
"""
import asyncio
import logging
import json
from datetime import datetime, timezone

import hashlib
import os

from config import get_settings
from services.database import is_connected, market_intel_collection
from services.gemini_service import call_gemini

logger = logging.getLogger(__name__)

INITIAL_DELAY_SECONDS = 15
SYNC_INTERVAL_SECONDS = 604800  # 1 week (user requested reduction)

DISCOVERY_PROMPT = """
You are a Cloud Technology Researcher. Identify exactly these 8 providers: AWS, GCP, Azure, Hyperstack (GPU Cloud), Vercel, Render, Railway, Netlify.
For each provider, list exactly their 3 most critical flagship services (e.g. 1 compute/serverless, 1 database, 1 storage/hosting).
Return JSON adhering strictly to this schema:
{
    "providers": [
        {
            "name": "Provider Name",
            "services": ["Service1", "Service2", "Service3"]
        }
    ]
}
"""


async def get_tavily_client():
    settings = get_settings()
    if not settings.has_tavily:
        return None
    try:
        from tavily import AsyncTavilyClient
        return AsyncTavilyClient(api_key=settings.tavily_api_key)
    except ImportError:
        try:
            from tavily import TavilyClient
            return TavilyClient(api_key=settings.tavily_api_key)
        except ImportError:
            return None


async def discover_cloud_landscape():
    """Use Gemini to dynamically discover what tools are heavily used right now."""
    logger.info("Autonomously discovering current cloud landscape...")
    try:
        result = await call_gemini(
            user_query="Identify the top cloud providers and their flagship services.",
            system_prompt=DISCOVERY_PROMPT,
            use_json=True
        )
        if isinstance(result, list):
            return result[0].get("providers", []) if result else []
        return result.get("providers", [])
    except Exception as e:
        logger.error(f"Failed to discover cloud landscape: {e}")
        return []


async def execute_single_sync():
    """
    Performs one full execution of the cloud policy crawl.
    Returns True if successful, False otherwise.
    """
    try:
        settings = get_settings()
        if not is_connected() or not settings.has_tavily:
            logger.warning("DB disconnected or Tavily missing. Skipping daily sync.")
            return False

        from services.database import market_intel_collection
        collection = market_intel_collection()

        # ── 1. Check if sync is needed (optional for cron, but good for safety) ──
        last_sync = await collection.find_one({"type": "macro_pulse"})
        if last_sync and last_sync.get("fetched_at"):
            fetched_at = last_sync["fetched_at"]
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=timezone.utc)
            time_since_sync = (datetime.now(timezone.utc) - fetched_at).total_seconds()
            if time_since_sync < SYNC_INTERVAL_SECONDS - 3600: # 1h buffer
                logger.info(f"Sync skipped. Last crawl was {int(time_since_sync/3600)}h ago.")
                return True

        # ── 2. Discovery & Crawling ──
        client = await get_tavily_client()
        if not client:
            logger.warning("Tavily client init failed.")
            return False

        providers = await discover_cloud_landscape()
        if not providers:
            logger.warning("No providers discovered.")
            return False

        from services.preprocessing_service import distill_service_data

        from services.preprocessing_service import distill_service_data, calculate_content_hash

        # ── 3. Load Static Registry for URL Optimization ──
        registry_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "cloud_registry.json")
        registry = {}
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r") as f:
                    registry = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")

        logger.info(f"Discovered providers: {[p['name'] for p in providers]}")
        extracted_knowledge = []

        for provider in providers:
            provider_name = provider.get("name")
            # Normalize name for registry lookup
            registry_key = next((k for k in registry.keys() if k.lower() in provider_name.lower()), None)
            
            for service in provider.get("services", []):
                # ── Search Strategy Optimization ──
                urls_to_extract = []
                
                # Try to get verified URL from registry first (saves 1 search call)
                if registry_key and service in registry[registry_key].get("services", {}):
                    urls_to_extract = [registry[registry_key]["services"][service]["url"]]
                    logger.info(f"Using registry URL for {provider_name} : {service}")

                if not urls_to_extract:
                    # Fallback to search only if unknown
                    search_query = f"{provider_name} {service} official documentation free tier usage limits SLA compliance"
                    try:
                        search_call = client.search(query=search_query, search_depth="basic", max_results=2)
                        search_res = await search_call if asyncio.iscoroutine(search_call) else search_call
                        urls_to_extract = [r["url"] for r in search_res.get("results", []) if "url" in r]
                    except Exception as e:
                        logger.warning(f"Tavily search failed for {service}: {e}")

                if not urls_to_extract:
                    continue
                        
                try:
                    extract_call = client.extract(urls=urls_to_extract)
                    extract_res = await extract_call if asyncio.iscoroutine(extract_call) else extract_call
                    extract_results = extract_res.get("results", []) if isinstance(extract_res, dict) else extract_res
                    
                    raw_combined_text = ""
                    for doc in extract_results:
                        raw_combined_text += (doc.get("raw_content", "") or doc.get("text", "")) + "\n"
                    
                    if not raw_combined_text:
                        continue

                    # ── Hash-Based Change Detection (Saves Gemini credits) ──
                    content_hash = calculate_content_hash(raw_combined_text)
                    existing_doc = await collection.find_one({
                        "type": "distilled_intel", 
                        "provider": provider_name, 
                        "service": service
                    })
                    
                    if existing_doc and existing_doc.get("raw_hash") == content_hash:
                        logger.info(f"No changes detected for {provider_name} {service}. Skipping distillation.")
                        continue

                    # ── Distillation Step ──
                    logger.info(f"Content changed or new. Distilling data for {provider_name} : {service}...")
                    distilled_intel = await distill_service_data(provider_name, service, raw_combined_text)

                    if distilled_intel:
                        intel_dict = distilled_intel.dict()
                        intel_dict["type"] = "distilled_intel"
                        
                        await collection.update_one(
                            {"type": "distilled_intel", "provider": provider_name, "service": service},
                            {
                                "$set": {
                                    "data": intel_dict,
                                    "raw_hash": content_hash,
                                    "urls_scraped": urls_to_extract,
                                    "fetched_at": datetime.now(timezone.utc),
                                }
                            },
                            upsert=True,
                        )
                        extracted_knowledge.append(f"Updated intel for {provider_name} {service}.")
                        
                except Exception as e:
                    logger.warning(f"Failed to crawl/distill {provider_name} {service}: {e}")

        logger.info("Crawl complete. Updating master pulse document.")
        master_summary = "\n".join(extracted_knowledge) if extracted_knowledge else "No new data distilled."
        await collection.update_one(
            {"type": "macro_pulse"},
            {
                "$set": {
                    "data": master_summary,
                    "fetched_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        return True

    except Exception as e:
        logger.error(f"Error during Autonomous Cloud Policy Crawl: {e}")
        return False


async def sync_daily_market_pulse():
    """
    Background task wrapper for local persistent execution.
    """
    await asyncio.sleep(INITIAL_DELAY_SECONDS)
    
    while True:
        await execute_single_sync()
        # Wait 24 hours
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)
