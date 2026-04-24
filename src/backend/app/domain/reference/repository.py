from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from app.domain.reference.entities import (
    AssetClassRecord,
    BookRecord,
    CounterpartyRecord,
    CurrencyRecord,
    FundRecord,
    TradeLabelRecord,
)


class ReferenceUnitOfWork(Protocol):
    def __enter__(self) -> "ReferenceUnitOfWork": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...

    def list_asset_classes(self, *, include_inactive: bool) -> list[AssetClassRecord]: ...
    def list_currencies(self, *, include_inactive: bool) -> list[CurrencyRecord]: ...
    def list_funds(
        self,
        *,
        id_org: int,
        accessible_fund_ids: list[int] | None,
        include_inactive: bool,
    ) -> list[FundRecord]: ...
    def list_books(
        self,
        *,
        id_org: int,
        id_f: int | None,
        accessible_fund_ids: list[int] | None,
        include_inactive: bool,
    ) -> list[BookRecord]: ...
    def list_trade_labels(self, *, id_org: int) -> list[TradeLabelRecord]: ...
    def list_counterparties(self, *, id_org: int, include_inactive: bool) -> list[CounterpartyRecord]: ...


ReferenceUnitOfWorkFactory = Callable[[], ReferenceUnitOfWork]
