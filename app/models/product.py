from pydantic import BaseModel, Field, computed_field, model_validator


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

    @model_validator(mode="after")
    def _check_price_logic(self) -> "Product":
        if self.cost_price >= self.anchor_price:
            raise ValueError("cost_price must be less than anchor_price")
        if self.min_margin > self.target_margin:
            raise ValueError("min_margin must not exceed target_margin")
        return self

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
