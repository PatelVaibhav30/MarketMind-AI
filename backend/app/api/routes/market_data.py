
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.stock import Stock
from app.services.market_data_ingestion import MarketDataIngestionService

router = APIRouter(
    prefix="/market-data",
    tags=["Market Data"],
)


@router.post("/ingest/{stock_id}")
def ingest_stock_market_data(
    stock_id: int,
    period: str = "5d",
    db: Session = Depends(get_db),
):
    stock = db.get(Stock, stock_id)

    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with id {stock_id} not found.",
        )

    service = MarketDataIngestionService(db)

    try:
        prices = service.ingest_daily_prices(
            stock=stock,
            period=period,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return {
        "message": "Market data ingestion completed.",
        "stock": stock.symbol,
        "records_processed": len(prices),
        "prices": [
            {
                "id": price.id,
                "stock_id": price.stock_id,
                "timestamp": price.timestamp,
                "open": price.open,
                "high": price.high,
                "low": price.low,
                "close": price.close,
                "volume": price.volume,
            }
            for price in prices
        ],
    }

@router.post("/ingest-all")
def ingest_all_active_stocks(
    period: str = "5d",
    db: Session = Depends(get_db),
):
    stocks = db.scalars(
        select(Stock)
        .where(Stock.is_active.is_(True))
        .order_by(Stock.symbol)
    ).all()

    service = MarketDataIngestionService(db)

    results = []

    for stock in stocks:
        try:
            prices = service.ingest_daily_prices(
                stock=stock,
                period=period,
            )

            results.append({
                "symbol": stock.symbol,
                "status": "success",
                "records_processed": len(prices),
            })

        except Exception:
            results.append({
                "symbol": stock.symbol,
                "status": "failed",
                "records_processed": 0,
                "message": "Data ingestion failed for this stock.",
            })

    successful = sum(
        1 for result in results
        if result["status"] == "success"
    )

    return {
        "message": "Bulk market data ingestion completed.",
        "total_stocks": len(stocks),
        "successful_stocks": successful,
        "failed_stocks": len(stocks) - successful,
        "results": results,
    }
