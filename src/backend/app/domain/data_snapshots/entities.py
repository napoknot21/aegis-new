from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from app.domain.data_snapshots.enums import DatasetCode, SnapshotCadence, SnapshotShape, SnapshotStatus


@dataclass(slots=True, frozen=True)
class DatasetDefinition:
    code: DatasetCode
    name: str
    cadence: SnapshotCadence
    shape: SnapshotShape
    snapshot_table: str
    row_table: str
    default_source_name: str
    description: str


@dataclass(slots=True)
class DataSnapshotRecord:
    snapshot_id: int
    dataset: DatasetCode
    id_org: int
    id_run: int
    id_f: int
    as_of_date: date
    as_of_ts: datetime | None
    source_name: str
    source_file_name: str | None
    source_generated_at: datetime | None
    loaded_at: datetime
    status: SnapshotStatus
    row_count: int
    is_official: bool
    notes: str | None


@dataclass(slots=True)
class DataSnapshotRowRecord:
    row_id: int
    dataset: DatasetCode
    snapshot_id: int
    id_org: int
    id_f: int
    row_key: str | None
    payload_json: dict[str, Any]
    created_at: datetime


@dataclass(slots=True)
class DataSnapshotAggregate:
    definition: DatasetDefinition
    snapshot: DataSnapshotRecord
    rows: list[DataSnapshotRowRecord] = field(default_factory=list)

