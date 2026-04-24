from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import psycopg

from app.domain.data_snapshots.catalog import get_dataset_catalog
from app.domain.data_snapshots.entities import (
    DataSnapshotAggregate,
    DataSnapshotRecord,
    DataSnapshotRowRecord,
    DatasetDefinition,
)
from app.domain.data_snapshots.enums import DatasetCode, SnapshotStatus
from app.domain.shared.errors import DomainError, NotFoundError

from .base import PostgresUnitOfWorkBase, to_jsonb, translate_psycopg_error


@dataclass(frozen=True, slots=True)
class SnapshotSqlMapping:
    snapshot_table: str
    snapshot_pk: str
    row_table: str
    row_pk: str
    row_snapshot_fk: str
    as_of_date_col: str | None
    as_of_ts_col: str | None
    loaded_at_col: str
    source_name_col: str | None
    source_file_name_col: str | None
    source_generated_at_col: str | None
    is_official_col: str | None
    fixed_source_name: str | None = None
    row_has_fund: bool = True


_SNAPSHOT_SQL: dict[DatasetCode, SnapshotSqlMapping] = {
    DatasetCode.AUM: SnapshotSqlMapping(
        snapshot_table="aum_snapshots",
        snapshot_pk="id_aum_snapshot",
        row_table="aum_rows",
        row_pk="id_aum_row",
        row_snapshot_fk="id_aum_snapshot",
        as_of_date_col="as_of_date",
        as_of_ts_col=None,
        loaded_at_col="loaded_at",
        source_name_col="source_name",
        source_file_name_col="source_file_name",
        source_generated_at_col="source_generated_at",
        is_official_col="is_official",
    ),
    DatasetCode.SIMM: SnapshotSqlMapping(
        snapshot_table="simm_snapshots",
        snapshot_pk="id_simm_snapshot",
        row_table="simm_snapshot_rows",
        row_pk="id_simm_row",
        row_snapshot_fk="id_simm_snapshot",
        as_of_date_col="as_of_date",
        as_of_ts_col=None,
        loaded_at_col="loaded_at",
        source_name_col="source_name",
        source_file_name_col="source_file_name",
        source_generated_at_col="source_generated_at",
        is_official_col="is_official",
    ),
    DatasetCode.EXPIRIES: SnapshotSqlMapping(
        snapshot_table="expiries_snapshots",
        snapshot_pk="id_exp_snapshot",
        row_table="expiries",
        row_pk="id_exp_row",
        row_snapshot_fk="id_exp_snapshot",
        as_of_date_col="snapshot_date",
        as_of_ts_col="snapshot_ts",
        loaded_at_col="imported_at",
        source_name_col=None,
        source_file_name_col="file_name",
        source_generated_at_col=None,
        is_official_col="is_latest_for_day",
        fixed_source_name="file",
        row_has_fund=False,
    ),
    DatasetCode.NAV_ESTIMATED: SnapshotSqlMapping(
        snapshot_table="nav_estimated_snapshots",
        snapshot_pk="id_nav_est_snapshot",
        row_table="nav_estimated",
        row_pk="id_nav_est_row",
        row_snapshot_fk="id_nav_est_snapshot",
        as_of_date_col=None,
        as_of_ts_col="as_of_ts",
        loaded_at_col="loaded_at",
        source_name_col="source_name",
        source_file_name_col="source_file_name",
        source_generated_at_col="source_generated_at",
        is_official_col="is_official",
    ),
    DatasetCode.LEVERAGES: SnapshotSqlMapping(
        snapshot_table="leverages_snapshots",
        snapshot_pk="id_leverage_snapshot",
        row_table="leverages",
        row_pk="id_leverage_row",
        row_snapshot_fk="id_leverage_snapshot",
        as_of_date_col=None,
        as_of_ts_col="as_of_ts",
        loaded_at_col="loaded_at",
        source_name_col="source_name",
        source_file_name_col="source_file_name",
        source_generated_at_col="source_generated_at",
        is_official_col="is_official",
    ),
    DatasetCode.LEVERAGES_PER_TRADE: SnapshotSqlMapping(
        snapshot_table="leverages_per_trade_snapshots",
        snapshot_pk="id_leverage_trade_snapshot",
        row_table="leverages_per_trade",
        row_pk="id_leverage_trade_row",
        row_snapshot_fk="id_leverage_trade_snapshot",
        as_of_date_col=None,
        as_of_ts_col="as_of_ts",
        loaded_at_col="loaded_at",
        source_name_col="source_name",
        source_file_name_col="source_file_name",
        source_generated_at_col="source_generated_at",
        is_official_col="is_official",
    ),
    DatasetCode.LEVERAGES_PER_UNDERLYING: SnapshotSqlMapping(
        snapshot_table="leverages_per_underlying_snapshots",
        snapshot_pk="id_leverage_underlying_snapshot",
        row_table="leverages_per_underlying",
        row_pk="id_leverage_underlying_row",
        row_snapshot_fk="id_leverage_underlying_snapshot",
        as_of_date_col=None,
        as_of_ts_col="as_of_ts",
        loaded_at_col="loaded_at",
        source_name_col="source_name",
        source_file_name_col="source_file_name",
        source_generated_at_col="source_generated_at",
        is_official_col="is_official",
    ),
    DatasetCode.LONG_SHORT_DELTA: SnapshotSqlMapping(
        snapshot_table="long_short_delta_snapshots",
        snapshot_pk="id_long_short_delta_snapshot",
        row_table="long_short_delta",
        row_pk="id_long_short_delta_row",
        row_snapshot_fk="id_long_short_delta_snapshot",
        as_of_date_col=None,
        as_of_ts_col="as_of_ts",
        loaded_at_col="loaded_at",
        source_name_col="source_name",
        source_file_name_col="source_file_name",
        source_generated_at_col="source_generated_at",
        is_official_col="is_official",
    ),
    DatasetCode.COUNTERPARTY_CONCENTRATION: SnapshotSqlMapping(
        snapshot_table="counterparty_concentration_snapshots",
        snapshot_pk="id_ctpy_concentration_snapshot",
        row_table="counterparty_concentration",
        row_pk="id_ctpy_concentration_row",
        row_snapshot_fk="id_ctpy_concentration_snapshot",
        as_of_date_col=None,
        as_of_ts_col="as_of_ts",
        loaded_at_col="loaded_at",
        source_name_col="source_name",
        source_file_name_col="source_file_name",
        source_generated_at_col="source_generated_at",
        is_official_col="is_official",
    ),
}


class PostgresDataSnapshotUnitOfWork(PostgresUnitOfWorkBase):
    def __init__(self, database_url: str):
        super().__init__(database_url)
        self._definitions = get_dataset_catalog()
        self._snapshot_cache: dict[tuple[DatasetCode, int, int], DataSnapshotRecord] = {}

    def list_dataset_definitions(self) -> list[DatasetDefinition]:
        return list(self._definitions.values())

    def get_dataset_definition(self, dataset: DatasetCode) -> DatasetDefinition:
        definition = self._definitions.get(dataset)
        if definition is None:
            raise NotFoundError(f"Dataset {dataset.value} is not registered.")
        return definition

    def list_snapshots(
        self,
        dataset: DatasetCode,
        id_org: int,
        accessible_fund_ids: list[int] | None = None,
        id_f: int | None = None,
        status: SnapshotStatus | None = None,
        is_official: bool | None = None,
        as_of_date: date | None = None,
        as_of_date_from: date | None = None,
        as_of_date_to: date | None = None,
    ) -> list[DataSnapshotRecord]:
        mapping = _SNAPSHOT_SQL[dataset]
        connection = self._connection_or_raise()
        if accessible_fund_ids == []:
            return []
        filters = ["id_org = %s"]
        params: list[Any] = [id_org]
        if accessible_fund_ids is not None:
            filters.append("id_f = ANY(%s)")
            params.append(accessible_fund_ids)
        if id_f is not None:
            filters.append("id_f = %s")
            params.append(id_f)
        if status is not None:
            filters.append("status = %s")
            params.append(status.value)
        if is_official is not None:
            filters.append(f"{_official_filter_sql(dataset, mapping)} = %s")
            params.append(is_official)
        if as_of_date is not None:
            filters.append(f"{_as_of_date_expr(mapping)} = %s")
            params.append(as_of_date)
        if as_of_date_from is not None:
            filters.append(f"{_as_of_date_expr(mapping)} >= %s")
            params.append(as_of_date_from)
        if as_of_date_to is not None:
            filters.append(f"{_as_of_date_expr(mapping)} <= %s")
            params.append(as_of_date_to)

        order_by = mapping.as_of_ts_col or mapping.as_of_date_col or mapping.loaded_at_col
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM {mapping.snapshot_table}
                WHERE {" AND ".join(filters)}
                ORDER BY {order_by} DESC, {mapping.snapshot_pk} DESC
                """,
                params,
            )
            rows = cursor.fetchall()
        return [self._build_snapshot_record(dataset, row) for row in rows]

    def get_snapshot(self, dataset: DatasetCode, id_org: int, snapshot_id: int) -> DataSnapshotAggregate | None:
        snapshot = self._load_snapshot_record(dataset=dataset, id_org=id_org, snapshot_id=snapshot_id)
        if snapshot is None:
            return None

        mapping = _SNAPSHOT_SQL[dataset]
        connection = self._connection_or_raise()
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM {mapping.row_table}
                WHERE id_org = %s
                  AND {mapping.row_snapshot_fk} = %s
                ORDER BY {mapping.row_pk}
                """,
                (id_org, snapshot_id),
            )
            rows = cursor.fetchall()

        definition = self.get_dataset_definition(dataset)
        aggregate_rows = [
            self._build_snapshot_row_record(dataset=dataset, snapshot=snapshot, row=row)
            for row in rows
        ]
        return DataSnapshotAggregate(definition=definition, snapshot=snapshot, rows=aggregate_rows)

    def next_snapshot_id(self, dataset: DatasetCode, id_org: int) -> int:
        mapping = _SNAPSHOT_SQL[dataset]
        return self._next_sequence_value(mapping.snapshot_table, mapping.snapshot_pk)

    def next_row_id(self, dataset: DatasetCode, id_org: int) -> int:
        mapping = _SNAPSHOT_SQL[dataset]
        return self._next_sequence_value(mapping.row_table, mapping.row_pk)

    def add_snapshot(self, snapshot: DataSnapshotRecord) -> None:
        connection = self._connection_or_raise()
        try:
            with connection.cursor() as cursor:
                self._insert_snapshot(cursor=cursor, snapshot=snapshot)
        except psycopg.Error as exc:
            raise translate_psycopg_error(
                exc,
                f"Could not create {snapshot.dataset.value} snapshot {snapshot.snapshot_id}.",
            ) from exc
        self._snapshot_cache[(snapshot.dataset, snapshot.id_org, snapshot.snapshot_id)] = snapshot

    def add_snapshot_row(self, row: DataSnapshotRowRecord) -> None:
        snapshot = self._load_snapshot_record(
            dataset=row.dataset,
            id_org=row.id_org,
            snapshot_id=row.snapshot_id,
        )
        if snapshot is None:
            raise NotFoundError(
                f"{row.dataset.value} snapshot {row.snapshot_id} was not found for organisation {row.id_org}."
            )

        connection = self._connection_or_raise()
        try:
            with connection.cursor() as cursor:
                self._insert_snapshot_row(cursor=cursor, snapshot=snapshot, row=row)
        except psycopg.Error as exc:
            raise translate_psycopg_error(
                exc,
                f"Could not append row {row.row_id} to {row.dataset.value} snapshot {row.snapshot_id}.",
            ) from exc

    def _load_snapshot_record(
        self,
        *,
        dataset: DatasetCode,
        id_org: int,
        snapshot_id: int,
    ) -> DataSnapshotRecord | None:
        cache_key = (dataset, id_org, snapshot_id)
        cached = self._snapshot_cache.get(cache_key)
        if cached is not None:
            return cached

        mapping = _SNAPSHOT_SQL[dataset]
        connection = self._connection_or_raise()
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM {mapping.snapshot_table}
                WHERE id_org = %s
                  AND {mapping.snapshot_pk} = %s
                """,
                (id_org, snapshot_id),
            )
            row = cursor.fetchone()
        if row is None:
            return None

        record = self._build_snapshot_record(dataset, row)
        self._snapshot_cache[cache_key] = record
        return record

    def _build_snapshot_record(self, dataset: DatasetCode, row: dict[str, Any]) -> DataSnapshotRecord:
        mapping = _SNAPSHOT_SQL[dataset]
        as_of_ts = row[mapping.as_of_ts_col] if mapping.as_of_ts_col else None
        as_of_date = row[mapping.as_of_date_col] if mapping.as_of_date_col else as_of_ts.date()
        source_name = (
            row[mapping.source_name_col]
            if mapping.source_name_col is not None
            else mapping.fixed_source_name
            or self.get_dataset_definition(dataset).default_source_name
        )
        source_file_name = row[mapping.source_file_name_col] if mapping.source_file_name_col else None
        source_generated_at = row[mapping.source_generated_at_col] if mapping.source_generated_at_col else None
        is_official = bool(row[mapping.is_official_col]) if mapping.is_official_col else False
        if dataset == DatasetCode.EXPIRIES and row["status"] == SnapshotStatus.OFFICIAL.value:
            is_official = True

        return DataSnapshotRecord(
            snapshot_id=int(row[mapping.snapshot_pk]),
            dataset=dataset,
            id_org=int(row["id_org"]),
            id_run=int(row["id_run"]),
            id_f=int(row["id_f"]),
            as_of_date=as_of_date,
            as_of_ts=as_of_ts,
            source_name=source_name,
            source_file_name=source_file_name,
            source_generated_at=source_generated_at,
            loaded_at=row[mapping.loaded_at_col],
            status=SnapshotStatus(row["status"]),
            row_count=int(row["row_count"]),
            is_official=is_official,
            notes=row.get("notes"),
        )

    def _build_snapshot_row_record(
        self,
        *,
        dataset: DatasetCode,
        snapshot: DataSnapshotRecord,
        row: dict[str, Any],
    ) -> DataSnapshotRowRecord:
        mapping = _SNAPSHOT_SQL[dataset]
        return DataSnapshotRowRecord(
            row_id=int(row[mapping.row_pk]),
            dataset=dataset,
            snapshot_id=snapshot.snapshot_id,
            id_org=snapshot.id_org,
            id_f=int(row["id_f"]) if mapping.row_has_fund else snapshot.id_f,
            row_key=_row_key_from_db_row(dataset, row),
            payload_json=_payload_from_db_row(dataset, row),
            created_at=row["created_at"],
        )

    def _insert_snapshot(self, *, cursor, snapshot: DataSnapshotRecord) -> None:
        status_value = snapshot.status.value
        if snapshot.dataset == DatasetCode.EXPIRIES and snapshot.is_official:
            status_value = SnapshotStatus.OFFICIAL.value

        if snapshot.dataset == DatasetCode.AUM:
            cursor.execute(
                """
                INSERT INTO aum_snapshots (
                    id_aum_snapshot,
                    id_org,
                    id_run,
                    id_f,
                    as_of_date,
                    source_name,
                    source_file_name,
                    source_generated_at,
                    loaded_at,
                    status,
                    row_count,
                    is_official,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.id_org,
                    snapshot.id_run,
                    snapshot.id_f,
                    snapshot.as_of_date,
                    snapshot.source_name,
                    snapshot.source_file_name,
                    snapshot.source_generated_at,
                    snapshot.loaded_at,
                    snapshot.status.value,
                    snapshot.row_count,
                    snapshot.is_official,
                    snapshot.notes,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.SIMM:
            cursor.execute(
                """
                INSERT INTO simm_snapshots (
                    id_simm_snapshot,
                    id_org,
                    id_run,
                    id_f,
                    as_of_date,
                    source_name,
                    source_file_name,
                    source_generated_at,
                    loaded_at,
                    status,
                    row_count,
                    is_official,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.id_org,
                    snapshot.id_run,
                    snapshot.id_f,
                    snapshot.as_of_date,
                    snapshot.source_name,
                    snapshot.source_file_name,
                    snapshot.source_generated_at,
                    snapshot.loaded_at,
                    snapshot.status.value,
                    snapshot.row_count,
                    snapshot.is_official,
                    snapshot.notes,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.EXPIRIES:
            if not snapshot.source_file_name:
                raise DomainError("EXPIRIES snapshots require source_file_name.")
            cursor.execute(
                """
                INSERT INTO expiries_snapshots (
                    id_exp_snapshot,
                    id_org,
                    id_run,
                    id_f,
                    snapshot_date,
                    snapshot_ts,
                    file_name,
                    imported_at,
                    row_count,
                    is_latest_for_day,
                    status,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.id_org,
                    snapshot.id_run,
                    snapshot.id_f,
                    snapshot.as_of_date,
                    snapshot.as_of_ts,
                    snapshot.source_file_name,
                    snapshot.loaded_at,
                    snapshot.row_count,
                    snapshot.is_official,
                    status_value,
                    snapshot.notes,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.NAV_ESTIMATED:
            cursor.execute(
                """
                INSERT INTO nav_estimated_snapshots (
                    id_nav_est_snapshot,
                    id_org,
                    id_run,
                    id_f,
                    as_of_ts,
                    source_name,
                    source_file_name,
                    source_generated_at,
                    loaded_at,
                    status,
                    row_count,
                    is_official,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.id_org,
                    snapshot.id_run,
                    snapshot.id_f,
                    snapshot.as_of_ts,
                    snapshot.source_name,
                    snapshot.source_file_name,
                    snapshot.source_generated_at,
                    snapshot.loaded_at,
                    snapshot.status.value,
                    snapshot.row_count,
                    snapshot.is_official,
                    snapshot.notes,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.LEVERAGES:
            cursor.execute(
                """
                INSERT INTO leverages_snapshots (
                    id_leverage_snapshot,
                    id_org,
                    id_run,
                    id_f,
                    as_of_ts,
                    source_name,
                    source_file_name,
                    source_generated_at,
                    loaded_at,
                    status,
                    row_count,
                    is_official,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.id_org,
                    snapshot.id_run,
                    snapshot.id_f,
                    snapshot.as_of_ts,
                    snapshot.source_name,
                    snapshot.source_file_name,
                    snapshot.source_generated_at,
                    snapshot.loaded_at,
                    snapshot.status.value,
                    snapshot.row_count,
                    snapshot.is_official,
                    snapshot.notes,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.LEVERAGES_PER_TRADE:
            cursor.execute(
                """
                INSERT INTO leverages_per_trade_snapshots (
                    id_leverage_trade_snapshot,
                    id_org,
                    id_run,
                    id_f,
                    as_of_ts,
                    source_name,
                    source_file_name,
                    source_generated_at,
                    loaded_at,
                    status,
                    row_count,
                    is_official,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.id_org,
                    snapshot.id_run,
                    snapshot.id_f,
                    snapshot.as_of_ts,
                    snapshot.source_name,
                    snapshot.source_file_name,
                    snapshot.source_generated_at,
                    snapshot.loaded_at,
                    snapshot.status.value,
                    snapshot.row_count,
                    snapshot.is_official,
                    snapshot.notes,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.LEVERAGES_PER_UNDERLYING:
            cursor.execute(
                """
                INSERT INTO leverages_per_underlying_snapshots (
                    id_leverage_underlying_snapshot,
                    id_org,
                    id_run,
                    id_f,
                    as_of_ts,
                    source_name,
                    source_file_name,
                    source_generated_at,
                    loaded_at,
                    status,
                    row_count,
                    is_official,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.id_org,
                    snapshot.id_run,
                    snapshot.id_f,
                    snapshot.as_of_ts,
                    snapshot.source_name,
                    snapshot.source_file_name,
                    snapshot.source_generated_at,
                    snapshot.loaded_at,
                    snapshot.status.value,
                    snapshot.row_count,
                    snapshot.is_official,
                    snapshot.notes,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.LONG_SHORT_DELTA:
            cursor.execute(
                """
                INSERT INTO long_short_delta_snapshots (
                    id_long_short_delta_snapshot,
                    id_org,
                    id_run,
                    id_f,
                    as_of_ts,
                    source_name,
                    source_file_name,
                    source_generated_at,
                    loaded_at,
                    status,
                    row_count,
                    is_official,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.id_org,
                    snapshot.id_run,
                    snapshot.id_f,
                    snapshot.as_of_ts,
                    snapshot.source_name,
                    snapshot.source_file_name,
                    snapshot.source_generated_at,
                    snapshot.loaded_at,
                    snapshot.status.value,
                    snapshot.row_count,
                    snapshot.is_official,
                    snapshot.notes,
                ),
            )
            return

        cursor.execute(
            """
            INSERT INTO counterparty_concentration_snapshots (
                id_ctpy_concentration_snapshot,
                id_org,
                id_run,
                id_f,
                as_of_ts,
                source_name,
                source_file_name,
                source_generated_at,
                loaded_at,
                status,
                row_count,
                is_official,
                notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                snapshot.snapshot_id,
                snapshot.id_org,
                snapshot.id_run,
                snapshot.id_f,
                snapshot.as_of_ts,
                snapshot.source_name,
                snapshot.source_file_name,
                snapshot.source_generated_at,
                snapshot.loaded_at,
                snapshot.status.value,
                snapshot.row_count,
                snapshot.is_official,
                snapshot.notes,
            ),
        )

    def _insert_snapshot_row(self, *, cursor, snapshot: DataSnapshotRecord, row: DataSnapshotRowRecord) -> None:
        payload = row.payload_json

        if snapshot.dataset == DatasetCode.AUM:
            cursor.execute(
                """
                INSERT INTO aum_rows (
                    id_aum_row,
                    id_org,
                    id_aum_snapshot,
                    id_f,
                    as_of_date,
                    aum_value,
                    id_ccy,
                    valuation_ts,
                    raw_payload_json,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row.row_id,
                    row.id_org,
                    row.snapshot_id,
                    snapshot.id_f,
                    snapshot.as_of_date,
                    payload.get("aum_value"),
                    payload.get("id_ccy"),
                    payload.get("valuation_ts"),
                    to_jsonb(payload),
                    row.created_at,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.SIMM:
            counterparty_raw = payload.get("counterparty_raw") or row.row_key
            if not counterparty_raw:
                raise DomainError("SIMM rows require counterparty_raw or row_key.")
            if payload.get("im_value") is None:
                raise DomainError("SIMM rows require im_value.")
            cursor.execute(
                """
                INSERT INTO simm_snapshot_rows (
                    id_simm_row,
                    id_org,
                    id_simm_snapshot,
                    id_f,
                    as_of_date,
                    id_ctpy,
                    counterparty_raw,
                    im_value,
                    mv_value,
                    mv_capped_value,
                    capped_type,
                    net_margin_value,
                    raw_payload_json,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row.row_id,
                    row.id_org,
                    row.snapshot_id,
                    snapshot.id_f,
                    snapshot.as_of_date,
                    payload.get("id_ctpy"),
                    counterparty_raw,
                    payload.get("im_value"),
                    payload.get("mv_value"),
                    payload.get("mv_capped_value"),
                    payload.get("capped_type"),
                    payload.get("net_margin_value"),
                    to_jsonb(payload),
                    row.created_at,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.EXPIRIES:
            row_hash = payload.get("row_hash") or row.row_key
            if not row_hash:
                raise DomainError("EXPIRIES rows require row_hash or row_key.")
            cursor.execute(
                """
                INSERT INTO expiries (
                    id_exp_row,
                    id_org,
                    id_exp_snapshot,
                    trade_type,
                    underlying_asset,
                    termination_date,
                    buy_sell,
                    notional,
                    portfolio_name,
                    id_ac,
                    call_put,
                    strike,
                    trigger_value,
                    reference_spot,
                    id_ctpy,
                    mv_value,
                    total_premium_value,
                    strike_1,
                    strike_2,
                    trigger_2,
                    id_ccy,
                    days_remaining,
                    as_of_ts,
                    row_hash,
                    raw_payload_json,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row.row_id,
                    row.id_org,
                    row.snapshot_id,
                    payload.get("trade_type"),
                    payload.get("underlying_asset"),
                    payload.get("termination_date"),
                    payload.get("buy_sell"),
                    payload.get("notional"),
                    payload.get("portfolio_name"),
                    payload.get("id_ac"),
                    payload.get("call_put"),
                    payload.get("strike"),
                    payload.get("trigger_value"),
                    payload.get("reference_spot"),
                    payload.get("id_ctpy"),
                    payload.get("mv_value"),
                    payload.get("total_premium_value"),
                    payload.get("strike_1"),
                    payload.get("strike_2"),
                    payload.get("trigger_2"),
                    payload.get("id_ccy"),
                    payload.get("days_remaining"),
                    payload.get("as_of_ts") or snapshot.as_of_ts,
                    row_hash,
                    to_jsonb(payload),
                    row.created_at,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.NAV_ESTIMATED:
            cursor.execute(
                """
                INSERT INTO nav_estimated (
                    id_nav_est_row,
                    id_org,
                    id_nav_est_snapshot,
                    id_f,
                    nav_estimate,
                    nav_estimate_weighted_by_time,
                    comment,
                    as_of_ts,
                    raw_payload_json,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row.row_id,
                    row.id_org,
                    row.snapshot_id,
                    snapshot.id_f,
                    payload.get("nav_estimate"),
                    payload.get("nav_estimate_weighted_by_time"),
                    payload.get("comment"),
                    payload.get("as_of_ts") or snapshot.as_of_ts,
                    to_jsonb(payload),
                    row.created_at,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.LEVERAGES:
            cursor.execute(
                """
                INSERT INTO leverages (
                    id_leverage_row,
                    id_org,
                    id_leverage_snapshot,
                    id_f,
                    as_of_ts,
                    gross_leverage,
                    commitment_leverage,
                    raw_payload_json,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row.row_id,
                    row.id_org,
                    row.snapshot_id,
                    snapshot.id_f,
                    payload.get("as_of_ts") or snapshot.as_of_ts,
                    payload.get("gross_leverage"),
                    payload.get("commitment_leverage"),
                    to_jsonb(payload),
                    row.created_at,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.LEVERAGES_PER_TRADE:
            trade_id = payload.get("trade_id")
            if trade_id is None and row.row_key is not None:
                trade_id = _coerce_int(row.row_key, "trade_id")
            cursor.execute(
                """
                INSERT INTO leverages_per_trade (
                    id_leverage_trade_row,
                    id_org,
                    id_leverage_trade_snapshot,
                    id_f,
                    as_of_ts,
                    trade_id,
                    id_ac,
                    trade_type,
                    underlying_asset,
                    termination_date,
                    buy_sell,
                    notional,
                    call_put,
                    strike,
                    trigger_value,
                    reference_spot,
                    counterparty_raw,
                    id_ctpy,
                    gross_leverage,
                    exposure_pct_nav,
                    compliance,
                    raw_payload_json,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row.row_id,
                    row.id_org,
                    row.snapshot_id,
                    snapshot.id_f,
                    payload.get("as_of_ts") or snapshot.as_of_ts,
                    trade_id,
                    payload.get("id_ac"),
                    payload.get("trade_type"),
                    payload.get("underlying_asset"),
                    payload.get("termination_date"),
                    payload.get("buy_sell"),
                    payload.get("notional"),
                    payload.get("call_put"),
                    payload.get("strike"),
                    payload.get("trigger_value"),
                    payload.get("reference_spot"),
                    payload.get("counterparty_raw"),
                    payload.get("id_ctpy"),
                    payload.get("gross_leverage"),
                    payload.get("exposure_pct_nav"),
                    payload.get("compliance"),
                    to_jsonb(payload),
                    row.created_at,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.LEVERAGES_PER_UNDERLYING:
            underlying_asset = payload.get("underlying_asset") or row.row_key
            cursor.execute(
                """
                INSERT INTO leverages_per_underlying (
                    id_leverage_underlying_row,
                    id_org,
                    id_leverage_underlying_snapshot,
                    id_f,
                    as_of_ts,
                    id_ac,
                    underlying_asset,
                    gross_leverage,
                    exposure_pct_nav,
                    compliance,
                    exposure_pct_nav_final,
                    raw_payload_json,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row.row_id,
                    row.id_org,
                    row.snapshot_id,
                    snapshot.id_f,
                    payload.get("as_of_ts") or snapshot.as_of_ts,
                    payload.get("id_ac"),
                    underlying_asset,
                    payload.get("gross_leverage"),
                    payload.get("exposure_pct_nav"),
                    payload.get("compliance"),
                    payload.get("exposure_pct_nav_final"),
                    to_jsonb(payload),
                    row.created_at,
                ),
            )
            return

        if snapshot.dataset == DatasetCode.LONG_SHORT_DELTA:
            underlying_asset = payload.get("underlying_asset") or row.row_key
            if not underlying_asset:
                raise DomainError("LONG_SHORT_DELTA rows require underlying_asset or row_key.")
            cursor.execute(
                """
                INSERT INTO long_short_delta (
                    id_long_short_delta_row,
                    id_org,
                    id_long_short_delta_snapshot,
                    id_f,
                    as_of_ts,
                    underlying_asset,
                    long_delta_pct,
                    average_strike_long,
                    average_maturities_long,
                    short_delta_pct,
                    average_strike_short,
                    average_maturities_short,
                    net_delta_pct,
                    raw_payload_json,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row.row_id,
                    row.id_org,
                    row.snapshot_id,
                    snapshot.id_f,
                    payload.get("as_of_ts") or snapshot.as_of_ts,
                    underlying_asset,
                    payload.get("long_delta_pct"),
                    payload.get("average_strike_long"),
                    payload.get("average_maturities_long"),
                    payload.get("short_delta_pct"),
                    payload.get("average_strike_short"),
                    payload.get("average_maturities_short"),
                    payload.get("net_delta_pct"),
                    to_jsonb(payload),
                    row.created_at,
                ),
            )
            return

        id_ctpy = payload.get("id_ctpy")
        if id_ctpy is None and row.row_key is not None:
            id_ctpy = _coerce_int(row.row_key, "id_ctpy")
        if id_ctpy is None:
            raise DomainError("COUNTERPARTY_CONCENTRATION rows require id_ctpy or row_key.")
        cursor.execute(
            """
            INSERT INTO counterparty_concentration (
                id_ctpy_concentration_row,
                id_org,
                id_ctpy_concentration_snapshot,
                id_f,
                id_ctpy,
                as_of_ts,
                mv_value,
                mv_nav_pct,
                compliance,
                raw_payload_json,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row.row_id,
                row.id_org,
                row.snapshot_id,
                snapshot.id_f,
                id_ctpy,
                payload.get("as_of_ts") or snapshot.as_of_ts,
                payload.get("mv_value"),
                payload.get("mv_nav_pct"),
                payload.get("compliance"),
                to_jsonb(payload),
                row.created_at,
            ),
        )


def _coerce_int(value: Any, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise DomainError(f"{field_name} must be an integer-compatible value.") from exc


def _as_of_date_expr(mapping: SnapshotSqlMapping) -> str:
    if mapping.as_of_date_col is not None:
        return mapping.as_of_date_col
    if mapping.as_of_ts_col is not None:
        return f"DATE({mapping.as_of_ts_col})"
    raise RuntimeError("Snapshot mapping must define either as_of_date_col or as_of_ts_col.")


def _official_filter_sql(dataset: DatasetCode, mapping: SnapshotSqlMapping) -> str:
    if dataset == DatasetCode.EXPIRIES:
        return "(COALESCE(is_latest_for_day, FALSE) OR status = 'official')"
    if mapping.is_official_col is None:
        return "FALSE"
    return f"COALESCE({mapping.is_official_col}, FALSE)"


def _row_key_from_db_row(dataset: DatasetCode, row: dict[str, Any]) -> str | None:
    if dataset == DatasetCode.AUM:
        return None
    if dataset == DatasetCode.SIMM:
        return row["counterparty_raw"]
    if dataset == DatasetCode.EXPIRIES:
        return row["row_hash"]
    if dataset == DatasetCode.NAV_ESTIMATED:
        return None
    if dataset == DatasetCode.LEVERAGES:
        return None
    if dataset == DatasetCode.LEVERAGES_PER_TRADE:
        trade_id = row.get("trade_id")
        return None if trade_id is None else str(trade_id)
    if dataset == DatasetCode.LEVERAGES_PER_UNDERLYING:
        return row.get("underlying_asset")
    if dataset == DatasetCode.LONG_SHORT_DELTA:
        return row.get("underlying_asset")
    id_ctpy = row.get("id_ctpy")
    return None if id_ctpy is None else str(id_ctpy)


def _payload_from_db_row(dataset: DatasetCode, row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row.get("raw_payload_json") or {})

    if dataset == DatasetCode.AUM:
        payload.update(_nonnull_fields(row, "aum_value", "id_ccy", "valuation_ts"))
        return payload
    if dataset == DatasetCode.SIMM:
        payload.update(
            _nonnull_fields(
                row,
                "id_ctpy",
                "counterparty_raw",
                "im_value",
                "mv_value",
                "mv_capped_value",
                "capped_type",
                "net_margin_value",
            )
        )
        return payload
    if dataset == DatasetCode.EXPIRIES:
        payload.update(
            _nonnull_fields(
                row,
                "trade_type",
                "underlying_asset",
                "termination_date",
                "buy_sell",
                "notional",
                "portfolio_name",
                "id_ac",
                "call_put",
                "strike",
                "trigger_value",
                "reference_spot",
                "id_ctpy",
                "mv_value",
                "total_premium_value",
                "strike_1",
                "strike_2",
                "trigger_2",
                "id_ccy",
                "days_remaining",
                "as_of_ts",
                "row_hash",
            )
        )
        return payload
    if dataset == DatasetCode.NAV_ESTIMATED:
        payload.update(_nonnull_fields(row, "nav_estimate", "nav_estimate_weighted_by_time", "comment", "as_of_ts"))
        return payload
    if dataset == DatasetCode.LEVERAGES:
        payload.update(_nonnull_fields(row, "as_of_ts", "gross_leverage", "commitment_leverage"))
        return payload
    if dataset == DatasetCode.LEVERAGES_PER_TRADE:
        payload.update(
            _nonnull_fields(
                row,
                "as_of_ts",
                "trade_id",
                "id_ac",
                "trade_type",
                "underlying_asset",
                "termination_date",
                "buy_sell",
                "notional",
                "call_put",
                "strike",
                "trigger_value",
                "reference_spot",
                "counterparty_raw",
                "id_ctpy",
                "gross_leverage",
                "exposure_pct_nav",
                "compliance",
            )
        )
        return payload
    if dataset == DatasetCode.LEVERAGES_PER_UNDERLYING:
        payload.update(
            _nonnull_fields(
                row,
                "as_of_ts",
                "id_ac",
                "underlying_asset",
                "gross_leverage",
                "exposure_pct_nav",
                "compliance",
                "exposure_pct_nav_final",
            )
        )
        return payload
    if dataset == DatasetCode.LONG_SHORT_DELTA:
        payload.update(
            _nonnull_fields(
                row,
                "as_of_ts",
                "underlying_asset",
                "long_delta_pct",
                "average_strike_long",
                "average_maturities_long",
                "short_delta_pct",
                "average_strike_short",
                "average_maturities_short",
                "net_delta_pct",
            )
        )
        return payload
    payload.update(_nonnull_fields(row, "id_ctpy", "as_of_ts", "mv_value", "mv_nav_pct", "compliance"))
    return payload


def _nonnull_fields(row: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {key: row[key] for key in keys if row.get(key) is not None}
