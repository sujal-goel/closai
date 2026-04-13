"""
Tavily-powered market intelligence service.
Implements 24-hour cache cycle for cloud pricing and policy updates.
Gracefully degrades when Tavily API key is not configured.
"""
import logging
from datetime import datetime, timedelta, timezone
from config import get_settings
from services.database import is_connected

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 24


def _get_tavily_client():
    """Create a Tavily client. Returns None if API key is missing."""
    settings = get_settings()
    if not settings.has_tavily:
        return None
    try:
        from tavily import TavilyClient
        return TavilyClient(api_key=settings.tavily_api_key)
    except ImportError:
        logger.warning("tavily-python not installed. Market intel disabled.")
        return None
    except Exception as e:
        logger.error(f"Failed to create Tavily client: {e}")
        return None


async def enrich_market_intel(
    provider: str,
    service: str,
    region: str = "us-east-1",
) -> dict | None:
    """
    Fetch latest pricing/policy data for a provider+service combo.
    Uses MongoDB cache with a 24-hour TTL before re-querying Tavily.
    Returns None gracefully if Tavily or MongoDB is unavailable.
    """
    # Check MongoDB cache first (if connected)
    if is_connected():
        try:
            from services.database import market_intel_collection
            collection = market_intel_collection()
            cutoff = datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS)

            cached = await collection.find_one(
                {
                    "provider": provider,
                    "service": service,
                    "region": region,
                    "fetched_at": {"$gte": cutoff},
                }
            )

            if cached:
                logger.info(f"Cache hit for {provider}/{service}/{region}")
                return cached.get("data")
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")

    # Cache miss or no DB → query Tavily
    client = _get_tavily_client()
    if client is None:
        logger.info("No Tavily client available. Skipping market intel enrichment.")
        return None

    logger.info(f"Cache miss for {provider}/{service}/{region}. Querying Tavily...")
    try:
        query = (
            f"{provider} {service} pricing {region} "
            f"{datetime.now().year} latest"
        )

        result = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=True,
        )

        data = {
            "answer": result.get("answer", ""),
            "sources": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:500],
                }
                for r in result.get("results", [])
            ],
        }

        # Cache in MongoDB if available
        if is_connected():
            try:
                from services.database import market_intel_collection
                collection = market_intel_collection()
                await collection.update_one(
                    {"provider": provider, "service": service, "region": region},
                    {
                        "$set": {
                            "data": data,
                            "fetched_at": datetime.now(timezone.utc),
                            "query_used": query,
                        }
                    },
                    upsert=True,
                )
            except Exception as e:
                logger.warning(f"Failed to cache market intel: {e}")

        return data

    except Exception as e:
        logger.error(f"Tavily enrichment failed for {provider}/{service}: {e}")
        return None


async def bulk_enrich_for_blueprint(
    blueprint_nodes: list[dict],
    providers: list[str] = ("aws", "gcp", "azure"),
    region: str = "us-east-1",
) -> dict:
    """
    Enrich market intel for every (provider × component) in the blueprint.
    Returns a nested dict: {provider: {service_type: data}}.
    """
    intel = {}
    for provider in providers:
        intel[provider] = {}
        for node in blueprint_nodes:
            service_type = node.get("type", "unknown")
            data = await enrich_market_intel(provider, service_type, region)
            if data:
                intel[provider][service_type] = data
    return intel
