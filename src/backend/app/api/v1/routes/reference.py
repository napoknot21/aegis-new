from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Query

from app.api.dependencies import ReferenceServiceDep
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

IdOrgQuery = Annotated[int, Query(..., gt=0, description="Organisation identifier.")]
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
    service: ReferenceServiceDep,
    id_org: IdOrgQuery,
    include_inactive: IncludeInactiveQuery = False,
) -> List[FundResponse]:
    return [
        build_fund_response(item)
        for item in service.list_funds(id_org=id_org, include_inactive=include_inactive)
    ]


@router.get("/books", response_model=List[BookResponse])
def list_books(
    service: ReferenceServiceDep,
    id_org: IdOrgQuery,
    id_f: FundQuery = None,
    include_inactive: IncludeInactiveQuery = False,
) -> List[BookResponse]:
    return [
        build_book_response(item)
        for item in service.list_books(id_org=id_org, id_f=id_f, include_inactive=include_inactive)
    ]

@router.get("/counterparties", response_model=List[CounterpartyResponse])
def list_counterparties(
    service: ReferenceServiceDep,
    id_org: IdOrgQuery,
    include_inactive: IncludeInactiveQuery = False,
) -> List[CounterpartyResponse]:
    return [
        build_counterparty_response(item)
        for item in service.list_counterparties(id_org=id_org, include_inactive=include_inactive)
    ]
