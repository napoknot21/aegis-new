from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.data_snapshots.entities import DataSnapshotAggregate, DataSnapshotRecord, DataSnapshotRowRecord, DatasetDefinition
from app.domain.data_snapshots.enums import DatasetCode, SnapshotCadence, SnapshotShape, SnapshotStatus


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DataSnapshotRowCreate(StrictModel):
    row_key: str | None = None
    payload_json: dict[str, Any] = Field(default_factory=dict)


class DataSnapshotCreateRequest(StrictModel):
    id_org: int
    id_run: int
    id_f: int
    as_of_date: date | None = None
    as_of_ts: datetime | None = None
    source_name: str | None = None
    source_file_name: str | None = None
    source_generated_at: datetime | None = None
    status: SnapshotStatus = SnapshotStatus.LOADED
    is_official: bool = False
    notes: str | None = None
    rows: list[DataSnapshotRowCreate] = Field(default_factory=list)


class DatasetDefinitionResponse(BaseModel):
    code: DatasetCode
    name: str
    cadence: SnapshotCadence
    shape: SnapshotShape
    snapshot_table: str
    row_table: str
    default_source_name: str
    description: str


class DataSnapshotRowResponse(BaseModel):
    row_id: int
    dataset: DatasetCode
    snapshot_id: int
    id_org: int
    id_f: int
    row_key: str | None
    payload_json: dict[str, Any]
    created_at: datetime


class DataSnapshotSummaryResponse(BaseModel):
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


class DataSnapshotAggregateResponse(BaseModel):
    definition: DatasetDefinitionResponse
    snapshot: DataSnapshotSummaryResponse
    rows: list[DataSnapshotRowResponse]


def build_dataset_definition_response(record: DatasetDefinition) -> DatasetDefinitionResponse:
    return DatasetDefinitionResponse(**asdict(record))


def build_data_snapshot_summary_response(record: DataSnapshotRecord) -> DataSnapshotSummaryResponse:
    return DataSnapshotSummaryResponse(**asdict(record))


def build_data_snapshot_row_response(record: DataSnapshotRowRecord) -> DataSnapshotRowResponse:
    return DataSnapshotRowResponse(**asdict(record))


def build_data_snapshot_aggregate_response(record: DataSnapshotAggregate) -> DataSnapshotAggregateResponse:
    return DataSnapshotAggregateResponse(
        definition=build_dataset_definition_response(record.definition),
        snapshot=build_data_snapshot_summary_response(record.snapshot),
        rows=[build_data_snapshot_row_response(item) for item in record.rows],
    )

