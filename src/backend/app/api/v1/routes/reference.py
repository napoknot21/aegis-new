from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Query, Request

from app.api.dependencies import (
    PrincipalDep,
    ReferenceServiceDep,
    assert_fund_access,
    get_accessible_fund_scope,
    resolve_id_org,
)
from app.domain.reference.schemas import (
    AssetClassResponse,
    BookResponse,
    CounterpartyResponse,
    CurrencyResponse,
    FundResponse,
    build_asset_class_response,
    build_book_response,
    build_counterparty_response,
    build_currency_response,
    build_fund_response,
)


router = APIRouter(tags=["reference"])

IdOrgQuery = Annotated[
    int | None,
    Query(description="Organisation identifier. If omitted and exactly one organisation is available, the backend infers it."),
]
FundQuery = Annotated[int | None, Query(gt=0, description="Optional fund filter.")]
IncludeInactiveQuery = Annotated[
    bool,
    Query(description="When true, includes inactive reference rows."),
]


@router.get("/asset-classes", response_model=List[AssetClassResponse])
def list_asset_classes(
    service: ReferenceServiceDep,
    include_inactive: IncludeInactiveQuery = False,
) -> List[AssetClassResponse]:
    return [
        build_asset_class_response(item)
        for item in service.list_asset_classes(include_inactive=include_inactive)
    ]


@router.get("/currencies", response_model=List[CurrencyResponse])
def list_currencies(
    service: ReferenceServiceDep,
    include_inactive: IncludeInactiveQuery = False,
) -> List[CurrencyResponse]:
    return [
        build_currency_response(item)
        for item in service.list_currencies(include_inactive=include_inactive)
    ]


@router.get("/funds", response_model=List[FundResponse])
def list_funds(
    request: Request,
    service: ReferenceServiceDep,
    principal: PrincipalDep,
    id_org: IdOrgQuery = None,
    include_inactive: IncludeInactiveQuery = False,
) -> List[FundResponse]:
    resolved_org_id = resolve_id_org(id_org=id_org, principal=principal, request=request)
    accessible_fund_ids = get_accessible_fund_scope(id_org=resolved_org_id, principal=principal, request=request)
    return [
        build_fund_response(item)
        for item in service.list_funds(
            id_org=resolved_org_id,
            accessible_fund_ids=accessible_fund_ids,
            include_inactive=include_inactive,
        )
    ]


@router.get("/books", response_model=List[BookResponse])
def list_books(
    request: Request,
    service: ReferenceServiceDep,
    principal: PrincipalDep,
    id_org: IdOrgQuery = None,
    id_f: FundQuery = None,
    include_inactive: IncludeInactiveQuery = False,
) -> List[BookResponse]:
    resolved_org_id = resolve_id_org(id_org=id_org, principal=principal, request=request)
    if id_f is not None:
        assert_fund_access(id_org=resolved_org_id, id_f=id_f, principal=principal, request=request)
    accessible_fund_ids = get_accessible_fund_scope(id_org=resolved_org_id, principal=principal, request=request)
    return [
        build_book_response(item)
        for item in service.list_books(
            id_org=resolved_org_id,
            id_f=id_f,
            accessible_fund_ids=accessible_fund_ids,
            include_inactive=include_inactive,
        )
    ]

@router.get("/counterparties", response_model=List[CounterpartyResponse])
def list_counterparties(
    request: Request,
    service: ReferenceServiceDep,
    principal: PrincipalDep,
    id_org: IdOrgQuery = None,
    include_inactive: IncludeInactiveQuery = False,
) -> List[CounterpartyResponse]:
    resolved_org_id = resolve_id_org(id_org=id_org, principal=principal, request=request)
    return [
        build_counterparty_response(item)
        for item in service.list_counterparties(id_org=resolved_org_id, include_inactive=include_inactive)
    ]
