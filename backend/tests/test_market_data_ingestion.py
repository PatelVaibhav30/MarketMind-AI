
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.models.market_price import MarketPrice
from app.models.stock import Stock
from app.services.market_data_ingestion import MarketDataIngestionService


def make_stock(db_session, symbol="RELIANCE", exchange="NSE", is_active=True):
    stock = Stock(
        symbol=symbol,
        company_name="Reliance Industries Limited",
        exchange=exchange,
        is_active=is_active,
    )
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)
    return stock


def make_candle(close="1423.80"):
    return {
        "timestamp": datetime(
            2026, 10, 19, 0, 0, tzinfo=timezone.utc
        ),
        "open": Decimal("1420.50"),
        "high": Decimal("1425.75"),
        "low": Decimal("1418.25"),
        "close": Decimal(close),
        "volume": 1250000,
    }


def test_ingestion_saves_fetched_candles(db_session, monkeypatch):
    stock = make_stock(db_session)
    service = MarketDataIngestionService(db_session)

    service.provider.fetch_daily_prices = Mock(
        return_value=[make_candle()]
    )

    result = service.ingest_daily_prices(stock)

    assert len(result) == 1
    assert result[0].stock_id == stock.id
    assert result[0].close == Decimal("1423.800000")

    service.provider.fetch_daily_prices.assert_called_once_with(
        ticker_symbol="RELIANCE.NS",
        period="5d",
    )


def test_repeated_ingestion_does_not_create_duplicates(
    db_session,
):
    stock = make_stock(db_session)
    service = MarketDataIngestionService(db_session)

    service.provider.fetch_daily_prices = Mock(
        return_value=[make_candle()]
    )

    first_result = service.ingest_daily_prices(stock)
    second_result = service.ingest_daily_prices(stock)

    assert len(first_result) == 1
    assert len(second_result) == 1

    stored = service.market_price_service.get_stock_prices(stock.id)
    assert len(stored) == 1
    assert stored[0].close == Decimal("1423.800000")


def test_repeated_ingestion_updates_existing_candle(db_session):
    stock = make_stock(db_session)
    service = MarketDataIngestionService(db_session)

    service.provider.fetch_daily_prices = Mock(
        side_effect=[
            [make_candle("1423.80")],
            [make_candle("1424.00")],
        ]
    )

    first_result = service.ingest_daily_prices(stock)
    original_id = first_result[0].id

    second_result = service.ingest_daily_prices(stock)

    stored = service.market_price_service.get_stock_prices(stock.id)

    assert len(stored) == 1
    assert second_result[0].id == original_id
    assert stored[0].close == Decimal("1424.000000")


def test_ingestion_returns_empty_when_provider_has_no_data(
    db_session,
):
    stock = make_stock(db_session)
    service = MarketDataIngestionService(db_session)
    service.provider.fetch_daily_prices = Mock(return_value=[])

    result = service.ingest_daily_prices(stock)

    assert result == []
    assert service.market_price_service.get_stock_prices(stock.id) == []


def test_ingestion_rejects_inactive_stock(db_session):
    stock = make_stock(db_session, is_active=False)
    service = MarketDataIngestionService(db_session)
    service.provider.fetch_daily_prices = Mock(return_value=[])

    with pytest.raises(ValueError, match="is inactive"):
        service.ingest_daily_prices(stock)

    service.provider.fetch_daily_prices.assert_not_called()


def test_ingestion_rejects_unsupported_exchange(db_session):
    stock = make_stock(db_session, exchange="OTHER")
    service = MarketDataIngestionService(db_session)
    service.provider.fetch_daily_prices = Mock(return_value=[])

    with pytest.raises(ValueError, match="Unsupported exchange"):
        service.ingest_daily_prices(stock)

    service.provider.fetch_daily_prices.assert_not_called()
