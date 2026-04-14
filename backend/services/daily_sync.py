"""
Autonomous daily synchronization service.
Dynamically discovers cloud providers, searches for their official documentation URLs, 
and leverages the Tavily Extract API to deeply crawl their raw policies and SLA limits.
"""
import asyncio
import logging
import json
from datetime import datetime, timezone

from config import get_settings
from services.database import is_connected
from services.gemini_service import call_gemini

logger = logging.getLogger(__name__)

INITIAL_DELAY_SECONDS = 15
SYNC_INTERVAL_SECONDS = 86400  # 24 hours

DISCOVERY_PROMPT = """
You are a Cloud Technology Researcher. Identify strictly the top 3 dominant public cloud providers dominating the enterprise market right now.
For each provider, list exactly their 3 most critical flagship services (e.g. 1 compute, 1 database, 1 network).
Return JSON adhering strictly to this schema:
{
    "providers": [
        {
            "name": "Amazon Web Services (AWS)",
            "services": ["EC2", "DynamoDB", "CloudFront"]
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

        logger.info(f"Discovered providers: {[p['name'] for p in providers]}")
        
        extracted_knowledge = []

        for provider in providers:
            provider_name = provider.get("name")
            for service in provider.get("services", []):
                search_query = f"{provider_name} {service} official documentation SLA limits policies"
                logger.info(f"Searching docs for: {search_query}")
                
                try:
                    search_call = client.search(query=search_query, search_depth="basic", max_results=2)
                    search_res = await search_call if asyncio.iscoroutine(search_call) else search_call
                        
                    urls_to_extract = [r["url"] for r in search_res.get("results", []) if "url" in r]
                    
                    if not urls_to_extract:
                        continue
                        
                    logger.info(f"URLs found for {service}: {urls_to_extract}")

                    extract_call = client.extract(urls=urls_to_extract)
                    extract_res = await extract_call if asyncio.iscoroutine(extract_call) else extract_call

                    extract_results = extract_res.get("results", []) if isinstance(extract_res, dict) else extract_res
                    
                    combined_text = ""
                    for doc in extract_results:
                        raw_content = doc.get("raw_content", "") or doc.get("text", "")
                        if raw_content:
                            combined_text += raw_content[:1500] + "\n...\n"
                            
                    if combined_text:
                        extracted_knowledge.append(
                            f"=== {provider_name} : {service} ===\n{combined_text}"
                        )

                        await collection.update_one(
                            {"type": "crawled_doc", "provider": provider_name, "service": service},
                            {
                                "$set": {
                                    "data": combined_text,
                                    "urls_scraped": urls_to_extract,
                                    "fetched_at": datetime.now(timezone.utc),
                                }
                            },
                            upsert=True,
                        )
                        
                except Exception as e:
                    logger.warning(f"Failed to crawl {provider_name} {service}: {e}")

        logger.info("Crawl complete. Updating master pulse document.")
        master_summary = "\n".join(extracted_knowledge)
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
