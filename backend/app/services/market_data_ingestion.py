
from sqlalchemy.orm import Session

from app.models.market_price import MarketPrice
from app.models.stock import Stock
from app.services.market_data_provider import YahooFinanceProvider
from app.services.market_price import MarketPriceService


class MarketDataIngestionService:
    """Fetch market data and persist it in the database."""

    def __init__(self, db: Session):
        self.db = db
        self.provider = YahooFinanceProvider()
        self.market_price_service = MarketPriceService(db)

    def ingest_daily_prices(
        self,
        stock: Stock,
        period: str = "5d",
    ) -> list[MarketPrice]:
        if not stock.is_active:
            raise ValueError(
                f"Stock {stock.symbol} is inactive."
            )

        ticker_symbol = self._get_yahoo_ticker(stock)

        candles = self.provider.fetch_daily_prices(
            ticker_symbol=ticker_symbol,
            period=period,
        )

        market_prices = [
            MarketPrice(
                stock_id=stock.id,
                timestamp=candle["timestamp"],
                open=candle["open"],
                high=candle["high"],
                low=candle["low"],
                close=candle["close"],
                volume=candle["volume"],
            )
            for candle in candles
        ]

        if not market_prices:
            return []

        return self.market_price_service.upsert_prices(market_prices)

    @staticmethod
    def _get_yahoo_ticker(stock: Stock) -> str:
        symbol = stock.symbol.strip().upper()

        if stock.exchange == "NSE":
            return f"{symbol}.NS"

        if stock.exchange == "BSE":
            return f"{symbol}.BO"

        raise ValueError(
            f"Unsupported exchange '{stock.exchange}' "
            f"for stock {stock.symbol}."
        )
