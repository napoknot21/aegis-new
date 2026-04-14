from __future__ import annotations

from enum import StrEnum


class DatasetCode(StrEnum):
    AUM = "AUM"
    SIMM = "SIMM"
    EXPIRIES = "EXPIRIES"
    NAV_ESTIMATED = "NAV_ESTIMATED"
    LEVERAGES = "LEVERAGES"
    LEVERAGES_PER_TRADE = "LEVERAGES_PER_TRADE"
    LEVERAGES_PER_UNDERLYING = "LEVERAGES_PER_UNDERLYING"
    LONG_SHORT_DELTA = "LONG_SHORT_DELTA"
    COUNTERPARTY_CONCENTRATION = "COUNTERPARTY_CONCENTRATION"


class SnapshotCadence(StrEnum):
    DAILY = "daily"
    INTRADAY = "intraday"


class SnapshotShape(StrEnum):
    SINGLE_ROW = "single_row"
    MULTI_ROW = "multi_row"


class SnapshotStatus(StrEnum):
    LOADED = "loaded"
    VALIDATED = "validated"
    OFFICIAL = "official"
    REPLACED = "replaced"
    FAILED = "failed"

