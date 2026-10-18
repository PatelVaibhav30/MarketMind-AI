from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock import Stock


class StockRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, stock: Stock) -> Stock:
        self.db.add(stock)
        self.db.commit()
        self.db.refresh(stock)

        return stock

    def get_all(self) -> list[Stock]:
        statement = select(Stock).order_by(Stock.symbol)

        return list(self.db.scalars(statement).all())

    def get_by_symbol(self, symbol: str) -> Stock | None:
        statement = select(Stock).where(
            Stock.symbol == symbol.upper()
        )

        return self.db.scalars(statement).first()