from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.domain.data_snapshots.service import DataSnapshotApplicationService
from app.domain.reference.service import ReferenceApplicationService
from app.domain.trades.service import TradeApplicationService
from app.infrastructure.persistence.memory.data_snapshot_store import InMemoryDataSnapshotStore, InMemoryDataSnapshotUnitOfWork
from app.infrastructure.persistence.memory.reference_store import InMemoryReferenceStore, InMemoryReferenceUnitOfWork
from app.infrastructure.persistence.memory.trade_store import InMemoryTradeStore, InMemoryTradeUnitOfWork
from app.infrastructure.persistence.postgres import (
    PostgresDataSnapshotUnitOfWork,
    PostgresReferenceUnitOfWork,
    PostgresTradeUnitOfWork,
)


@dataclass(slots=True)
class Container:
    trade_service: TradeApplicationService
    data_snapshot_service: DataSnapshotApplicationService
    reference_service: ReferenceApplicationService


def build_container(settings: Settings | None = None) -> Container:
    settings = settings or get_settings()

    if settings.resolved_persistence_backend == "postgres":
        if not settings.database_url:
            raise RuntimeError("AEGIS_DATABASE_URL must be set when using the postgres backend.")

        trade_service = TradeApplicationService(
            uow_factory=lambda: PostgresTradeUnitOfWork(settings.database_url)
        )
        data_snapshot_service = DataSnapshotApplicationService(
            uow_factory=lambda: PostgresDataSnapshotUnitOfWork(settings.database_url)
        )
        reference_service = ReferenceApplicationService(
            uow_factory=lambda: PostgresReferenceUnitOfWork(settings.database_url)
        )
        return Container(
            trade_service=trade_service,
            data_snapshot_service=data_snapshot_service,
            reference_service=reference_service,
        )

    trade_store = InMemoryTradeStore()
    data_snapshot_store = InMemoryDataSnapshotStore()
    reference_store = InMemoryReferenceStore()

    trade_service = TradeApplicationService(
        uow_factory=lambda: InMemoryTradeUnitOfWork(trade_store)
    )
    data_snapshot_service = DataSnapshotApplicationService(
        uow_factory=lambda: InMemoryDataSnapshotUnitOfWork(data_snapshot_store)
    )
    reference_service = ReferenceApplicationService(
        uow_factory=lambda: InMemoryReferenceUnitOfWork(reference_store)
    )
    return Container(
        trade_service=trade_service,
        data_snapshot_service=data_snapshot_service,
        reference_service=reference_service,
    )
