
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert as pg_insert

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_price import MarketPrice


class MarketPriceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, market_price: MarketPrice) -> MarketPrice:
        try:
            self.db.add(market_price)
            self.db.commit()
            self.db.refresh(market_price)
            return market_price

        except Exception:
            self.db.rollback()
            raise

    def create_many(
        self,
        market_prices: list[MarketPrice],
    ) -> list[MarketPrice]:
        if not market_prices:
            return []

        try:
            self.db.add_all(market_prices)
            self.db.commit()

            for market_price in market_prices:
                self.db.refresh(market_price)

            return market_prices

        except Exception:
            self.db.rollback()
            raise

    def get_by_stock(
        self,
        stock_id: int,
    ) -> list[MarketPrice]:
        statement = (
            select(MarketPrice)
            .where(MarketPrice.stock_id == stock_id)
            .order_by(MarketPrice.timestamp.asc())
        )

        return list(self.db.scalars(statement).all())

    def get_latest_by_stock(
        self,
        stock_id: int,
    ) -> MarketPrice | None:
        statement = (
            select(MarketPrice)
            .where(MarketPrice.stock_id == stock_id)
            .order_by(MarketPrice.timestamp.desc())
            .limit(1)
        )

        return self.db.scalars(statement).first()

    def get_by_stock_and_range(
        self,
        stock_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> list[MarketPrice]:
        statement = (
            select(MarketPrice)
            .where(
                MarketPrice.stock_id == stock_id,
                MarketPrice.timestamp >= start_time,
                MarketPrice.timestamp <= end_time,
            )
            .order_by(MarketPrice.timestamp.asc())
        )

        return list(self.db.scalars(statement).all())


    def upsert_many(
        self,
        market_prices: list[MarketPrice],
    ) -> list[MarketPrice]:
        if not market_prices:
            return []

        values = [
            {
                "stock_id": price.stock_id,
                "timestamp": price.timestamp,
                "open": price.open,
                "high": price.high,
                "low": price.low,
                "close": price.close,
                "volume": price.volume,
            }
            for price in market_prices
        ]

        statement = pg_insert(MarketPrice).values(values)

        statement = statement.on_conflict_do_update(
            index_elements=[
                MarketPrice.stock_id,
                MarketPrice.timestamp,
            ],
            set_={
                "open": statement.excluded.open,
                "high": statement.excluded.high,
                "low": statement.excluded.low,
                "close": statement.excluded.close,
                "volume": statement.excluded.volume,
            },
        ).returning(MarketPrice)

        try:
            saved_prices = list(
                self.db.scalars(
                    statement,
                    execution_options={"populate_existing": True},
                ).all()
            )

            self.db.commit()
            return saved_prices

        except Exception:
            self.db.rollback()
            raise


    def stock_exists(self, stock_id: int) -> bool:
        from app.models.stock import Stock

        statement = select(Stock.id).where(Stock.id == stock_id)
        return self.db.scalar(statement) is not None