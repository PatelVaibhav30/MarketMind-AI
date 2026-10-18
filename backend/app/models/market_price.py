from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    __table_args__ = (
        UniqueConstraint(
            "stock_id",
            "timestamp",
            name="uq_market_prices_stock_timestamp",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    open: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    high: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    low: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    close: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    volume: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )