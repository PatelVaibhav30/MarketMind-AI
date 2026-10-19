
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.market_price import MarketPrice
from app.repositories.market_price import MarketPriceRepository


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


def create_market_price(stock_id, timestamp, close="1423.80"):
    return MarketPrice(
        stock_id=stock_id,
        timestamp=timestamp,
        open=Decimal("1420.50"),
        high=Decimal("1425.75"),
        low=Decimal("1418.25"),
        close=Decimal(close),
        volume=1250000,
    )


def test_create_market_price(db_session, client):
    stock = create_test_stock(client)
    repository = MarketPriceRepository(db_session)

    price = create_market_price(
        stock["id"],
        datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc),
    )

    result = repository.create(price)

    assert result.id is not None
    assert result.stock_id == stock["id"]
    assert result.close == Decimal("1423.800000")


def test_create_many_market_prices(db_session, client):
    stock = create_test_stock(client)
    repository = MarketPriceRepository(db_session)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    prices = [
        create_market_price(stock["id"], timestamp),
        create_market_price(stock["id"], timestamp + timedelta(minutes=1)),
    ]

    result = repository.create_many(prices)

    assert len(result) == 2
    assert all(price.id is not None for price in result)


def test_create_many_empty_list(db_session):
    repository = MarketPriceRepository(db_session)

    assert repository.create_many([]) == []


def test_get_by_stock_returns_chronological_order(db_session, client):
    stock = create_test_stock(client)
    repository = MarketPriceRepository(db_session)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    repository.create_many([
        create_market_price(
            stock["id"],
            timestamp + timedelta(minutes=2),
        ),
        create_market_price(
            stock["id"],
            timestamp,
        ),
        create_market_price(
            stock["id"],
            timestamp + timedelta(minutes=1),
        ),
    ])

    result = repository.get_by_stock(stock["id"])

    assert len(result) == 3
    assert [price.timestamp for price in result] == sorted(
        price.timestamp for price in result
    )


def test_get_latest_by_stock(db_session, client):
    stock = create_test_stock(client)
    repository = MarketPriceRepository(db_session)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    repository.create_many([
        create_market_price(stock["id"], timestamp),
        create_market_price(
            stock["id"],
            timestamp + timedelta(minutes=1),
            close="1426.00",
        ),
    ])

    latest = repository.get_latest_by_stock(stock["id"])

    assert latest is not None
    assert latest.timestamp == timestamp + timedelta(minutes=1)
    assert latest.close == Decimal("1426.000000")


def test_get_latest_by_stock_when_no_prices(db_session, client):
    stock = create_test_stock(client)
    repository = MarketPriceRepository(db_session)

    assert repository.get_latest_by_stock(stock["id"]) is None


def test_get_by_stock_and_range(db_session, client):
    stock = create_test_stock(client)
    repository = MarketPriceRepository(db_session)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    repository.create_many([
        create_market_price(stock["id"], timestamp),
        create_market_price(
            stock["id"],
            timestamp + timedelta(minutes=1),
        ),
        create_market_price(
            stock["id"],
            timestamp + timedelta(minutes=2),
        ),
    ])

    result = repository.get_by_stock_and_range(
        stock_id=stock["id"],
        start_time=timestamp + timedelta(minutes=1),
        end_time=timestamp + timedelta(minutes=2),
    )

    assert len(result) == 2
    assert result[0].timestamp == timestamp + timedelta(minutes=1)
    assert result[1].timestamp == timestamp + timedelta(minutes=2)


def test_get_by_stock_returns_empty_list_when_no_prices(db_session, client):
    stock = create_test_stock(client)
    repository = MarketPriceRepository(db_session)

    assert repository.get_by_stock(stock["id"]) == []

def test_upsert_many_inserts_new_prices(db_session, client):
    stock = create_test_stock(client)
    repository = MarketPriceRepository(db_session)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    prices = [
        create_market_price(stock["id"], timestamp),
        create_market_price(
            stock["id"],
            timestamp + timedelta(minutes=1),
            close="1426.00",
        ),
    ]

    result = repository.upsert_many(prices)

    assert len(result) == 2
    assert all(price.id is not None for price in result)

    stored = repository.get_by_stock(stock["id"])
    assert len(stored) == 2


def test_upsert_many_updates_existing_price(db_session, client):
    stock = create_test_stock(client)
    repository = MarketPriceRepository(db_session)
    timestamp = datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc)

    original = create_market_price(
        stock["id"],
        timestamp,
        close="1423.80",
    )
    repository.create(original)
    original_id = original.id

    updated = create_market_price(
        stock["id"],
        timestamp,
        close="1424.00",
    )

    result = repository.upsert_many([updated])

    assert len(result) == 1
    assert result[0].id == original_id
    assert result[0].close == Decimal("1424.000000")

    stored = repository.get_by_stock(stock["id"])
    assert len(stored) == 1
    assert stored[0].close == Decimal("1424.000000")


def test_upsert_many_empty_list(db_session):
    repository = MarketPriceRepository(db_session)

    assert repository.upsert_many([]) == []
