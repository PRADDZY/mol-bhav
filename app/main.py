"""Mol-Bhav AI Negotiation Engine — FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.mongo import connect_mongo, close_mongo
from app.db.redis import connect_redis, close_redis
from app.api import negotiate, products, sessions, beckn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set — dialogue generation will use fallback responses")
    await connect_mongo()
    await connect_redis()
    logger.info("Mol-Bhav engine started successfully")
    yield
    # Shutdown
    await close_redis()
    await close_mongo()
    logger.info("Mol-Bhav engine shut down")


_is_prod = settings.env.lower() == "production"

app = FastAPI(
    title="Mol-Bhav",
    description="AI Negotiation Engine — Indian Bazaar-style haggling for e-commerce",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(negotiate.router)
app.include_router(products.router)
app.include_router(sessions.router)
app.include_router(beckn.router)


@app.get("/health")
async def health():
    return {"status": "ok", "engine": "mol-bhav", "version": "1.0.0"}
