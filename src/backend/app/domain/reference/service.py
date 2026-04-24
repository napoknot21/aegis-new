from __future__ import annotations

from app.domain.reference.repository import ReferenceUnitOfWorkFactory


class ReferenceApplicationService:
    def __init__(self, uow_factory: ReferenceUnitOfWorkFactory):
        self._uow_factory = uow_factory

    def list_asset_classes(self, *, include_inactive: bool):
        with self._uow_factory() as uow:
            return uow.list_asset_classes(include_inactive=include_inactive)

    def list_currencies(self, *, include_inactive: bool):
        with self._uow_factory() as uow:
            return uow.list_currencies(include_inactive=include_inactive)

    def list_funds(self, *, id_org: int, accessible_fund_ids: list[int] | None, include_inactive: bool):
        with self._uow_factory() as uow:
            return uow.list_funds(
                id_org=id_org,
                accessible_fund_ids=accessible_fund_ids,
                include_inactive=include_inactive,
            )

    def list_books(
        self,
        *,
        id_org: int,
        id_f: int | None,
        accessible_fund_ids: list[int] | None,
        include_inactive: bool,
    ):
        with self._uow_factory() as uow:
            return uow.list_books(
                id_org=id_org,
                id_f=id_f,
                accessible_fund_ids=accessible_fund_ids,
                include_inactive=include_inactive,
            )

    def list_trade_labels(self, *, id_org: int):
        with self._uow_factory() as uow:
            return uow.list_trade_labels(id_org=id_org)

    def list_counterparties(self, *, id_org: int, include_inactive: bool):
        with self._uow_factory() as uow:
            return uow.list_counterparties(id_org=id_org, include_inactive=include_inactive)
