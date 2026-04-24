from __future__ import annotations

from datetime import date, datetime, timezone

from app.domain.data_snapshots.entities import DataSnapshotRecord, DataSnapshotRowRecord
from app.domain.data_snapshots.enums import DatasetCode, SnapshotCadence, SnapshotShape, SnapshotStatus
from app.domain.data_snapshots.repository import DataSnapshotUnitOfWorkFactory
from app.domain.data_snapshots.schemas import DataSnapshotCreateRequest
from app.domain.shared.errors import ConflictError, NotFoundError


class DataSnapshotApplicationService:
    def __init__(self, uow_factory: DataSnapshotUnitOfWorkFactory):
        self._uow_factory = uow_factory

    def list_datasets(self):
        with self._uow_factory() as uow:
            return uow.list_dataset_definitions()

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
    ):
        with self._uow_factory() as uow:
            uow.get_dataset_definition(dataset)
            return uow.list_snapshots(
                dataset=dataset,
                id_org=id_org,
                accessible_fund_ids=accessible_fund_ids,
                id_f=id_f,
                status=status,
                is_official=is_official,
                as_of_date=as_of_date,
                as_of_date_from=as_of_date_from,
                as_of_date_to=as_of_date_to,
            )

    def get_snapshot(self, dataset: DatasetCode, id_org: int, snapshot_id: int):
        with self._uow_factory() as uow:
            aggregate = uow.get_snapshot(dataset=dataset, id_org=id_org, snapshot_id=snapshot_id)
            if aggregate is None:
                raise NotFoundError(
                    f"{dataset} snapshot {snapshot_id} was not found for organisation {id_org}."
                )
            return aggregate

    def create_snapshot(self, dataset: DatasetCode, payload: DataSnapshotCreateRequest):
        with self._uow_factory() as uow:
            definition = uow.get_dataset_definition(dataset)
            as_of_date, as_of_ts = self._normalize_temporal_fields(
                cadence=definition.cadence,
                as_of_date=payload.as_of_date,
                as_of_ts=payload.as_of_ts,
            )
            self._validate_rows(dataset=dataset, shape=definition.shape, rows=payload.rows)

            loaded_at = datetime.now(timezone.utc)
            snapshot_id = uow.next_snapshot_id(dataset=dataset, id_org=payload.id_org)
            snapshot = DataSnapshotRecord(
                snapshot_id=snapshot_id,
                dataset=dataset,
                id_org=payload.id_org,
                id_run=payload.id_run,
                id_f=payload.id_f,
                as_of_date=as_of_date,
                as_of_ts=as_of_ts,
                source_name=payload.source_name or definition.default_source_name,
                source_file_name=payload.source_file_name,
                source_generated_at=payload.source_generated_at,
                loaded_at=loaded_at,
                status=payload.status,
                row_count=len(payload.rows),
                is_official=payload.is_official,
                notes=payload.notes,
            )
            uow.add_snapshot(snapshot)

            for row_payload in payload.rows:
                uow.add_snapshot_row(
                    DataSnapshotRowRecord(
                        row_id=uow.next_row_id(dataset=dataset, id_org=payload.id_org),
                        dataset=dataset,
                        snapshot_id=snapshot_id,
                        id_org=payload.id_org,
                        id_f=payload.id_f,
                        row_key=row_payload.row_key,
                        payload_json=row_payload.payload_json,
                        created_at=loaded_at,
                    )
                )

            aggregate = uow.get_snapshot(dataset=dataset, id_org=payload.id_org, snapshot_id=snapshot_id)
            if aggregate is None:
                raise NotFoundError(
                    f"{dataset} snapshot {snapshot_id} could not be loaded after creation."
                )

            uow.commit()
            return aggregate

    @staticmethod
    def _normalize_temporal_fields(*, cadence: SnapshotCadence, as_of_date, as_of_ts):
        now = datetime.now(timezone.utc)

        if cadence == SnapshotCadence.DAILY:
            normalized_date = as_of_date or (as_of_ts.date() if as_of_ts else now.date())
            return normalized_date, as_of_ts

        normalized_ts = as_of_ts or now
        normalized_date = as_of_date or normalized_ts.date()
        return normalized_date, normalized_ts

    @staticmethod
    def _validate_rows(*, dataset: DatasetCode, shape: SnapshotShape, rows):
        if shape == SnapshotShape.SINGLE_ROW and len(rows) > 1:
            raise ConflictError(f"{dataset} accepts at most one row per snapshot.")

        seen_keys: set[str] = set()
        for row in rows:
            if row.row_key is None:
                continue
            if row.row_key in seen_keys:
                raise ConflictError(
                    f"Duplicate row_key '{row.row_key}' is not allowed inside one {dataset} snapshot."
                )
            seen_keys.add(row.row_key)
