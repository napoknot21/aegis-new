from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException
from src.api.dependencies import SubredServiceDep
from src.models.subred import SubredAUMResponse, SubredSaveRequest

router = APIRouter(prefix="/api/v1/subred", tags=["SubRed / AUM"])

@router.get("/aum", response_model=SubredAUMResponse)
def get_aum (
    
        service: SubredServiceDep,
        date: str = Query(..., openapi_examples={
            "default": {
                "summary": "Example date",
                "value": "2025-01-15"
            }
        }),
        force_refresh: bool = Query(False),
    
    ) :
    """
    Returns net AUM per fund for a given date.
    Uses local file cache by default, hits live datacenter on cache miss or force_refresh.
    """
    result = service.get_aum(date=date, force_refresh=force_refresh)

    if result is None :
        raise HTTPException(404, detail=f"No subred data for date: {date}")
    
    return result


@router.get("/aum/raw")
def get_raw (

        service: SubredServiceDep,
        date: str = Query(...),
        force_refresh: bool = Query(False),
        
    ) :
    """
    Raw trade-leg records for a given date. Useful for debugging.
    """
    df, md5 = service.get_raw(date=date, force_refresh=force_refresh)
    if df is None:
        raise HTTPException(404, detail=f"No raw subred data for date: {date}")
    return {"date": date, "md5": md5, "records": df.to_dicts()}


@router.post("/aum")
def save_aum(payload: SubredSaveRequest, service: SubredServiceDep):
    """Manually persist AUM data for a date (corrections, backfill)."""
    aum_dict = {f: {"amount": e.amount, "currency": e.currency} for f, e in payload.funds.items()}
    ok = service.save_aum_manually(aum_dict, payload.date)
    if not ok:
        raise HTTPException(500, detail="Failed to save AUM data.")
    return {"status": "ok", "date": payload.date}