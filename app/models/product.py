from pydantic import BaseModel, Field, computed_field


class Product(BaseModel):
    id: str = ""
    name: str
    category: str = ""
    anchor_price: float = Field(gt=0, description="Listing / sticker price")
    cost_price: float = Field(gt=0, description="Base cost to seller")
    min_margin: float = Field(
        gt=0, le=1, description="Minimum margin fraction, e.g. 0.05 for 5%"
    )
    target_margin: float = Field(
        gt=0, le=1, description="Target margin fraction, e.g. 0.30 for 30%"
    )
    metadata: dict = Field(default_factory=dict)

    @computed_field
    @property
    def reservation_price(self) -> float:
        """Floor price = cost * (1 + min_margin). Never sell below this."""
        return round(self.cost_price * (1 + self.min_margin), 2)

    @computed_field
    @property
    def target_price(self) -> float:
        """Ideal selling price = cost * (1 + target_margin)."""
        return round(self.cost_price * (1 + self.target_margin), 2)

    @computed_field
    @property
    def zopa_range(self) -> tuple[float, float]:
        """(reservation_price, anchor_price) — the negotiable range."""
        return (self.reservation_price, self.anchor_price)
