from __future__ import annotations

from enum import Enum


class TradeTypeCode(str, Enum):
    DISC = "DISC"
    ADV = "ADV"


class TradeStatus(str, Enum):
    BOOKED = "booked"
    RECAP_DONE = "recap_done"
    VALIDATED = "validated"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
