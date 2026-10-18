from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.repositories.stock import StockRepository
from app.schemas.stock import StockCreate


class StockService:

    def __init__(self, db: Session):
        self.repository = StockRepository(db)

    def create_stock(self, data: StockCreate) -> Stock:
        symbol = data.symbol.upper().strip()

        existing_stock = self.repository.get_by_symbol(symbol)

        if existing_stock:
            raise ValueError(
                f"Stock with symbol '{symbol}' already exists."
            )

        stock = Stock(
            symbol=symbol,
            company_name=data.company_name.strip(),
            exchange=data.exchange.upper().strip(),
        )

        return self.repository.create(stock)

    def get_stocks(self) -> list[Stock]:
        return self.repository.get_all()

    def get_stock(self, symbol: str) -> Stock | None:
        return self.repository.get_by_symbol(symbol)