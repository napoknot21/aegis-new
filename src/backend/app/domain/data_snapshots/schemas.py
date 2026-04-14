from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field

from app.domain.data_snapshots.entities import DataSnapshotAggregate, DataSnapshotRecord, DataSnapshotRowRecord, DatasetDefinition
from app.domain.data_snapshots.enums import DatasetCode, SnapshotCadence, SnapshotShape, SnapshotStatus


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DataSnapshotRowCreate (StrictModel) :
    """
    Request model for creating a new data snapshot row, including the row key and payload.
    """
    row_key : str | None = None
    payload_json : dict[str, Any] = Field(default_factory=dict)


class DataSnapshotCreateRequest(StrictModel) :
    """
    Request model for creating a new data snapshot, including metadata and rows.
    """
    id_org : int
    id_run : int
    id_f : int
    as_of_date : date | None = None
    as_of_ts : datetime | None = None
    source_name : str | None = None
    source_file_name : str | None = None
    source_generated_at : datetime | None = None
    status : SnapshotStatus = SnapshotStatus.LOADED
    is_official : bool = False
    notes : str | None = None
    rows : List[DataSnapshotRowCreate] = Field(default_factory=list)


class DatasetDefinitionResponse (BaseModel) :
    """
    Response model for dataset definitions, including metadata about the dataset structure and source.
    """
    code : DatasetCode
    name : str
    cadence : SnapshotCadence
    shape : SnapshotShape
    snapshot_table : str
    row_table : str
    default_source_name : str
    description : str


class DataSnapshotRowResponse (BaseModel) :
    """
    Response model for a single row within a data snapshot, including the payload and metadata.
    """
    row_id : int
    dataset : DatasetCode
    snapshot_id : int
    id_org : int
    id_f : int
    row_key : str | None
    payload_json : dict[str, Any]
    created_at : datetime


class DataSnapshotSummaryResponse (BaseModel) :
    """
    Response model for a summary of a data snapshot, including metadata and row count.
    """
    snapshot_id : int
    dataset : DatasetCode
    id_org : int
    id_run : int
    id_f : int
    as_of_date : date
    as_of_ts : datetime | None
    source_name : str
    source_file_name : str | None
    source_generated_at : datetime | None
    loaded_at : datetime
    status : SnapshotStatus
    row_count : int
    is_official : bool
    notes : str | None


class DataSnapshotAggregateResponse (BaseModel) :
    """
    Response model for a complete data snapshot aggregate, including the dataset definition, 
    snapshot summary, and all associated rows.
    """
    definition : DatasetDefinitionResponse
    snapshot : DataSnapshotSummaryResponse
    rows : list[DataSnapshotRowResponse]


def build_dataset_definition_response (record: DatasetDefinition) -> DatasetDefinitionResponse :
    """
    Helper function to convert a DatasetDefinition entity into a DatasetDefinitionResponse model.
    """
    return DatasetDefinitionResponse(**asdict(record))


def build_data_snapshot_summary_response (record: DataSnapshotRecord) -> DataSnapshotSummaryResponse :
    """
    Helper function to convert a DataSnapshotRecord entity into a DataSnapshotSummaryResponse model.
    """
    return DataSnapshotSummaryResponse(**asdict(record))


def build_data_snapshot_row_response (record: DataSnapshotRowRecord) -> DataSnapshotRowResponse :
    """
    Helper function to convert a DataSnapshotRowRecord entity into a DataSnapshotRowResponse model.
    """
    return DataSnapshotRowResponse(**asdict(record))


def build_data_snapshot_aggregate_response (record: DataSnapshotAggregate) -> DataSnapshotAggregateResponse :
    """
    Helper function to convert a DataSnapshotAggregate entity into a DataSnapshotAggregateResponse model.
    """
    return DataSnapshotAggregateResponse(

        definition=build_dataset_definition_response(record.definition),
        snapshot=build_data_snapshot_summary_response(record.snapshot),
        rows=[build_data_snapshot_row_response(item) for item in record.rows],
    
    )

