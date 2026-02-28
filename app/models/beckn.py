from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class BecknPrice(BaseModel):
    currency: str = "INR"
    value: str


class BecknBreakupItem(BaseModel):
    title: str
    price: BecknPrice


class BecknQuote(BaseModel):
    price: BecknPrice
    breakup: list[BecknBreakupItem] = Field(default_factory=list)
    ttl: str = "PT5M"  # ISO 8601 duration


class BecknContext(BaseModel):
    domain: str = "retail"
    action: str = ""
    transaction_id: str = Field(default_factory=lambda: uuid4().hex)
    message_id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ttl: str = "PT1M"


class BecknSelectRequest(BaseModel):
    context: BecknContext
    message: dict = Field(default_factory=dict)


class BecknOnSelectResponse(BaseModel):
    context: BecknContext
    message: dict = Field(default_factory=dict)
