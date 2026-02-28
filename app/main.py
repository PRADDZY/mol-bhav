"""Mol-Bhav AI Negotiation Engine — FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Session-Token", "X-Request-ID"],
)


# Request body size limit middleware
class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_body_bytes:
            return JSONResponse(status_code=413, content={"detail": "Request body too large"})
        return await call_next(request)


app.add_middleware(BodySizeLimitMiddleware)

# Routes
app.include_router(negotiate.router)
app.include_router(products.router)
app.include_router(sessions.router)
app.include_router(beckn.router)


@app.get("/health")
async def health():
    checks = {"engine": "mol-bhav", "version": "1.0.0"}
    try:
        from app.db.mongo import get_db
        await get_db().command("ping")
        checks["mongodb"] = "ok"
    except Exception:
        checks["mongodb"] = "unavailable"
    try:
        from app.db.redis import get_redis
        await get_redis().ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"

    all_ok = checks["mongodb"] == "ok" and checks["redis"] == "ok"
    checks["status"] = "ok" if all_ok else "degraded"
    return JSONResponse(content=checks, status_code=200 if all_ok else 503)
