from __future__ import annotations

"""
api/routes/nav.py
-----------------
FastAPI routes for the NAV domain.

Endpoints:
  GET  /api/v1/nav/history          - Full NAV time series for a fund
  GET  /api/v1/nav/portfolio        - Per-book snapshot for a given date
  GET  /api/v1/nav/estimate         - GAV / weighted performance series
  GET  /api/v1/nav/performance      - Monthly/yearly performance table
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Literal

from src.api.dependencies import NavServiceDep
from src.models.nav import (
    NavHistoryResponse,
    NavPortfolioResponse,
    NavEstimateResponse,
    NavPerformanceResponse,
)

router = APIRouter(prefix="/api/v1/nav", tags=["NAV"])


@router.get("/history", response_model=NavHistoryResponse)
def get_history (

        service : NavServiceDep,
        fund : str = Query(..., openapi_examples={
                "hv": {"summary": "Fund HV", "value": "Heroics Volatility"},
            }
        ),
        cutoff_date : str = Query(None, openapi_examples={
                "default": { "summary" : "Cutoff date", "value" : "2020-01-01"},
            }
        ),
    
    ) :
    """
    Full NAV history for a fund, filtered by cutoff date.
    Returns one row per portfolio per date.
    """
    result = service.get_history(fund=fund, cutoff_date=cutoff_date)

    if result is None:
        raise HTTPException(404, detail=f"No NAV history for fund '{fund}'")
    
    return result


@router.get("/portfolio", response_model=NavPortfolioResponse)
def get_portfolio (

        service: NavServiceDep,
        fund : str = Query(...),
        date : str = Query(..., openapi_examples={
                "default": {"summary" : "Target date", "value" : "2025-01-15"},
            }
        ),
        mode : Literal["eq", "le", "ge"] = Query("eq", description=(
            "eq = exact date | le = latest date ≤ target | ge = earliest date ≥ target"
        )),

    ) :
    """
    Per-book NAV snapshot for a given date.
    Use mode=le to get the most recent available file if the exact date is missing.
    """
    result = service.get_portfolio(fund=fund, date=date, mode=mode)

    if result is None :
        raise HTTPException(404, detail=f"No NAV portfolio for fund '{fund}' date '{date}' mode '{mode}'")
    
    return result


@router.get("/estimate", response_model=NavEstimateResponse)
def get_estimate (

        service: NavServiceDep,
        fund: str = Query(...),
    
    ) :
    """
    GAV and weighted performance time series for a fund.
    """
    result = service.get_estimate(fund=fund)

    if result is None :
        raise HTTPException(404, detail=f"No NAV estimate data for fund '{fund}'")
    
    return result


@router.get("/performance", response_model=NavPerformanceResponse)
def get_performance(

        service: NavServiceDep,
        fund: str = Query(...),
        nav_col: str = Query(..., description="Name of the NAV column in the estimate file for this fund"),
    
    ) :
    """
    Monthly/yearly performance table (like what you see in the Streamlit UI).
    Returns a pivot table: rows = years, columns = Jan..Dec + Total.
    """
    result = service.get_monthly_performance(fund=fund, nav_col=nav_col)

    if result is None :
        raise HTTPException(404, detail=f"No performance data for fund '{fund}'")
    
    return result