from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel, Field


# ----------------------------------------------------------------
# Entries (single records)
# ----------------------------------------------------------------

class SubredFundEntry(BaseModel):
    """
    Net AUM for one fund.
    amount = sum of SUB notionals - sum of RED notionals (signed)
    """
    amount: int
    currency: str


class SubredRawRecord(BaseModel):
    """
    A single raw trade leg before aggregation.
    Mirrors the columns from SUBRED_COLS_NEEDED in schema.py.
    """
    tradeLegCode:     str               # "SUB" or "RED"
    tradeDescription: str
    tradeName:        str
    bookName:         str
    tradeType:        str               # always "SUBRED" after filtering
    deliveryDate:     Optional[str]     # from instrument struct
    notional:         Optional[float]   # from instrument struct
    currency:         Optional[str]     # from instrument struct


# ----------------------------------------------------------------
# Responses (what the frontend receives)
# ----------------------------------------------------------------

class SubredAUMResponse(BaseModel):
    """
    Aggregated AUM per fund for a given date.
    This is the main response for GET /api/v1/subred/aum

    Example:
    {
        "date": "2025-01-15",
        "source": "local",
        "funds": {
            "Heroics Volatility": {"amount": 1500000, "currency": "EUR"},
            "Heroics WR":         {"amount": -200000, "currency": "USD"}
        }
    }
    """
    date:   str
    source: str = Field(description="local | remote | storage")
    funds:  Dict[str, SubredFundEntry]


class SubredRawResponse(BaseModel):
    """
    Raw trade-leg records for a given date.
    Response for GET /api/v1/subred/aum/raw
    """
    date:    str
    md5:     Optional[str]              # file hash, None for live remote data
    records: list[SubredRawRecord]


# ----------------------------------------------------------------
# Requests (what the frontend sends)
# ----------------------------------------------------------------

class SubredSaveRequest(BaseModel):
    """
    Body for POST /api/v1/subred/aum
    Used for manual corrections or backfilling historical data.
    """
    date:  str = Field(..., example="2025-01-15")
    funds: Dict[str, SubredFundEntry]