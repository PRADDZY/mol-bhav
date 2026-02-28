from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Actor(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"


class Offer(BaseModel):
    round: int
    actor: Actor
    price: float = Field(gt=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    concession_delta: float = 0.0
    message: str = ""


class OfferHistory(BaseModel):
    offers: list[Offer] = Field(default_factory=list)

    def add(self, offer: Offer) -> None:
        self.offers.append(offer)

    @property
    def last_buyer_offer(self) -> Offer | None:
        for o in reversed(self.offers):
            if o.actor == Actor.BUYER:
                return o
        return None

    @property
    def last_seller_offer(self) -> Offer | None:
        for o in reversed(self.offers):
            if o.actor == Actor.SELLER:
                return o
        return None

    @property
    def buyer_offers(self) -> list[Offer]:
        return [o for o in self.offers if o.actor == Actor.BUYER]

    @property
    def seller_offers(self) -> list[Offer]:
        return [o for o in self.offers if o.actor == Actor.SELLER]
