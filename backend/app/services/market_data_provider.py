
from datetime import datetime
from decimal import Decimal

import yfinance as yf


class YahooFinanceProvider:
    """Fetch and normalize market data from Yahoo Finance."""

    def fetch_daily_prices(
        self,
        ticker_symbol: str,
        period: str = "5d",
    ) -> list[dict]:
        if not ticker_symbol or not ticker_symbol.strip():
            raise ValueError("ticker_symbol cannot be empty.")

        history = yf.Ticker(ticker_symbol).history(
            period=period,
            interval="1d",
            auto_adjust=False,
        )

        if history.empty:
            return []

        prices = []

        for timestamp, row in history.iterrows():
            prices.append(
                {
                    "timestamp": timestamp.to_pydatetime(),
                    "open": Decimal(str(row["Open"])),
                    "high": Decimal(str(row["High"])),
                    "low": Decimal(str(row["Low"])),
                    "close": Decimal(str(row["Close"])),
                    "volume": int(row["Volume"]),
                }
            )

        return prices
