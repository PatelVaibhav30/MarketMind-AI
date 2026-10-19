
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.market_price import MarketPrice
from app.repositories.market_price import MarketPriceRepository


class MarketPriceService:
    def __init__(self, db: Session):
        self.repository = MarketPriceRepository(db)

    def save_price(self, market_price: MarketPrice) -> MarketPrice:
        self._validate_price(market_price)
        return self.repository.create(market_price)

    def save_prices(
        self,
        market_prices: list[MarketPrice],
    ) -> list[MarketPrice]:
        if not market_prices:
            return []

        for market_price in market_prices:
            self._validate_price(market_price)

        self._validate_unique_timestamps(market_prices)

        return self.repository.create_many(market_prices)

    def upsert_prices(
        self,
        market_prices: list[MarketPrice],
    ) -> list[MarketPrice]:
        if not market_prices:
            return []

        for market_price in market_prices:
            self._validate_price(market_price)

        self._validate_unique_timestamps(market_prices)

        return self.repository.upsert_many(market_prices)
    
    def get_stock_prices(self, stock_id: int) -> list[MarketPrice]:
        self._validate_stock_id(stock_id)
        return self.repository.get_by_stock(stock_id)

    def get_latest_price(self, stock_id: int) -> MarketPrice | None:
        self._validate_stock_id(stock_id)
        return self.repository.get_latest_by_stock(stock_id)

    def get_prices_in_range(
        self,
        stock_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> list[MarketPrice]:
        self._validate_stock_id(stock_id)

        if start_time > end_time:
            raise ValueError("start_time must be before or equal to end_time.")

        self._validate_timezone(start_time, "start_time")
        self._validate_timezone(end_time, "end_time")

        return self.repository.get_by_stock_and_range(
            stock_id=stock_id,
            start_time=start_time,
            end_time=end_time,
        )

    def _validate_stock_id(self, stock_id: int) -> None:
        if stock_id <= 0:
            raise ValueError("stock_id must be a positive integer.")

        if not self.repository.stock_exists(stock_id):
            raise LookupError(f"Stock with id {stock_id} not found.")

    @staticmethod
    def _validate_price(market_price: MarketPrice) -> None:
        if market_price.stock_id <= 0:
            raise ValueError("stock_id must be a positive integer.")

        MarketPriceService._validate_timezone(
            market_price.timestamp,
            "timestamp",
        )

        if market_price.volume < 0:
            raise ValueError("volume cannot be negative.")

        if market_price.low > market_price.high:
            raise ValueError("low cannot be greater than high.")

        if not (
            market_price.low
            <= market_price.open
            <= market_price.high
        ):
            raise ValueError("open must be between low and high.")

        if not (
            market_price.low
            <= market_price.close
            <= market_price.high
        ):
            raise ValueError("close must be between low and high.")

    @staticmethod
    def _validate_timezone(value: datetime, field_name: str) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone-aware.")

    @staticmethod
    def _validate_unique_timestamps(
        market_prices: list[MarketPrice],
    ) -> None:
        seen: set[tuple[int, datetime]] = set()

        for price in market_prices:
            key = (price.stock_id, price.timestamp)

            if key in seen:
                raise ValueError(
                    "Duplicate timestamp found for the same stock."
                )

            seen.add(key)
