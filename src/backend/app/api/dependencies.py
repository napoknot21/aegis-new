from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.bootstrap.container import Container
from app.domain.data_snapshots.service import DataSnapshotApplicationService
from app.domain.trades.service import TradeApplicationService


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_trade_service(container: ContainerDep) -> TradeApplicationService:
    return container.trade_service


TradeServiceDep = Annotated[TradeApplicationService, Depends(get_trade_service)]


def get_data_snapshot_service(container: ContainerDep) -> DataSnapshotApplicationService:
    return container.data_snapshot_service


DataSnapshotServiceDep = Annotated[
    DataSnapshotApplicationService,
    Depends(get_data_snapshot_service),
]

