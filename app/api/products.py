"""Product catalog CRUD routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

from app.auth import verify_admin_key
from app.db.mongo import products_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/products", tags=["products"])


class CreateProductRequest(BaseModel):
    id: str
    name: str
    category: str = ""
    anchor_price: float = Field(gt=0)
    cost_price: float = Field(gt=0)
    min_margin: float = Field(gt=0, le=1)
    target_margin: float = Field(gt=0, le=1)
    metadata: dict = {}


@router.post("", status_code=201)
async def create_product(
    body: CreateProductRequest,
    _admin: str = Depends(verify_admin_key),
):
    """Add a product to the catalog."""
    doc = body.model_dump()
    doc["_id"] = doc.pop("id")
    try:
        await products_collection().insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail=f"Product {body.id} already exists")
    return {"status": "created", "id": body.id}


@router.get("/{product_id}")
async def get_product(product_id: str):
    """Fetch a single product."""
    doc = await products_collection().find_one({"_id": product_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    doc["id"] = doc.pop("_id")
    return doc


@router.get("")
async def list_products(limit: int = 50, skip: int = 0):
    """List products in the catalog."""
    cursor = products_collection().find().skip(skip).limit(limit)
    results = []
    async for doc in cursor:
        doc["id"] = doc.pop("_id")
        results.append(doc)
    return results
