from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Protocol

from app.domain.data_snapshots.entities import DataSnapshotAggregate, DataSnapshotRecord, DataSnapshotRowRecord, DatasetDefinition
from app.domain.data_snapshots.enums import DatasetCode, SnapshotStatus


class DataSnapshotUnitOfWork(Protocol):
    def __enter__(self) -> "DataSnapshotUnitOfWork": ...

    def __exit__(self, exc_type, exc, tb) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def list_dataset_definitions(self) -> list[DatasetDefinition]: ...

    def get_dataset_definition(self, dataset: DatasetCode) -> DatasetDefinition: ...

    def list_snapshots(
        self,
        dataset: DatasetCode,
        id_org: int,
        id_f: int | None = None,
        status: SnapshotStatus | None = None,
        is_official: bool | None = None,
        as_of_date: date | None = None,
        as_of_date_from: date | None = None,
        as_of_date_to: date | None = None,
    ) -> list[DataSnapshotRecord]: ...

    def get_snapshot(self, dataset: DatasetCode, id_org: int, snapshot_id: int) -> DataSnapshotAggregate | None: ...

    def next_snapshot_id(self, dataset: DatasetCode, id_org: int) -> int: ...

    def next_row_id(self, dataset: DatasetCode, id_org: int) -> int: ...

    def add_snapshot(self, snapshot: DataSnapshotRecord) -> None: ...

    def add_snapshot_row(self, row: DataSnapshotRowRecord) -> None: ...


DataSnapshotUnitOfWorkFactory = Callable[[], DataSnapshotUnitOfWork]
