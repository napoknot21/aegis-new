from __future__ import annotations

from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.services.recap_service import RecapService

router = APIRouter(prefix="/api/v1/recap", tags=["Trade Recap"])

class TradeRecord(BaseModel):
    TradeId: str
    Portfolio: str
    ProductType: str
    Quantity: float
    Price: float
    Currency: str
    Status: str
    Date: str
    TradeDate: str

def get_recap_service() -> RecapService:
    return RecapService()

@router.get("/run")
def run_trade_recap(
    date: str = Query(None, description="Report Date as YYYY-MM-DD"),
    trade_date: str = Query(None, description="Trade Date as YYYY-MM-DD"),
    service: RecapService = Depends(get_recap_service)
):
    """
    Returns the Trade Recap information.
    Currently mocked as a DataFrame.
    """
    try:
        df = service.get_trade_recap(date=date, trade_date=trade_date)
        records = df.to_dict(orient="records")
        return {"status": "ok", "date": date, "trade_date": trade_date, "records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/book")
def book_recap_trades(
    trades: List[TradeRecord],
    service: RecapService = Depends(get_recap_service)
):
    """
    Receives edited trades from the Recap grid and processes booking.
    """
    try:
        trades_dict = [t.model_dump() for t in trades]
        count = service.book_recap_trades(trades_dict)
        return {"status": "ok", "booked_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))