"""Mol-Bhav AI Negotiation Engine — FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.mongo import connect_mongo, close_mongo
from app.db.redis import connect_redis, close_redis
from app.api import negotiate, products, sessions, beckn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_mongo()
    await connect_redis()
    yield
    # Shutdown
    await close_redis()
    await close_mongo()


app = FastAPI(
    title="Mol-Bhav",
    description="AI Negotiation Engine — Indian Bazaar-style haggling for e-commerce",
    version="1.0.0",
    lifespan=lifespan,
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
