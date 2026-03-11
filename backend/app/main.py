"""
E.V.O.N. — Enhanced Voice-Operated Nexus
FastAPI application entry point.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import chat, system, voice
from app.services.llm_service import llm_service
from app.services.stt_service import stt_service
from app.services.tts_service import tts_service

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("evon")


# ── Lifespan ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown lifecycle."""
    logger.info("═" * 60)
    logger.info("  E.V.O.N. — Starting up …")
    logger.info("═" * 60)

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database ready.")

    # Initialize services
    try:
        await stt_service.load_model()
    except Exception as exc:
        logger.warning("STT model load failed (will retry on first use): %s", exc)

    await llm_service.initialize()
    await tts_service.initialize()

    # Check Ollama health
    if await llm_service.health_check():
        models = await llm_service.list_models()
        logger.info("Ollama connected — models: %s", models)
    else:
        logger.warning("Ollama not reachable at %s", settings.OLLAMA_BASE_URL)

    logger.info("═" * 60)
    logger.info("  E.V.O.N. — Online and ready.")
    logger.info("═" * 60)

    yield  # ← Application runs here

    # Shutdown
    logger.info("E.V.O.N. shutting down …")
    await llm_service.shutdown()


# ── App ──────────────────────────────────────────────────
app = FastAPI(
    title="E.V.O.N. — Enhanced Voice-Operated Nexus",
    description="Offline AI assistant powered by Whisper + Ollama + Piper TTS",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for TTS output
app.mount("/static/tts", StaticFiles(directory=settings.TTS_OUTPUT_DIR), name="tts")

# Routers
app.include_router(chat.router)
app.include_router(voice.router)
app.include_router(system.router)


# ── Root ─────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "name": "E.V.O.N.",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    ollama_ok = await llm_service.health_check()
    return {
        "status": "healthy",
        "ollama": "connected" if ollama_ok else "disconnected",
        "stt": "loaded" if stt_service._model is not None else "not loaded",
    }
