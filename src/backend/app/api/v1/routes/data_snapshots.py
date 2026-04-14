from __future__ import annotations

from datetime import date
from typing import Annotated, List

from fastapi import APIRouter, Query, status

from app.api.dependencies import DataSnapshotServiceDep
from app.domain.data_snapshots.enums import DatasetCode, SnapshotStatus
from app.domain.data_snapshots.schemas import (
    DataSnapshotAggregateResponse,
    DataSnapshotCreateRequest,
    DataSnapshotSummaryResponse,
    DatasetDefinitionResponse,
    build_data_snapshot_aggregate_response,
    build_data_snapshot_summary_response,
    build_dataset_definition_response,
)


router = APIRouter(tags=["data snapshots"])

IdOrgQuery = Annotated[int, Query(description="Organisation identifier.")]
FundQuery = Annotated[int | None, Query(description="Optional fund filter.")]
StatusQuery = Annotated[SnapshotStatus | None, Query(description="Optional snapshot status filter.")]
OfficialQuery = Annotated[bool | None, Query(description="Optional official/latest filter.")]
AsOfDateQuery = Annotated[date | None, Query(description="Optional exact as-of date filter.")]
AsOfDateFromQuery = Annotated[date | None, Query(description="Optional lower bound for as-of date.")]
AsOfDateToQuery = Annotated[date | None, Query(description="Optional upper bound for as-of date.")]


@router.get("/datasets", response_model=List[DatasetDefinitionResponse])
def list_dataset_definitions (service : DataSnapshotServiceDep) -> List[DatasetDefinitionResponse] :
    """
    Endpoint to list all available dataset definitions.
    """
    return [build_dataset_definition_response(item) for item in service.list_datasets()]


@router.get("/{dataset}/snapshots", response_model=List[DataSnapshotSummaryResponse])
def list_dataset_snapshots (

        dataset : DatasetCode,
        id_org : IdOrgQuery,
        service : DataSnapshotServiceDep,
        id_f : FundQuery = None,
        status : StatusQuery = None,
        is_official : OfficialQuery = None,
        as_of_date : AsOfDateQuery = None,
        as_of_date_from : AsOfDateFromQuery = None,
        as_of_date_to : AsOfDateToQuery = None,
    
    ) -> List[DataSnapshotSummaryResponse] :
    """
    Endpoint to list data snapshots for a dataset and organisation, with optional filtering by fund,
    status, official/latest flag, and as-of date range.
    """
    snapshots = service.list_snapshots(
        dataset=dataset,
        id_org=id_org,
        id_f=id_f,
        status=status,
        is_official=is_official,
        as_of_date=as_of_date,
        as_of_date_from=as_of_date_from,
        as_of_date_to=as_of_date_to,
    )

    return [build_data_snapshot_summary_response(item) for item in snapshots]


@router.get("/{dataset}/snapshots/{snapshot_id}", response_model=DataSnapshotAggregateResponse)
def get_dataset_snapshot (
        
        dataset: DatasetCode,
        snapshot_id: int,
        id_org: IdOrgQuery,
        service: DataSnapshotServiceDep,
    
    ) -> DataSnapshotAggregateResponse :
    """
    Endpoint to retrieve a specific data snapshot by its identifier, including all associated data and metadata.
    """
    return build_data_snapshot_aggregate_response(
        service.get_snapshot(dataset=dataset, id_org=id_org, snapshot_id=snapshot_id)
    )


@router.post("/{dataset}/snapshots", response_model=DataSnapshotAggregateResponse, status_code=status.HTTP_201_CREATED)
def create_dataset_snapshot (
        
        dataset : DatasetCode,
        payload : DataSnapshotCreateRequest,
        service : DataSnapshotServiceDep,
    
    ) -> DataSnapshotAggregateResponse :
    """
    
    """
    aggregate = service.create_snapshot(dataset=dataset, payload=payload)
    
    return build_data_snapshot_aggregate_response(aggregate)
