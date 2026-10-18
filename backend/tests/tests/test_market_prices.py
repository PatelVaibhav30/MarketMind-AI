from datetime import datetime, timezone
from decimal import Decimal

from app.models.market_price import MarketPrice


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


def test_market_price_model(db_session, client):
    stock = create_test_stock(client)

    market_price = MarketPrice(
        stock_id=stock["id"],
        timestamp=datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc),
        open=Decimal("1420.50"),
        high=Decimal("1425.75"),
        low=Decimal("1418.25"),
        close=Decimal("1423.80"),
        volume=1250000,
    )

    db_session.add(market_price)
    db_session.commit()
    db_session.refresh(market_price)

    assert market_price.id is not None
    assert market_price.stock_id == stock["id"]
    assert market_price.open == Decimal("1420.500000")
    assert market_price.high == Decimal("1425.750000")
    assert market_price.low == Decimal("1418.250000")
    assert market_price.close == Decimal("1423.800000")
    assert market_price.volume == 1250000


def test_market_price_allows_different_timestamps(db_session, client):
    stock = create_test_stock(client)

    price_1 = MarketPrice(
        stock_id=stock["id"],
        timestamp=datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc),
        open=Decimal("1420"),
        high=Decimal("1425"),
        low=Decimal("1418"),
        close=Decimal("1423"),
        volume=100000,
    )

    price_2 = MarketPrice(
        stock_id=stock["id"],
        timestamp=datetime(2026, 10, 1, 9, 16, tzinfo=timezone.utc),
        open=Decimal("1423"),
        high=Decimal("1427"),
        low=Decimal("1422"),
        close=Decimal("1426"),
        volume=150000,
    )

    db_session.add_all([price_1, price_2])
    db_session.commit()

    assert price_1.id != price_2.id


def test_market_price_prevents_duplicate_timestamp(db_session, client):
    stock = create_test_stock(client)

    timestamp = datetime(
        2026,
        10,
        1,
        9,
        15,
        tzinfo=timezone.utc,
    )

    price_1 = MarketPrice(
        stock_id=stock["id"],
        timestamp=timestamp,
        open=Decimal("1420"),
        high=Decimal("1425"),
        low=Decimal("1418"),
        close=Decimal("1423"),
        volume=100000,
    )

    price_2 = MarketPrice(
        stock_id=stock["id"],
        timestamp=timestamp,
        open=Decimal("1423"),
        high=Decimal("1427"),
        low=Decimal("1422"),
        close=Decimal("1426"),
        volume=150000,
    )

    db_session.add(price_1)
    db_session.commit()

    db_session.add(price_2)

    try:
        db_session.commit()
        assert False, "Expected duplicate timestamp constraint violation"
    except Exception:
        db_session.rollback()


def test_market_price_cascade_delete(db_session, client):
    stock = create_test_stock(client)

    market_price = MarketPrice(
        stock_id=stock["id"],
        timestamp=datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc),
        open=Decimal("1420"),
        high=Decimal("1425"),
        low=Decimal("1418"),
        close=Decimal("1423"),
        volume=100000,
    )

    db_session.add(market_price)
    db_session.commit()

    stock_id = stock["id"]

    db_session.execute(
        __import__("sqlalchemy").text(
            "DELETE FROM stocks WHERE id = :stock_id"
        ),
        {"stock_id": stock_id},
    )
    db_session.commit()

    remaining = db_session.query(MarketPrice).filter(
        MarketPrice.stock_id == stock_id
    ).first()

    assert remaining is None