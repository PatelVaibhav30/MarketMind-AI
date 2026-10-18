from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.stock import StockCreate, StockResponse
from app.services.stock import StockService


router = APIRouter(
    prefix="/stocks",
    tags=["Stocks"],
)


@router.post(
    "",
    response_model=StockResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_stock(
    data: StockCreate,
    db: Session = Depends(get_db),
):
    service = StockService(db)

    try:
        return service.create_stock(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[StockResponse],
)
def get_stocks(
    db: Session = Depends(get_db),
):
    service = StockService(db)

    return service.get_stocks()


@router.get(
    "/{symbol}",
    response_model=StockResponse,
)
def get_stock(
    symbol: str,
    db: Session = Depends(get_db),
):
    service = StockService(db)

    stock = service.get_stock(symbol)

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock '{symbol}' not found.",
        )

    return stock