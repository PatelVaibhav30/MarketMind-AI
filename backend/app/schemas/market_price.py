
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MarketPriceCreate(BaseModel):
    stock_id: int = Field(gt=0)
    timestamp: datetime

    open: Decimal = Field(ge=0)
    high: Decimal = Field(ge=0)
    low: Decimal = Field(ge=0)
    close: Decimal = Field(ge=0)

    volume: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_ohlc(self):
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must include timezone information.")

        if self.low > self.high:
            raise ValueError("low cannot be greater than high.")

        if not self.low <= self.open <= self.high:
            raise ValueError("open must be between low and high.")

        if not self.low <= self.close <= self.high:
            raise ValueError("close must be between low and high.")

        return self


class MarketPriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_id: int
    timestamp: datetime

    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal

    volume: int
    created_at: datetime
