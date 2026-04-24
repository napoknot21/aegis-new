from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from app.domain.data_snapshots.catalog import get_dataset_catalog
from app.domain.data_snapshots.entities import DataSnapshotAggregate, DataSnapshotRecord, DataSnapshotRowRecord, DatasetDefinition
from app.domain.data_snapshots.enums import DatasetCode, SnapshotStatus
from app.domain.shared.errors import NotFoundError


@dataclass(slots=True)
class InMemoryDataSnapshotStore:
    definitions: dict[DatasetCode, DatasetDefinition] = field(default_factory=get_dataset_catalog)
    snapshot_sequences: dict[tuple[DatasetCode, int], int] = field(default_factory=dict)
    row_sequences: dict[tuple[DatasetCode, int], int] = field(default_factory=dict)
    snapshots: dict[tuple[DatasetCode, int, int], DataSnapshotRecord] = field(default_factory=dict)
    rows_by_snapshot: dict[tuple[DatasetCode, int, int], list[DataSnapshotRowRecord]] = field(default_factory=dict)


class InMemoryDataSnapshotUnitOfWork:
    def __init__(self, store: InMemoryDataSnapshotStore):
        self._store = store
        self._working_store: InMemoryDataSnapshotStore | None = None

    def __enter__(self) -> "InMemoryDataSnapshotUnitOfWork":
        self._working_store = deepcopy(self._store)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        if self._working_store is None:
            raise RuntimeError("Unit of work not started.")
        self._store.definitions = self._working_store.definitions
        self._store.snapshot_sequences = self._working_store.snapshot_sequences
        self._store.row_sequences = self._working_store.row_sequences
        self._store.snapshots = self._working_store.snapshots
        self._store.rows_by_snapshot = self._working_store.rows_by_snapshot
        self._working_store = None

    def rollback(self) -> None:
        self._working_store = None

    def list_dataset_definitions(self) -> list[DatasetDefinition]:
        return list(self._state().definitions.values())

    def get_dataset_definition(self, dataset: DatasetCode) -> DatasetDefinition:
        definition = self._state().definitions.get(dataset)
        if definition is None:
            raise NotFoundError(f"Dataset {dataset} is not registered.")
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
        items = [
            snapshot
            for snapshot in self._state().snapshots.values()
            if snapshot.dataset == dataset and snapshot.id_org == id_org and (id_f is None or snapshot.id_f == id_f)
        ]
        if accessible_fund_ids is not None:
            allowed = set(accessible_fund_ids)
            items = [snapshot for snapshot in items if snapshot.id_f in allowed]
        if status is not None:
            items = [snapshot for snapshot in items if snapshot.status == status]
        if is_official is not None:
            items = [snapshot for snapshot in items if snapshot.is_official == is_official]
        if as_of_date is not None:
            items = [snapshot for snapshot in items if snapshot.as_of_date == as_of_date]
        if as_of_date_from is not None:
            items = [snapshot for snapshot in items if snapshot.as_of_date >= as_of_date_from]
        if as_of_date_to is not None:
            items = [snapshot for snapshot in items if snapshot.as_of_date <= as_of_date_to]
        epoch = datetime.min.replace(tzinfo=timezone.utc)
        return sorted(
            items,
            key=lambda item: (item.as_of_ts or epoch, item.as_of_date, item.snapshot_id),
            reverse=True,
        )

    def get_snapshot(self, dataset: DatasetCode, id_org: int, snapshot_id: int) -> DataSnapshotAggregate | None:
        key = (dataset, id_org, snapshot_id)
        snapshot = self._state().snapshots.get(key)
        if snapshot is None:
            return None
        rows = list(self._state().rows_by_snapshot.get(key, []))
        definition = self.get_dataset_definition(dataset)
        return DataSnapshotAggregate(definition=definition, snapshot=snapshot, rows=rows)

    def next_snapshot_id(self, dataset: DatasetCode, id_org: int) -> int:
        key = (dataset, id_org)
        state = self._state()
        current = state.snapshot_sequences.get(key, 0) + 1
        state.snapshot_sequences[key] = current
        return current

    def next_row_id(self, dataset: DatasetCode, id_org: int) -> int:
        key = (dataset, id_org)
        state = self._state()
        current = state.row_sequences.get(key, 0) + 1
        state.row_sequences[key] = current
        return current

    def add_snapshot(self, snapshot: DataSnapshotRecord) -> None:
        key = (snapshot.dataset, snapshot.id_org, snapshot.snapshot_id)
        self._state().snapshots[key] = snapshot

    def add_snapshot_row(self, row: DataSnapshotRowRecord) -> None:
        key = (row.dataset, row.id_org, row.snapshot_id)
        rows = self._state().rows_by_snapshot.setdefault(key, [])
        rows.append(row)

    def _state(self) -> InMemoryDataSnapshotStore:
        if self._working_store is None:
            raise RuntimeError("Unit of work not started.")
        return self._working_store
