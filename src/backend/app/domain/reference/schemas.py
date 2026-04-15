from __future__ import annotations

from dataclasses import asdict
from datetime import date

from pydantic import BaseModel

from app.domain.reference.entities import (
    AssetClassRecord,
    BookRecord,
    CounterpartyRecord,
    CurrencyRecord,
    FundRecord,
    TradeLabelRecord,
)


class AssetClassResponse(BaseModel):
    id_ac: int
    code: str
    ice_code: str | None
    name: str
    description: str | None
    sort_order: int
    is_active: bool


class CurrencyResponse(BaseModel):
    id_ccy: int
    code: str
    name: str
    symbol: str | None
    iso_numeric: int | None
    decimals: int
    sort_order: int
    is_active: bool


class FundResponse(BaseModel):
    id_f: int
    id_org: int
    id_ccy: int
    name: str
    code: str
    fund_type: str | None
    inception_date: date | None
    is_active: bool


class BookResponse(BaseModel):
    id_book: int
    id_org: int
    id_f: int
    name: str
    parent_id: int | None
    is_active: bool


class TradeLabelResponse(BaseModel):
    id_label: int
    id_org: int
    code: str


class CounterpartyResponse(BaseModel):
    id_ctpy: int
    id_org: int
    id_bank: int | None
    ice_name: str | None
    ext_code: str | None
    is_active: bool
    display_name: str


def build_asset_class_response(record: AssetClassRecord) -> AssetClassResponse:
    return AssetClassResponse(**asdict(record))


def build_currency_response(record: CurrencyRecord) -> CurrencyResponse:
    return CurrencyResponse(**asdict(record))


def build_fund_response(record: FundRecord) -> FundResponse:
    return FundResponse(**asdict(record))


def build_book_response(record: BookRecord) -> BookResponse:
    return BookResponse(**asdict(record))


def build_trade_label_response(record: TradeLabelRecord) -> TradeLabelResponse:
    return TradeLabelResponse(**asdict(record))


def build_counterparty_response(record: CounterpartyRecord) -> CounterpartyResponse:
    return CounterpartyResponse(**asdict(record))
