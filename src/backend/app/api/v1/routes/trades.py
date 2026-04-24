from __future__ import annotations

from typing import List

from fastapi import APIRouter, Query, Request, status

from app.api.dependencies import (
    PrincipalDep,
    ReferenceServiceDep,
    TradeServiceDep,
    assert_fund_access,
    assert_org_access,
    get_accessible_fund_scope,
    resolve_id_org,
)
from app.domain.reference.schemas import TradeLabelResponse, build_trade_label_response
from app.domain.trades.schemas import (
    DiscTradeAggregateResponse,
    DiscTradeCreateRequest,
    TradeSummaryResponse,
    TradeTypeResponse,
    build_disc_trade_response,
    build_trade_summary_response,
    build_trade_type_response,
)


router = APIRouter(tags=["trades"])


@router.get("/labels", response_model=List[TradeLabelResponse])
def list_trade_labels(
    request: Request,
    reference_service: ReferenceServiceDep,
    principal: PrincipalDep,
    id_org: int | None = Query(default=None, gt=0),
) -> List[TradeLabelResponse]:
    resolved_org_id = resolve_id_org(id_org=id_org, principal=principal, request=request)
    return [
        build_trade_label_response(item)
        for item in reference_service.list_trade_labels(id_org=resolved_org_id)
    ]


@router.get("/types", response_model=List[TradeTypeResponse])
def list_trade_types(
    request: Request,
    trade_service: TradeServiceDep,
    principal: PrincipalDep,
    id_org: int | None = Query(default=None, gt=0),
) -> List[TradeTypeResponse]:
    """
    Endpoint to retrieve a list of available trade types for a given organization.
    """
    resolved_org_id = resolve_id_org(id_org=id_org, principal=principal, request=request)
    return [
        build_trade_type_response(item)
        for item in trade_service.list_trade_types(id_org=resolved_org_id)
    ]


@router.get("", response_model=List[TradeSummaryResponse])
def list_trades(
    request: Request,
    trade_service: TradeServiceDep,
    principal: PrincipalDep,
    id_org: int | None = Query(default=None, gt=0),
) -> List[TradeSummaryResponse]:
    """
    Endpoint to retrieve a list of trades for a given organization, with optional filtering by trade type.
    """
    resolved_org_id = resolve_id_org(id_org=id_org, principal=principal, request=request)
    accessible_fund_ids = get_accessible_fund_scope(id_org=resolved_org_id, principal=principal, request=request)
    return [
        build_trade_summary_response(item)
        for item in trade_service.list_trades(id_org=resolved_org_id, accessible_fund_ids=accessible_fund_ids)
    ]


@router.get("/disc/{id_spe}", response_model=DiscTradeAggregateResponse)
def get_disc_trade(
    id_spe: int,
    request: Request,
    trade_service: TradeServiceDep,
    principal: PrincipalDep,
    id_org: int | None = Query(default=None, gt=0),
) -> DiscTradeAggregateResponse:
    """
    Discovery endpoint to retrieve detailed information about a specific trade, including related entities and metadata.
    """
    resolved_org_id = resolve_id_org(id_org=id_org, principal=principal, request=request)
    aggregate = trade_service.get_disc_trade(id_org=resolved_org_id, id_spe=id_spe)
    assert_fund_access(id_org=resolved_org_id, id_f=aggregate.trade.id_f, principal=principal, request=request)
    return build_disc_trade_response(aggregate)


@router.post("/disc", response_model=DiscTradeAggregateResponse, status_code=status.HTTP_201_CREATED)
def create_disc_trade(
    request: Request,
    payload: DiscTradeCreateRequest,
    trade_service: TradeServiceDep,
    principal: PrincipalDep,
) -> DiscTradeAggregateResponse:
    """
    Endpoint to create a new trade based on the provided discovery payload, which includes all necessary information
    to construct the trade and its related entities.
    """
    assert_org_access(id_org=payload.id_org, principal=principal, request=request)
    assert_fund_access(id_org=payload.id_org, id_f=payload.id_f, principal=principal, request=request)
    if principal is not None:
        payload.booked_by = principal.user_id_for_org(payload.id_org)

    aggregate = trade_service.create_disc_trade(payload)
    return build_disc_trade_response(aggregate)
