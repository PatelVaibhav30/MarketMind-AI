from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StockCreate(BaseModel):
    symbol: str = Field(
        min_length=1,
        max_length=20,
    )

    company_name: str = Field(
        min_length=1,
        max_length=255,
    )

    exchange: str = Field(
        min_length=1,
        max_length=20,
    )


class StockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    company_name: str
    exchange: str
    is_active: bool
    created_at: datetime
    updated_at: datetime