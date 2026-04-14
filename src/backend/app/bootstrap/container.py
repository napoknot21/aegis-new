from __future__ import annotations

from dataclasses import dataclass

from app.domain.data_snapshots.service import DataSnapshotApplicationService
from app.domain.trades.service import TradeApplicationService
from app.infrastructure.persistence.memory.data_snapshot_store import InMemoryDataSnapshotStore, InMemoryDataSnapshotUnitOfWork
from app.infrastructure.persistence.memory.trade_store import InMemoryTradeStore, InMemoryTradeUnitOfWork


@dataclass(slots=True)
class Container:
    trade_service: TradeApplicationService
    data_snapshot_service: DataSnapshotApplicationService


def build_container() -> Container:
    trade_store = InMemoryTradeStore()
    data_snapshot_store = InMemoryDataSnapshotStore()

    trade_service = TradeApplicationService(
        uow_factory=lambda: InMemoryTradeUnitOfWork(trade_store)
    )
    data_snapshot_service = DataSnapshotApplicationService(
        uow_factory=lambda: InMemoryDataSnapshotUnitOfWork(data_snapshot_store)
    )
    return Container(
        trade_service=trade_service,
        data_snapshot_service=data_snapshot_service,
    )

