from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.trades.entities import (
    DiscTradeAggregate,
    DiscTradeFieldRecord,
    DiscTradeInstrumentRecord,
    DiscTradeLegAggregate,
    DiscTradePremiumRecord,
    DiscTradeSettlementRecord,
    TradeMasterRecord,
    TradeTypeRecord,
)
from app.domain.trades.enums import TradeStatus, TradeTypeCode


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DiscTradeInstrumentCreate(StrictModel):
    id_ac: int | None = None
    notional: Decimal | None = None
    id_ccy: int | None = None
    buysell: Literal["Buy", "Sell"] | None = None
    i_type: str | None = None
    trade_date: date | None = None
    isin: str | None = None
    bbg_ticker: str | None = None
    payload_json: dict[str, Any] | None = None


class DiscTradePremiumCreate(StrictModel):
    amount: Decimal | None = None
    id_ccy: int | None = None
    p_date: date | None = None
    markup: Decimal | None = None
    total: Decimal | None = None
    payload_json: dict[str, Any] | None = None


class DiscTradeSettlementCreate(StrictModel):
    s_date: date | None = None
    id_ccy: int | None = None
    settlement_type: str | None = Field(default=None, alias="type")
    payload_json: dict[str, Any] | None = None


class DiscTradeFieldsCreate(StrictModel):
    id_ccy: int | None = None
    d_date: date | None = None
    notional: Decimal | None = None
    payout_ccy_id: int | None = None
    buysell: Literal["Buy", "Sell"] | None = None
    i_type: str | None = None


class DiscTradeLegCreate(StrictModel):
    id_ac: int
    leg_id: str
    leg_code: str | None = None
    direction: Literal["Buy", "Sell"] | None = None
    notional: Decimal | None = None
    id_ccy: int | None = None
    instrument: DiscTradeInstrumentCreate | None = None
    premium: DiscTradePremiumCreate | None = None
    settlement: DiscTradeSettlementCreate | None = None
    fields: DiscTradeFieldsCreate | None = None


class DiscTradeCreateRequest(StrictModel):
    id_org: int
    id_f: int
    booked_by: int | None = None
    status: TradeStatus = TradeStatus.BOOKED
    id_book: int
    id_portfolio: int | None = None
    id_ctpy: int
    id_label: int
    ice_trade_id: str | None = None
    external_id: str | None = None
    description: str | None = None
    trade_name: str | None = None
    trade_date: date | None = None
    creation_time: datetime | None = None
    last_update_time: datetime | None = None
    volume: int | None = None
    ice_status: Literal["Success", "Failed"] | None = None
    originating_action: Literal["New", "Exercise", "Amendment", "Early termination"] | None = None
    legs: list[DiscTradeLegCreate] = Field(min_length=1)


class TradeTypeResponse(BaseModel):
    id_type: int
    code: TradeTypeCode
    name: str


class TradeSummaryResponse(BaseModel):
    id_trade: int
    id_org: int
    id_spe: int
    id_type: int
    type_code: TradeTypeCode
    id_f: int
    booked_by: int | None
    booked_at: datetime
    last_modified_by: int | None
    last_modified_at: datetime | None
    status: TradeStatus


class DiscTradeResponse(BaseModel):
    id_spe: int
    id_org: int
    id_book: int
    id_portfolio: int | None
    id_ctpy: int
    id_label: int
    ice_trade_id: str | None
    external_id: str | None
    description: str | None
    trade_name: str | None
    trade_date: date | None
    creation_time: datetime | None
    last_update_time: datetime | None
    volume: int | None
    ice_status: str | None
    originating_action: str | None


class DiscTradeInstrumentResponse(BaseModel):
    id_inst: int
    id_org: int
    id_leg: int
    id_ac: int | None
    notional: Decimal | None
    id_ccy: int | None
    buysell: str | None
    i_type: str | None
    trade_date: date | None
    isin: str | None
    bbg_ticker: str | None
    payload_json: dict[str, Any] | None


class DiscTradePremiumResponse(BaseModel):
    id_prem: int
    id_org: int
    id_leg: int
    amount: Decimal | None
    id_ccy: int | None
    p_date: date | None
    markup: Decimal | None
    total: Decimal | None
    payload_json: dict[str, Any] | None


class DiscTradeSettlementResponse(BaseModel):
    id_settle: int
    id_org: int
    id_leg: int
    s_date: date | None
    id_ccy: int | None
    settlement_type: str | None
    payload_json: dict[str, Any] | None


class DiscTradeFieldsResponse(BaseModel):
    id_field: int
    id_org: int
    id_leg: int
    id_ccy: int | None
    d_date: date | None
    notional: Decimal | None
    payout_ccy_id: int | None
    buysell: str | None
    i_type: str | None


class DiscTradeLegResponse(BaseModel):
    id_leg: int
    id_org: int
    id_disc: int
    id_ac: int
    leg_id: str
    leg_code: str | None
    direction: str | None
    notional: Decimal | None
    id_ccy: int | None
    instrument: DiscTradeInstrumentResponse | None = None
    premium: DiscTradePremiumResponse | None = None
    settlement: DiscTradeSettlementResponse | None = None
    fields: DiscTradeFieldsResponse | None = None


class DiscTradeAggregateResponse(BaseModel):
    trade: TradeSummaryResponse
    disc: DiscTradeResponse
    legs: list[DiscTradeLegResponse]


def build_trade_type_response(record: TradeTypeRecord) -> TradeTypeResponse:
    return TradeTypeResponse(id_type=record.id_type, code=record.code, name=record.name)



def build_trade_summary_response(record: TradeMasterRecord) -> TradeSummaryResponse:
    return TradeSummaryResponse(
        id_trade=record.id_trade,
        id_org=record.id_org,
        id_spe=record.id_spe,
        id_type=record.id_type,
        type_code=record.type_code,
        id_f=record.id_f,
        booked_by=record.booked_by,
        booked_at=record.booked_at,
        last_modified_by=record.last_modified_by,
        last_modified_at=record.last_modified_at,
        status=record.status,
    )



def _build_instrument_response(record: DiscTradeInstrumentRecord | None) -> DiscTradeInstrumentResponse | None:
    if record is None:
        return None
    return DiscTradeInstrumentResponse(**asdict(record))



def _build_premium_response(record: DiscTradePremiumRecord | None) -> DiscTradePremiumResponse | None:
    if record is None:
        return None
    return DiscTradePremiumResponse(**asdict(record))



def _build_settlement_response(record: DiscTradeSettlementRecord | None) -> DiscTradeSettlementResponse | None:
    if record is None:
        return None
    return DiscTradeSettlementResponse(**asdict(record))



def _build_fields_response(record: DiscTradeFieldRecord | None) -> DiscTradeFieldsResponse | None:
    if record is None:
        return None
    return DiscTradeFieldsResponse(**asdict(record))



def _build_leg_response(record: DiscTradeLegAggregate) -> DiscTradeLegResponse:
    return DiscTradeLegResponse(
        id_leg=record.leg.id_leg,
        id_org=record.leg.id_org,
        id_disc=record.leg.id_disc,
        id_ac=record.leg.id_ac,
        leg_id=record.leg.leg_id,
        leg_code=record.leg.leg_code,
        direction=record.leg.direction,
        notional=record.leg.notional,
        id_ccy=record.leg.id_ccy,
        instrument=_build_instrument_response(record.instrument),
        premium=_build_premium_response(record.premium),
        settlement=_build_settlement_response(record.settlement),
        fields=_build_fields_response(record.fields),
    )



def build_disc_trade_response(record: DiscTradeAggregate) -> DiscTradeAggregateResponse:
    return DiscTradeAggregateResponse(
        trade=build_trade_summary_response(record.trade),
        disc=DiscTradeResponse(**asdict(record.disc)),
        legs=[_build_leg_response(item) for item in record.legs],
    )
