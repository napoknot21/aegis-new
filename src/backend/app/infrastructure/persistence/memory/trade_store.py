from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from app.domain.shared.errors import ConflictError, NotFoundError
from app.domain.trades.entities import (
    DiscTradeAggregate,
    DiscTradeFieldRecord,
    DiscTradeInstrumentRecord,
    DiscTradeLegAggregate,
    DiscTradeLegRecord,
    DiscTradePremiumRecord,
    DiscTradeRecord,
    DiscTradeSettlementRecord,
    TradeMasterRecord,
    TradeTypeRecord,
)
from app.domain.trades.enums import TradeTypeCode


@dataclass(slots=True)
class InMemoryTradeStore:
    counters: dict[tuple[int, str], int] = field(default_factory=dict)
    trade_types: dict[tuple[int, TradeTypeCode], TradeTypeRecord] = field(default_factory=dict)
    master_trades: dict[tuple[int, int], TradeMasterRecord] = field(default_factory=dict)
    disc_trades: dict[tuple[int, int], DiscTradeRecord] = field(default_factory=dict)
    disc_legs: dict[tuple[int, int], DiscTradeLegRecord] = field(default_factory=dict)
    disc_instruments: dict[tuple[int, int], DiscTradeInstrumentRecord] = field(default_factory=dict)
    disc_premiums: dict[tuple[int, int], DiscTradePremiumRecord] = field(default_factory=dict)
    disc_settlements: dict[tuple[int, int], DiscTradeSettlementRecord] = field(default_factory=dict)
    disc_fields: dict[tuple[int, int], DiscTradeFieldRecord] = field(default_factory=dict)


class InMemoryTradeUnitOfWork:
    def __init__(self, store: InMemoryTradeStore):
        self._store = store
        self._working: InMemoryTradeStore | None = None
        self._committed = False

    def __enter__(self) -> "InMemoryTradeUnitOfWork":
        self._working = deepcopy(self._store)
        self._committed = False
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None and self._working is not None:
            self.rollback()
        elif not self._committed and self._working is not None:
            self.rollback()

    def commit(self) -> None:
        if self._working is None:
            return
        self._store.counters = deepcopy(self._working.counters)
        self._store.trade_types = deepcopy(self._working.trade_types)
        self._store.master_trades = deepcopy(self._working.master_trades)
        self._store.disc_trades = deepcopy(self._working.disc_trades)
        self._store.disc_legs = deepcopy(self._working.disc_legs)
        self._store.disc_instruments = deepcopy(self._working.disc_instruments)
        self._store.disc_premiums = deepcopy(self._working.disc_premiums)
        self._store.disc_settlements = deepcopy(self._working.disc_settlements)
        self._store.disc_fields = deepcopy(self._working.disc_fields)
        self._committed = True

    def rollback(self) -> None:
        self._working = None
        self._committed = False

    def list_trade_types(self, id_org: int) -> list[TradeTypeRecord]:
        self._ensure_trade_types(id_org)
        return sorted(
            [record for (org_id, _), record in self._working.trade_types.items() if org_id == id_org],
            key=lambda item: item.id_type,
        )

    def get_trade_type_by_code(self, id_org: int, code: TradeTypeCode) -> TradeTypeRecord:
        self._ensure_trade_types(id_org)
        key = (id_org, code)
        trade_type = self._working.trade_types.get(key)
        if trade_type is None:
            raise NotFoundError(f"Trade type {code} was not found for organisation {id_org}.")
        return trade_type

    def next_id_spe(self, id_org: int) -> int:
        return self._next_counter(id_org, "spe", start=10_000)

    def next_id_trade(self, id_org: int) -> int:
        return self._next_counter(id_org, "trade", start=20_000)

    def next_id_leg(self, id_org: int) -> int:
        return self._next_counter(id_org, "leg", start=30_000)

    def next_id_instrument(self, id_org: int) -> int:
        return self._next_counter(id_org, "instrument", start=40_000)

    def next_id_premium(self, id_org: int) -> int:
        return self._next_counter(id_org, "premium", start=50_000)

    def next_id_settlement(self, id_org: int) -> int:
        return self._next_counter(id_org, "settlement", start=60_000)

    def next_id_field(self, id_org: int) -> int:
        return self._next_counter(id_org, "field", start=70_000)

    def add_master_trade(self, trade: TradeMasterRecord) -> None:
        key = (trade.id_org, trade.id_spe)
        if key in self._working.master_trades:
            raise ConflictError(f"Trade {trade.id_spe} already exists for organisation {trade.id_org}.")
        self._working.master_trades[key] = trade

    def add_disc_trade(self, trade: DiscTradeRecord) -> None:
        key = (trade.id_org, trade.id_spe)
        if key in self._working.disc_trades:
            raise ConflictError(f"DISC trade {trade.id_spe} already exists for organisation {trade.id_org}.")
        self._working.disc_trades[key] = trade

    def add_disc_leg(self, leg: DiscTradeLegRecord) -> None:
        key = (leg.id_org, leg.id_leg)
        if key in self._working.disc_legs:
            raise ConflictError(f"Leg {leg.id_leg} already exists for organisation {leg.id_org}.")
        self._working.disc_legs[key] = leg

    def add_disc_instrument(self, instrument: DiscTradeInstrumentRecord) -> None:
        key = (instrument.id_org, instrument.id_leg)
        if key in self._working.disc_instruments:
            raise ConflictError(f"Instrument block already exists for leg {instrument.id_leg}.")
        self._working.disc_instruments[key] = instrument

    def add_disc_premium(self, premium: DiscTradePremiumRecord) -> None:
        key = (premium.id_org, premium.id_leg)
        if key in self._working.disc_premiums:
            raise ConflictError(f"Premium block already exists for leg {premium.id_leg}.")
        self._working.disc_premiums[key] = premium

    def add_disc_settlement(self, settlement: DiscTradeSettlementRecord) -> None:
        key = (settlement.id_org, settlement.id_leg)
        if key in self._working.disc_settlements:
            raise ConflictError(f"Settlement block already exists for leg {settlement.id_leg}.")
        self._working.disc_settlements[key] = settlement

    def add_disc_fields(self, fields: DiscTradeFieldRecord) -> None:
        key = (fields.id_org, fields.id_leg)
        if key in self._working.disc_fields:
            raise ConflictError(f"Fields block already exists for leg {fields.id_leg}.")
        self._working.disc_fields[key] = fields

    def list_trades(self, id_org: int) -> list[TradeMasterRecord]:
        records = [record for (org_id, _), record in self._working.master_trades.items() if org_id == id_org]
        return sorted(records, key=lambda item: item.booked_at, reverse=True)

    def get_disc_trade(self, id_org: int, id_spe: int) -> DiscTradeAggregate | None:
        master = self._working.master_trades.get((id_org, id_spe))
        disc = self._working.disc_trades.get((id_org, id_spe))
        if master is None or disc is None:
            return None

        legs = [
            leg
            for (org_id, _), leg in self._working.disc_legs.items()
            if org_id == id_org and leg.id_disc == id_spe
        ]
        legs.sort(key=lambda item: item.id_leg)

        aggregate_legs: list[DiscTradeLegAggregate] = []
        for leg in legs:
            key = (id_org, leg.id_leg)
            aggregate_legs.append(
                DiscTradeLegAggregate(
                    leg=leg,
                    instrument=self._working.disc_instruments.get(key),
                    premium=self._working.disc_premiums.get(key),
                    settlement=self._working.disc_settlements.get(key),
                    fields=self._working.disc_fields.get(key),
                )
            )

        return DiscTradeAggregate(trade=master, disc=disc, legs=aggregate_legs)

    def _ensure_trade_types(self, id_org: int) -> None:
        definitions = (
            (TradeTypeCode.DISC, 1, "Discretionary"),
            (TradeTypeCode.ADV, 2, "Advisory"),
        )
        for code, id_type, name in definitions:
            key = (id_org, code)
            if key not in self._working.trade_types:
                self._working.trade_types[key] = TradeTypeRecord(
                    id_type=id_type,
                    code=code,
                    name=name,
                )

    def _next_counter(self, id_org: int, name: str, start: int) -> int:
        key = (id_org, name)
        current = self._working.counters.get(key, start - 1) + 1
        self._working.counters[key] = current
        return current
