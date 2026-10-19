
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.market_price import (
    MarketPriceCreate,
    MarketPriceResponse,
)


def valid_price_data():
    return {
        "stock_id": 1,
        "timestamp": datetime(
            2026, 10, 1, 9, 15, tzinfo=timezone.utc
        ),
        "open": Decimal("1420.50"),
        "high": Decimal("1425.75"),
        "low": Decimal("1418.25"),
        "close": Decimal("1423.80"),
        "volume": 1250000,
    }


def test_valid_market_price_schema():
    price = MarketPriceCreate(**valid_price_data())

    assert price.stock_id == 1
    assert price.open == Decimal("1420.50")
    assert price.volume == 1250000


@pytest.mark.parametrize("stock_id", [0, -1])
def test_stock_id_must_be_positive(stock_id):
    data = valid_price_data()
    data["stock_id"] = stock_id

    with pytest.raises(ValidationError):
        MarketPriceCreate(**data)


@pytest.mark.parametrize(
    "field",
    ["open", "high", "low", "close", "volume"],
)
def test_negative_values_are_rejected(field):
    data = valid_price_data()
    data[field] = -1

    with pytest.raises(ValidationError):
        MarketPriceCreate(**data)


def test_naive_timestamp_is_rejected():
    data = valid_price_data()
    data["timestamp"] = datetime(2026, 10, 1, 9, 15)

    with pytest.raises(ValidationError, match="timezone"):
        MarketPriceCreate(**data)


def test_low_cannot_exceed_high():
    data = valid_price_data()
    data["low"] = Decimal("1430")
    data["high"] = Decimal("1425")

    with pytest.raises(ValidationError, match="low cannot be greater"):
        MarketPriceCreate(**data)


def test_open_must_be_between_low_and_high():
    data = valid_price_data()
    data["open"] = Decimal("1430")

    with pytest.raises(ValidationError, match="open must be between"):
        MarketPriceCreate(**data)


def test_close_must_be_between_low_and_high():
    data = valid_price_data()
    data["close"] = Decimal("1410")

    with pytest.raises(ValidationError, match="close must be between"):
        MarketPriceCreate(**data)


def test_response_schema_supports_attributes():
    class FakeMarketPrice:
        id = 1
        stock_id = 2
        timestamp = datetime(
            2026, 10, 1, 9, 15, tzinfo=timezone.utc
        )
        open = Decimal("100")
        high = Decimal("110")
        low = Decimal("90")
        close = Decimal("105")
        volume = 5000
        created_at = datetime(
            2026, 10, 1, 9, 16, tzinfo=timezone.utc
        )

    response = MarketPriceResponse.model_validate(FakeMarketPrice())

    assert response.id == 1
    assert response.stock_id == 2
    assert response.close == Decimal("105")
