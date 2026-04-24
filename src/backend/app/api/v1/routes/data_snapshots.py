from __future__ import annotations

from datetime import date
from typing import Annotated, List

from fastapi import APIRouter, Query, Request, status

from app.api.dependencies import (
    DataSnapshotServiceDep,
    PrincipalDep,
    assert_fund_access,
    assert_org_access,
    get_accessible_fund_scope,
    resolve_id_org,
)
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

IdOrgQuery = Annotated[
    int | None,
    Query(description="Organisation identifier. If omitted and exactly one organisation is available, the backend infers it."),
]
FundQuery = Annotated[int | None, Query(description="Optional fund filter.")]
StatusQuery = Annotated[SnapshotStatus | None, Query(description="Optional snapshot status filter.")]
OfficialQuery = Annotated[bool | None, Query(description="Optional official/latest filter.")]
AsOfDateQuery = Annotated[date | None, Query(description="Optional exact as-of date filter.")]
AsOfDateFromQuery = Annotated[date | None, Query(description="Optional lower bound for as-of date.")]
AsOfDateToQuery = Annotated[date | None, Query(description="Optional upper bound for as-of date.")]


@router.get("/datasets", response_model=List[DatasetDefinitionResponse])
def list_dataset_definitions(service: DataSnapshotServiceDep) -> List[DatasetDefinitionResponse]:
    """
    Endpoint to list all available dataset definitions.
    """
    return [build_dataset_definition_response(item) for item in service.list_datasets()]


@router.get("/{dataset}/snapshots", response_model=List[DataSnapshotSummaryResponse])
def list_dataset_snapshots(
    request: Request,
    dataset: DatasetCode,
    service: DataSnapshotServiceDep,
    principal: PrincipalDep,
    id_org: IdOrgQuery = None,
    id_f: FundQuery = None,
    status: StatusQuery = None,
    is_official: OfficialQuery = None,
    as_of_date: AsOfDateQuery = None,
    as_of_date_from: AsOfDateFromQuery = None,
    as_of_date_to: AsOfDateToQuery = None,
) -> List[DataSnapshotSummaryResponse]:
    """
    Endpoint to list data snapshots for a dataset and organisation, with optional filtering by fund,
    status, official/latest flag, and as-of date range.
    """
    resolved_org_id = resolve_id_org(id_org=id_org, principal=principal, request=request)
    if id_f is not None:
        assert_fund_access(id_org=resolved_org_id, id_f=id_f, principal=principal, request=request)
    accessible_fund_ids = get_accessible_fund_scope(id_org=resolved_org_id, principal=principal, request=request)

    snapshots = service.list_snapshots(
        dataset=dataset,
        id_org=resolved_org_id,
        accessible_fund_ids=accessible_fund_ids,
        id_f=id_f,
        status=status,
        is_official=is_official,
        as_of_date=as_of_date,
        as_of_date_from=as_of_date_from,
        as_of_date_to=as_of_date_to,
    )

    return [build_data_snapshot_summary_response(item) for item in snapshots]


@router.get("/{dataset}/snapshots/{snapshot_id}", response_model=DataSnapshotAggregateResponse)
def get_dataset_snapshot(
    request: Request,
    dataset: DatasetCode,
    snapshot_id: int,
    service: DataSnapshotServiceDep,
    principal: PrincipalDep,
    id_org: IdOrgQuery = None,
) -> DataSnapshotAggregateResponse:
    """
    Endpoint to retrieve a specific data snapshot by its identifier, including all associated data and metadata.
    """
    resolved_org_id = resolve_id_org(id_org=id_org, principal=principal, request=request)
    aggregate = service.get_snapshot(dataset=dataset, id_org=resolved_org_id, snapshot_id=snapshot_id)
    assert_fund_access(
        id_org=resolved_org_id,
        id_f=aggregate.snapshot.id_f,
        principal=principal,
        request=request,
    )
    return build_data_snapshot_aggregate_response(aggregate)


@router.post("/{dataset}/snapshots", response_model=DataSnapshotAggregateResponse, status_code=status.HTTP_201_CREATED)
def create_dataset_snapshot(
    request: Request,
    dataset: DatasetCode,
    payload: DataSnapshotCreateRequest,
    service: DataSnapshotServiceDep,
    principal: PrincipalDep,
) -> DataSnapshotAggregateResponse:
    assert_org_access(id_org=payload.id_org, principal=principal, request=request)
    assert_fund_access(id_org=payload.id_org, id_f=payload.id_f, principal=principal, request=request)
    aggregate = service.create_snapshot(dataset=dataset, payload=payload)
    return build_data_snapshot_aggregate_response(aggregate)
