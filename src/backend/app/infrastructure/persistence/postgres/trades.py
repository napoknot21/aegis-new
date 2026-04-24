from __future__ import annotations

from typing import Any

import psycopg

from app.domain.shared.errors import NotFoundError
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
from app.domain.trades.enums import TradeStatus, TradeTypeCode

from .base import PostgresUnitOfWorkBase, to_jsonb, translate_psycopg_error


class PostgresTradeUnitOfWork(PostgresUnitOfWorkBase):
    def list_trade_types(self, id_org: int) -> list[TradeTypeRecord]:
        self._ensure_default_trade_types(id_org)
        connection = self._connection_or_raise()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_type, code, name
                FROM trade_types
                WHERE id_org = %s
                ORDER BY id_type
                """,
                (id_org,),
            )
            rows = cursor.fetchall()
        return [_build_trade_type_record(row) for row in rows]

    def get_trade_type_by_code(self, id_org: int, code: TradeTypeCode) -> TradeTypeRecord:
        self._ensure_default_trade_types(id_org)
        connection = self._connection_or_raise()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_type, code, name
                FROM trade_types
                WHERE id_org = %s AND code = %s
                """,
                (id_org, code.value),
            )
            row = cursor.fetchone()
        if row is None:
            raise NotFoundError(f"Trade type {code.value} was not found for organisation {id_org}.")
        return _build_trade_type_record(row)

    def next_id_spe(self, id_org: int) -> int:
        return self._next_sequence_value("trade_spe", "id_spe")

    def next_id_trade(self, id_org: int) -> int:
        return self._next_sequence_value("trades", "id_trade")

    def next_id_leg(self, id_org: int) -> int:
        return self._next_sequence_value("trade_disc_legs", "id_leg")

    def next_id_instrument(self, id_org: int) -> int:
        return self._next_sequence_value("trade_disc_instruments", "id_inst")

    def next_id_premium(self, id_org: int) -> int:
        return self._next_sequence_value("trade_disc_premiums", "id_prem")

    def next_id_settlement(self, id_org: int) -> int:
        return self._next_sequence_value("trade_disc_settlements", "id_settle")

    def next_id_field(self, id_org: int) -> int:
        return self._next_sequence_value("trade_disc_fields", "id_field")

    def add_master_trade(self, trade: TradeMasterRecord) -> None:
        connection = self._connection_or_raise()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO trade_spe (id_spe, id_org)
                    VALUES (%s, %s)
                    """,
                    (trade.id_spe, trade.id_org),
                )
                cursor.execute(
                    """
                    INSERT INTO trades (
                        id_trade,
                        id_org,
                        id_spe,
                        id_type,
                        id_f,
                        booked_by,
                        booked_at,
                        last_modified_by,
                        last_modified_at,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        trade.id_trade,
                        trade.id_org,
                        trade.id_spe,
                        trade.id_type,
                        trade.id_f,
                        trade.booked_by,
                        trade.booked_at,
                        trade.last_modified_by,
                        trade.last_modified_at,
                        trade.status.value,
                    ),
                )
        except psycopg.Error as exc:
            raise translate_psycopg_error(exc, f"Could not create trade {trade.id_spe}.") from exc

    def add_disc_trade(self, trade: DiscTradeRecord) -> None:
        connection = self._connection_or_raise()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO trade_disc (
                        id_spe,
                        id_org,
                        id_book,
                        id_portfolio,
                        id_ctpy,
                        id_label,
                        ice_trade_id,
                        external_id,
                        description,
                        trade_name,
                        trade_date,
                        creation_time,
                        last_update_time,
                        volume,
                        ice_status,
                        originating_action
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        trade.id_spe,
                        trade.id_org,
                        trade.id_book,
                        trade.id_portfolio,
                        trade.id_ctpy,
                        trade.id_label,
                        trade.ice_trade_id,
                        trade.external_id,
                        trade.description,
                        trade.trade_name,
                        trade.trade_date,
                        trade.creation_time,
                        trade.last_update_time,
                        trade.volume,
                        trade.ice_status,
                        trade.originating_action,
                    ),
                )
        except psycopg.Error as exc:
            raise translate_psycopg_error(exc, f"Could not create DISC details for trade {trade.id_spe}.") from exc

    def add_disc_leg(self, leg: DiscTradeLegRecord) -> None:
        connection = self._connection_or_raise()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO trade_disc_legs (
                        id_leg,
                        id_org,
                        id_disc,
                        id_ac,
                        leg_id,
                        leg_code,
                        direction,
                        notional,
                        id_ccy
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        leg.id_leg,
                        leg.id_org,
                        leg.id_disc,
                        leg.id_ac,
                        leg.leg_id,
                        leg.leg_code,
                        leg.direction,
                        leg.notional,
                        leg.id_ccy,
                    ),
                )
        except psycopg.Error as exc:
            raise translate_psycopg_error(exc, f"Could not create leg {leg.leg_id} for trade {leg.id_disc}.") from exc

    def add_disc_instrument(self, instrument: DiscTradeInstrumentRecord) -> None:
        connection = self._connection_or_raise()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO trade_disc_instruments (
                        id_inst,
                        id_org,
                        id_leg,
                        id_ac,
                        notional,
                        id_ccy,
                        buysell,
                        i_type,
                        trade_date,
                        isin,
                        bbg_ticker,
                        payload_json
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        instrument.id_inst,
                        instrument.id_org,
                        instrument.id_leg,
                        instrument.id_ac,
                        instrument.notional,
                        instrument.id_ccy,
                        instrument.buysell,
                        instrument.i_type,
                        instrument.trade_date,
                        instrument.isin,
                        instrument.bbg_ticker,
                        to_jsonb(instrument.payload_json),
                    ),
                )
        except psycopg.Error as exc:
            raise translate_psycopg_error(exc, f"Could not create instrument for leg {instrument.id_leg}.") from exc

    def add_disc_premium(self, premium: DiscTradePremiumRecord) -> None:
        connection = self._connection_or_raise()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO trade_disc_premiums (
                        id_prem,
                        id_org,
                        id_leg,
                        amount,
                        id_ccy,
                        p_date,
                        markup,
                        total,
                        payload_json
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        premium.id_prem,
                        premium.id_org,
                        premium.id_leg,
                        premium.amount,
                        premium.id_ccy,
                        premium.p_date,
                        premium.markup,
                        premium.total,
                        to_jsonb(premium.payload_json),
                    ),
                )
        except psycopg.Error as exc:
            raise translate_psycopg_error(exc, f"Could not create premium for leg {premium.id_leg}.") from exc

    def add_disc_settlement(self, settlement: DiscTradeSettlementRecord) -> None:
        connection = self._connection_or_raise()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO trade_disc_settlements (
                        id_settle,
                        id_org,
                        id_leg,
                        s_date,
                        id_ccy,
                        type,
                        payload_json
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        settlement.id_settle,
                        settlement.id_org,
                        settlement.id_leg,
                        settlement.s_date,
                        settlement.id_ccy,
                        settlement.settlement_type,
                        to_jsonb(settlement.payload_json),
                    ),
                )
        except psycopg.Error as exc:
            raise translate_psycopg_error(exc, f"Could not create settlement for leg {settlement.id_leg}.") from exc

    def add_disc_fields(self, fields: DiscTradeFieldRecord) -> None:
        connection = self._connection_or_raise()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO trade_disc_fields (
                        id_field,
                        id_org,
                        id_leg,
                        id_ccy,
                        d_date,
                        notional,
                        payout_ccy_id,
                        buysell,
                        i_type
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        fields.id_field,
                        fields.id_org,
                        fields.id_leg,
                        fields.id_ccy,
                        fields.d_date,
                        fields.notional,
                        fields.payout_ccy_id,
                        fields.buysell,
                        fields.i_type,
                    ),
                )
        except psycopg.Error as exc:
            raise translate_psycopg_error(exc, f"Could not create field block for leg {fields.id_leg}.") from exc

    def list_trades(self, id_org: int, accessible_fund_ids: list[int] | None = None) -> list[TradeMasterRecord]:
        if accessible_fund_ids == []:
            return []

        connection = self._connection_or_raise()
        params: list[Any] = [id_org]
        fund_filter = ""
        if accessible_fund_ids is not None:
            fund_filter = " AND t.id_f = ANY(%s)"
            params.append(accessible_fund_ids)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    t.id_trade,
                    t.id_org,
                    t.id_spe,
                    t.id_type,
                    tt.code AS type_code,
                    t.id_f,
                    t.booked_by,
                    t.booked_at,
                    t.last_modified_by,
                    t.last_modified_at,
                    t.status
                FROM trades AS t
                JOIN trade_types AS tt
                  ON tt.id_org = t.id_org
                 AND tt.id_type = t.id_type
                WHERE t.id_org = %s
                {fund_filter}
                ORDER BY t.booked_at DESC, t.id_trade DESC
                """,
                params,
            )
            rows = cursor.fetchall()
        return [_build_trade_master_record(row) for row in rows]

    def get_disc_trade(self, id_org: int, id_spe: int) -> DiscTradeAggregate | None:
        connection = self._connection_or_raise()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    t.id_trade,
                    t.id_org,
                    t.id_spe,
                    t.id_type,
                    tt.code AS type_code,
                    t.id_f,
                    t.booked_by,
                    t.booked_at,
                    t.last_modified_by,
                    t.last_modified_at,
                    t.status,
                    d.id_book,
                    d.id_portfolio,
                    d.id_ctpy,
                    d.id_label,
                    d.ice_trade_id,
                    d.external_id,
                    d.description,
                    d.trade_name,
                    d.trade_date,
                    d.creation_time,
                    d.last_update_time,
                    d.volume,
                    d.ice_status,
                    d.originating_action
                FROM trades AS t
                JOIN trade_types AS tt
                  ON tt.id_org = t.id_org
                 AND tt.id_type = t.id_type
                JOIN trade_disc AS d
                  ON d.id_org = t.id_org
                 AND d.id_spe = t.id_spe
                WHERE t.id_org = %s
                  AND t.id_spe = %s
                """,
                (id_org, id_spe),
            )
            trade_row = cursor.fetchone()
        if trade_row is None:
            return None

        trade = _build_trade_master_record(trade_row)
        disc = _build_disc_trade_record(trade_row)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM trade_disc_legs
                WHERE id_org = %s
                  AND id_disc = %s
                ORDER BY id_leg
                """,
                (id_org, id_spe),
            )
            leg_rows = cursor.fetchall()

        leg_ids = [row["id_leg"] for row in leg_rows]
        instruments_by_leg = self._load_child_rows(
            table_name="trade_disc_instruments",
            id_org=id_org,
            leg_ids=leg_ids,
        )
        premiums_by_leg = self._load_child_rows(
            table_name="trade_disc_premiums",
            id_org=id_org,
            leg_ids=leg_ids,
        )
        settlements_by_leg = self._load_child_rows(
            table_name="trade_disc_settlements",
            id_org=id_org,
            leg_ids=leg_ids,
        )
        fields_by_leg = self._load_child_rows(
            table_name="trade_disc_fields",
            id_org=id_org,
            leg_ids=leg_ids,
        )

        legs: list[DiscTradeLegAggregate] = []
        for leg_row in leg_rows:
            leg_id = leg_row["id_leg"]
            legs.append(
                DiscTradeLegAggregate(
                    leg=_build_disc_trade_leg_record(leg_row),
                    instrument=_build_disc_trade_instrument_record(instruments_by_leg.get(leg_id)),
                    premium=_build_disc_trade_premium_record(premiums_by_leg.get(leg_id)),
                    settlement=_build_disc_trade_settlement_record(settlements_by_leg.get(leg_id)),
                    fields=_build_disc_trade_fields_record(fields_by_leg.get(leg_id)),
                )
            )

        return DiscTradeAggregate(trade=trade, disc=disc, legs=legs)

    def _ensure_default_trade_types(self, id_org: int) -> None:
        connection = self._connection_or_raise()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO trade_types (id_org, name, code)
                    VALUES
                        (%s, 'Discretionary', 'DISC'),
                        (%s, 'Advisory', 'ADV')
                    ON CONFLICT (id_org, code)
                    DO UPDATE SET name = EXCLUDED.name
                    """,
                    (id_org, id_org),
                )
        except psycopg.errors.ForeignKeyViolation as exc:
            raise NotFoundError(f"Organisation {id_org} was not found.") from exc
        except psycopg.Error as exc:
            raise translate_psycopg_error(exc, f"Could not initialize trade types for organisation {id_org}.") from exc

    def _load_child_rows(self, *, table_name: str, id_org: int, leg_ids: list[int]) -> dict[int, dict[str, Any]]:
        if not leg_ids:
            return {}

        connection = self._connection_or_raise()
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM {table_name}
                WHERE id_org = %s
                  AND id_leg = ANY(%s)
                """,
                (id_org, leg_ids),
            )
            rows = cursor.fetchall()
        return {int(row["id_leg"]): row for row in rows}


def _build_trade_type_record(row: dict[str, Any]) -> TradeTypeRecord:
    return TradeTypeRecord(
        id_type=int(row["id_type"]),
        code=TradeTypeCode(row["code"]),
        name=row["name"],
    )


def _build_trade_master_record(row: dict[str, Any]) -> TradeMasterRecord:
    return TradeMasterRecord(
        id_trade=int(row["id_trade"]),
        id_org=int(row["id_org"]),
        id_spe=int(row["id_spe"]),
        id_type=int(row["id_type"]),
        type_code=TradeTypeCode(row["type_code"]),
        id_f=int(row["id_f"]),
        booked_by=row["booked_by"],
        booked_at=row["booked_at"],
        last_modified_by=row["last_modified_by"],
        last_modified_at=row["last_modified_at"],
        status=TradeStatus(row["status"]),
    )


def _build_disc_trade_record(row: dict[str, Any]) -> DiscTradeRecord:
    return DiscTradeRecord(
        id_spe=int(row["id_spe"]),
        id_org=int(row["id_org"]),
        id_book=int(row["id_book"]),
        id_portfolio=row["id_portfolio"],
        id_ctpy=int(row["id_ctpy"]),
        id_label=int(row["id_label"]),
        ice_trade_id=row["ice_trade_id"],
        external_id=row["external_id"],
        description=row["description"],
        trade_name=row["trade_name"],
        trade_date=row["trade_date"],
        creation_time=row["creation_time"],
        last_update_time=row["last_update_time"],
        volume=row["volume"],
        ice_status=row["ice_status"],
        originating_action=row["originating_action"],
    )


def _build_disc_trade_leg_record(row: dict[str, Any]) -> DiscTradeLegRecord:
    return DiscTradeLegRecord(
        id_leg=int(row["id_leg"]),
        id_org=int(row["id_org"]),
        id_disc=int(row["id_disc"]),
        id_ac=int(row["id_ac"]),
        leg_id=row["leg_id"],
        leg_code=row["leg_code"],
        direction=row["direction"],
        notional=row["notional"],
        id_ccy=row["id_ccy"],
    )


def _build_disc_trade_instrument_record(row: dict[str, Any] | None) -> DiscTradeInstrumentRecord | None:
    if row is None:
        return None
    return DiscTradeInstrumentRecord(
        id_inst=int(row["id_inst"]),
        id_org=int(row["id_org"]),
        id_leg=int(row["id_leg"]),
        id_ac=row["id_ac"],
        notional=row["notional"],
        id_ccy=row["id_ccy"],
        buysell=row["buysell"],
        i_type=row["i_type"],
        trade_date=row["trade_date"],
        isin=row["isin"],
        bbg_ticker=row["bbg_ticker"],
        payload_json=row["payload_json"],
    )


def _build_disc_trade_premium_record(row: dict[str, Any] | None) -> DiscTradePremiumRecord | None:
    if row is None:
        return None
    return DiscTradePremiumRecord(
        id_prem=int(row["id_prem"]),
        id_org=int(row["id_org"]),
        id_leg=int(row["id_leg"]),
        amount=row["amount"],
        id_ccy=row["id_ccy"],
        p_date=row["p_date"],
        markup=row["markup"],
        total=row["total"],
        payload_json=row["payload_json"],
    )


def _build_disc_trade_settlement_record(row: dict[str, Any] | None) -> DiscTradeSettlementRecord | None:
    if row is None:
        return None
    return DiscTradeSettlementRecord(
        id_settle=int(row["id_settle"]),
        id_org=int(row["id_org"]),
        id_leg=int(row["id_leg"]),
        s_date=row["s_date"],
        id_ccy=row["id_ccy"],
        settlement_type=row["type"],
        payload_json=row["payload_json"],
    )


def _build_disc_trade_fields_record(row: dict[str, Any] | None) -> DiscTradeFieldRecord | None:
    if row is None:
        return None
    return DiscTradeFieldRecord(
        id_field=int(row["id_field"]),
        id_org=int(row["id_org"]),
        id_leg=int(row["id_leg"]),
        id_ccy=row["id_ccy"],
        d_date=row["d_date"],
        notional=row["notional"],
        payout_ccy_id=row["payout_ccy_id"],
        buysell=row["buysell"],
        i_type=row["i_type"],
    )
