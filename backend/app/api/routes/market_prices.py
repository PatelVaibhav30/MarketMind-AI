from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.market_price import MarketPriceCreate, MarketPriceResponse
from app.services.market_price import MarketPriceService
from app.models.market_price import MarketPrice

router = APIRouter(prefix="/market-prices", tags=["Market Prices"])


@router.post(
    "",
    response_model=MarketPriceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_market_price(
    data: MarketPriceCreate,
    db: Session = Depends(get_db),
):
    service = MarketPriceService(db)

    try:
        market_price = service.save_price(
            MarketPrice(**data.model_dump())
        )
        return market_price
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stock does not exist or this timestamp already has a price record.",
        )


@router.post(
    "/bulk",
    response_model=list[MarketPriceResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_market_prices_bulk(
    data: list[MarketPriceCreate],
    db: Session = Depends(get_db),
):
    service = MarketPriceService(db)

    try:
        market_prices = [
            MarketPrice(**item.model_dump())
            for item in data
        ]
        return service.save_prices(market_prices)
    except ValueError as exc:
        if str(exc) == "Duplicate timestamp found for the same stock.":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more stocks do not exist, or duplicate price records were submitted.",
        )


@router.get(
    "/{stock_id}/latest",
    response_model=MarketPriceResponse,
)
def get_latest_market_price(
    stock_id: int,
    db: Session = Depends(get_db),
):
    service = MarketPriceService(db)

    try:
        price = service.get_latest_price(stock_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise get_not_found_http_exception(exc) from exc

    if price is None:
        raise HTTPException(
            status_code=404,
            detail=f"No market prices found for stock ID {stock_id}.",
        )

    return price


@router.get(
    "/{stock_id}/range",
    response_model=list[MarketPriceResponse],
)
def get_market_prices_in_range(
    stock_id: int,
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: Session = Depends(get_db),
):
    service = MarketPriceService(db)

    # Reject naive datetimes before comparing them.
    for field_name, value in (
        ("start_time", start_time),
        ("end_time", end_time),
    ):
        if value.tzinfo is None or value.utcoffset() is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field_name} must include timezone information.",
            )

    try:
        return service.get_prices_in_range(
            stock_id=stock_id,
            start_time=start_time,
            end_time=end_time,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except LookupError as exc:
        raise get_not_found_http_exception(exc) from exc


@router.get(
    "/{stock_id}",
    response_model=list[MarketPriceResponse],
)
def get_market_prices(
    stock_id: int,
    db: Session = Depends(get_db),
):
    service = MarketPriceService(db)

    try:
        return service.get_stock_prices(stock_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise get_not_found_http_exception(exc) from exc


def get_not_found_http_exception(exc: LookupError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(exc),
    )