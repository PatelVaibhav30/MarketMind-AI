
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models.market_price import MarketPrice
from app.services.market_price import MarketPriceService


def create_test_stock(client):
    response = client.post(
        "/stocks",
        json={
            "symbol": "RELIANCE",
            "company_name": "Reliance Industries Limited",
            "exchange": "NSE",
        },
    )
    assert response.status_code == 201
    return response.json()


def make_price(stock_id, timestamp, **overrides):
    values = {
        "stock_id": stock_id,
        "timestamp": timestamp,
        "open": Decimal("1420.50"),
        "high": Decimal("1425.75"),
        "low": Decimal("1418.25"),
        "close": Decimal("1423.80"),
        "volume": 1250000,
    }
    values.update(overrides)
    return MarketPrice(**values)


def test_save_price(db_session, client):
    stock = create_test_stock(client)
    service = MarketPriceService(db_session)

    price = make_price(
        stock["id"],
        datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc),
    )

    result = service.save_price(price)

    assert result.id is not None
    assert result.stock_id == stock["id"]


def test_save_prices(db_session, client):
    stock = create_test_stock(client)
    service = MarketPriceService(db_session)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    result = service.save_prices([
        make_price(stock["id"], timestamp),
        make_price(stock["id"], timestamp + timedelta(minutes=1)),
    ])

    assert len(result) == 2
    assert all(price.id is not None for price in result)


def test_save_prices_empty_list(db_session):
    service = MarketPriceService(db_session)

    assert service.save_prices([]) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"volume": -1},
        {"low": Decimal("1430"), "high": Decimal("1425")},
        {"open": Decimal("1426")},
        {"close": Decimal("1417")},
    ],
)
def test_save_price_rejects_invalid_values(
    db_session,
    client,
    overrides,
):
    stock = create_test_stock(client)
    service = MarketPriceService(db_session)

    price = make_price(
        stock["id"],
        datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc),
        **overrides,
    )

    with pytest.raises(ValueError):
        service.save_price(price)


def test_save_price_rejects_naive_timestamp(db_session, client):
    stock = create_test_stock(client)
    service = MarketPriceService(db_session)

    price = make_price(
        stock["id"],
        datetime(2026, 10, 1, 9, 15),
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        service.save_price(price)


def test_save_prices_rejects_duplicate_timestamps(db_session, client):
    stock = create_test_stock(client)
    service = MarketPriceService(db_session)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    prices = [
        make_price(stock["id"], timestamp),
        make_price(stock["id"], timestamp),
    ]

    with pytest.raises(ValueError, match="Duplicate timestamp"):
        service.save_prices(prices)


def test_get_stock_prices(db_session, client):
    stock = create_test_stock(client)
    service = MarketPriceService(db_session)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    service.save_prices([
        make_price(stock["id"], timestamp),
        make_price(stock["id"], timestamp + timedelta(minutes=1)),
    ])

    result = service.get_stock_prices(stock["id"])

    assert len(result) == 2
    assert result[0].timestamp < result[1].timestamp


def test_get_latest_price(db_session, client):
    stock = create_test_stock(client)
    service = MarketPriceService(db_session)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    service.save_prices([
        make_price(stock["id"], timestamp),
        make_price(stock["id"], timestamp + timedelta(minutes=1)),
    ])

    result = service.get_latest_price(stock["id"])

    assert result is not None
    assert result.timestamp == timestamp + timedelta(minutes=1)


def test_get_prices_in_range(db_session, client):
    stock = create_test_stock(client)
    service = MarketPriceService(db_session)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    service.save_prices([
        make_price(stock["id"], timestamp),
        make_price(stock["id"], timestamp + timedelta(minutes=1)),
        make_price(stock["id"], timestamp + timedelta(minutes=2)),
    ])

    result = service.get_prices_in_range(
        stock["id"],
        timestamp + timedelta(minutes=1),
        timestamp + timedelta(minutes=2),
    )

    assert len(result) == 2


def test_get_prices_in_range_rejects_invalid_range(db_session, client):
    stock = create_test_stock(client)
    service = MarketPriceService(db_session)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="start_time"):
        service.get_prices_in_range(
            stock["id"],
            timestamp + timedelta(minutes=2),
            timestamp,
        )


@pytest.mark.parametrize("stock_id", [0, -1])
def test_service_rejects_invalid_stock_id(db_session, stock_id):
    service = MarketPriceService(db_session)

    with pytest.raises(ValueError, match="stock_id"):
        service.get_stock_prices(stock_id)
