from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Query, status

from app.api.dependencies import TradeServiceDep
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


@router.get("/types", response_model=List[TradeTypeResponse])
def list_trade_types (
        
        trade_service : TradeServiceDep,
        id_org : int = Query(..., gt=0)
    
    ) -> List[TradeTypeResponse] :
    """
    Endpoint to retrieve a list of available trade types for a given organization.
    """
    return [

        build_trade_type_response(item)
        for item in trade_service.list_trade_types(id_org=id_org)

    ]


@router.get("", response_model=List[TradeSummaryResponse])
def list_trades (
    
        trade_service : TradeServiceDep,
        id_org : int = Query(..., gt=0)
    
    ) -> List[TradeSummaryResponse] :
    """
    Endpoint to retrieve a list of trades for a given organization, with optional filtering by trade type.
    """
    return [

        build_trade_summary_response(item)
        for item in trade_service.list_trades(id_org=id_org)

    ]


@router.get("/disc/{id_spe}", response_model=DiscTradeAggregateResponse)
def get_disc_trade (

        id_spe : int,
        trade_service : TradeServiceDep,
        id_org : int = Query(..., gt=0),
    
    ) -> DiscTradeAggregateResponse:
    """
    Discovery endpoint to retrieve detailed information about a specific trade, including related entities and metadata.
    """
    aggregate = trade_service.get_disc_trade(id_org=id_org, id_spe=id_spe)
    
    return build_disc_trade_response(aggregate)


@router.post("/disc", response_model=DiscTradeAggregateResponse, status_code=status.HTTP_201_CREATED)
def create_disc_trade (
        
        payload: DiscTradeCreateRequest,
        trade_service: TradeServiceDep,
    
    ) -> DiscTradeAggregateResponse:
    """
    Endpoint to create a new trade based on the provided discovery payload, which includes all necessary information
    to construct the trade and its related entities.
    """
    aggregate = trade_service.create_disc_trade(payload)
    
    return build_disc_trade_response(aggregate)
