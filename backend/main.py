"""
Cloud Deployment Comparison Tool — FastAPI Backend
Main application entry point with robust startup/shutdown lifecycle.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from services.database import connect_db, close_db
from services.daily_sync import sync_daily_market_pulse, execute_single_sync
from services.knowledge_service import init_knowledge_base
import asyncio
import logging
# ── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    is_vercel = os.environ.get("VERCEL") == "1"
    
    logger.info(f"🚀 Starting Cloud Compare API (Serverless: {is_vercel})...")

    # Validate critical config
    if not settings.has_gemini:
        logger.warning("⚠️  GEMINI_API_KEY not set — LLM features will fail!")

    await connect_db()
    
    # Initialize the local RAG knowledge base
    init_knowledge_base()
    
    sync_task = None
    if not is_vercel:
        # Boot the dynamic macro background task (Local/Docker only)
        sync_task = asyncio.create_task(sync_daily_market_pulse())
    else:
        logger.info("ℹ️  Serverless mode: Skipping persistent background sync loop.")
    
    yield
    
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass
        
    await close_db()
    logger.info("👋 Cloud Compare API shutdown.")


# ── App ────────────────────────────────────────────────────
app = FastAPI(
    title="CLOS AI API",
    description=(
        "AI-driven cloud deployment comparison tool. "
        "Converts natural language into architecture blueprints, "
        "scores providers across 7 dimensions, and maps to native services."
    ),
    version="2.1.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────
settings = get_settings()
print(settings)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if settings.frontend_url:
    # Ensure no trailing slash for exact matches
    origins.append(settings.frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────
# Import routers after app is created to avoid circular imports
from routes.chat import router as chat_router
from routes.blueprint import router as blueprint_router
from routes.auth import router as auth_router

app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(blueprint_router, prefix="/api", tags=["Blueprint"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])


# ── Root & Health ──────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    return {
        "service": "CLOS AI API",
        "version": "2.1.0",
        "status": "operational",
    }


@app.get("/health", tags=["System"])
async def health():
    from services.database import is_connected
    return {
        "status": "healthy",
        "database": "connected" if is_connected() else "disconnected",
        "gemini": "configured" if settings.has_gemini else "missing",
        "tavily": "configured" if settings.has_tavily else "disabled",
    }


# ── Vercel Cron Sync ───────────────────────────────────────
@app.post("/api/cron/sync", tags=["System"])
async def trigger_sync(authorization: str = Header(None)):
    """
    Protected endpoint to trigger a single sync run.
    Expects 'Authorization: Bearer <CRON_SECRET>'
    """
    cron_secret = os.environ.get("CRON_SECRET")
    if not cron_secret:
        logger.warning("CRON_SECRET not set in environment. Cron trigger disabled.")
        raise HTTPException(status_code=500, detail="Cron secret not configured")
        
    if authorization != f"Bearer {cron_secret}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron secret",
        )
    
    # Run sync in background (it will likely finish within Vercel's timeout if data is small, 
    # but strictly speaking serverless might kill it if it takes too long. 
    # Vercel CRONs wait for response.)
    success = await execute_single_sync()
    if not success:
        raise HTTPException(status_code=500, detail="Sync failed")
        
    return {"status": "success", "message": "Manual sync completed."}
