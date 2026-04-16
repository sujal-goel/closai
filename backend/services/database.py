"""
MongoDB async connection via Motor and collection accessors.
Implements the schema design from the architecture spec:
- chats, blueprints, skus, market_intel
"""
from motor.motor_asyncio import AsyncIOMotorClient
from config import get_settings
import logging

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db = None


async def connect_db():
    """Initialize MongoDB connection pool."""
    global _client, _db
    settings = get_settings()

    if not settings.mongodb_uri:
        logger.warning("No MONGODB_URI set — database features disabled.")
        return

    try:
        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        # Verify connection
        await _client.admin.command("ping")
        _db = _client[settings.db_name]
        logger.info(f"Connected to MongoDB database: {settings.db_name}")

        # Create indexes
        await _ensure_indexes()
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        logger.warning("Continuing without database — endpoints will return errors.")
        _client = None
        _db = None


async def _ensure_indexes():
    """Create or verify all required indexes."""
    if _db is None:
        return

    try:
        await _db.chats.create_index("chatId", unique=True)
        await _db.chats.create_index("expiresAt", expireAfterSeconds=0)
        await _db.blueprints.create_index("blueprintId", unique=True)
        await _db.blueprints.create_index("chatId")
        await _db.skus.create_index(
            [("provider_id", 1), ("workload_category", 1), ("region", 1)]
        )
        await _db.skus.create_index(
            [("provider", 1), ("service", 1), ("region", 1), ("instance_type", 1)],
            unique=True,
            sparse=True,
        )
        await _db.market_intel.create_index(
            [("provider", 1), ("service", 1), ("region", 1)],
        )
        logger.info("MongoDB indexes created/verified.")
    except Exception as e:
        logger.error(f"Index creation failed: {e}")


async def close_db():
    """Close MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")


def get_db():
    """Return the database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _db


def is_connected() -> bool:
    """Check if database is available."""
    return _db is not None


# ── Collection accessors ──────────────────────────────────

def chats_collection():
    return get_db()["chats"]


def blueprints_collection():
    return get_db()["blueprints"]


def skus_collection():
    return get_db()["skus"]


def market_intel_collection():
    return get_db()["market_intel"]


def users_collection():
    return get_db()["users"]
