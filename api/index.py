"""
Vercel Serverless entry point.
Imports FastAPI app from the backend package and exposes it as the ASGI handler.
"""
import sys
import os

# Allow importing from `backend/` as if it were in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app  # noqa: F401 — Vercel discovers `app` automatically
