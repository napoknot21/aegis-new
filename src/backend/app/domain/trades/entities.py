from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.domain.trades.enums import TradeStatus, TradeTypeCode


@dataclass(slots=True)
class TradeTypeRecord:
    id_type: int
    code: TradeTypeCode
    name: str


@dataclass(slots=True)
class TradeMasterRecord:
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


@dataclass(slots=True)
class DiscTradeRecord:
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


@dataclass(slots=True)
class DiscTradeLegRecord:
    id_leg: int
    id_org: int
    id_disc: int
    id_ac: int
    leg_id: str
    leg_code: str | None
    direction: str | None
    notional: Decimal | None
    id_ccy: int | None


@dataclass(slots=True)
class DiscTradeInstrumentRecord:
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


@dataclass(slots=True)
class DiscTradePremiumRecord:
    id_prem: int
    id_org: int
    id_leg: int
    amount: Decimal | None
    id_ccy: int | None
    p_date: date | None
    markup: Decimal | None
    total: Decimal | None
    payload_json: dict[str, Any] | None


@dataclass(slots=True)
class DiscTradeSettlementRecord:
    id_settle: int
    id_org: int
    id_leg: int
    s_date: date | None
    id_ccy: int | None
    settlement_type: str | None
    payload_json: dict[str, Any] | None


@dataclass(slots=True)
class DiscTradeFieldRecord:
    id_field: int
    id_org: int
    id_leg: int
    id_ccy: int | None
    d_date: date | None
    notional: Decimal | None
    payout_ccy_id: int | None
    buysell: str | None
    i_type: str | None


@dataclass(slots=True)
class DiscTradeLegAggregate:
    leg: DiscTradeLegRecord
    instrument: DiscTradeInstrumentRecord | None = None
    premium: DiscTradePremiumRecord | None = None
    settlement: DiscTradeSettlementRecord | None = None
    fields: DiscTradeFieldRecord | None = None


@dataclass(slots=True)
class DiscTradeAggregate:
    trade: TradeMasterRecord
    disc: DiscTradeRecord
    legs: list[DiscTradeLegAggregate] = field(default_factory=list)
