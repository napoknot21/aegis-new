from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class AssetClassRecord:
    id_ac: int
    code: str
    ice_code: str | None
    name: str
    description: str | None
    sort_order: int
    is_active: bool


@dataclass(slots=True)
class CurrencyRecord:
    id_ccy: int
    code: str
    name: str
    symbol: str | None
    iso_numeric: int | None
    decimals: int
    sort_order: int
    is_active: bool


@dataclass(slots=True)
class FundRecord:
    id_f: int
    id_org: int
    id_ccy: int
    name: str
    code: str
    fund_type: str | None
    inception_date: date | None
    is_active: bool


@dataclass(slots=True)
class BookRecord:
    id_book: int
    id_org: int
    id_f: int
    name: str
    parent_id: int | None
    is_active: bool


@dataclass(slots=True)
class TradeLabelRecord:
    id_label: int
    id_org: int
    code: str


@dataclass(slots=True)
class CounterpartyRecord:
    id_ctpy: int
    id_org: int
    id_bank: int | None
    ice_name: str | None
    ext_code: str | None
    is_active: bool
    display_name: str
