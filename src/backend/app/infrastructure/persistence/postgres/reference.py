from __future__ import annotations

from typing import Any

from app.domain.reference.entities import (
    AssetClassRecord,
    BookRecord,
    CounterpartyRecord,
    CurrencyRecord,
    FundRecord,
    TradeLabelRecord,
)

from .base import PostgresUnitOfWorkBase


class PostgresReferenceUnitOfWork(PostgresUnitOfWorkBase):
    def list_asset_classes(self, *, include_inactive: bool) -> list[AssetClassRecord]:
        query = """
            SELECT id_ac, code, ice_code, name, description, sort_order, is_active
            FROM asset_classes
        """
        params: list[Any] = []
        if not include_inactive:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY sort_order, id_ac"
        return [_build_asset_class_record(row) for row in self._fetch_all(query, params)]

    def list_currencies(self, *, include_inactive: bool) -> list[CurrencyRecord]:
        query = """
            SELECT id_ccy, code, name, symbol, iso_numeric, decimals, sort_order, is_active
            FROM currencies
        """
        params: list[Any] = []
        if not include_inactive:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY sort_order, id_ccy"
        return [_build_currency_record(row) for row in self._fetch_all(query, params)]

    def list_funds(self, *, id_org: int, include_inactive: bool) -> list[FundRecord]:
        query = """
            SELECT id_f, id_org, id_ccy, name, code, fund_type, inception_date, is_active
            FROM funds
            WHERE id_org = %s
        """
        params: list[Any] = [id_org]
        if not include_inactive:
            query += " AND is_active = TRUE"
        query += " ORDER BY name, id_f"
        return [_build_fund_record(row) for row in self._fetch_all(query, params)]

    def list_books(self, *, id_org: int, id_f: int | None, include_inactive: bool) -> list[BookRecord]:
        query = """
            SELECT id_book, id_org, id_f, name, parent_id, is_active
            FROM books
            WHERE id_org = %s
        """
        params: list[Any] = [id_org]
        if id_f is not None:
            query += " AND id_f = %s"
            params.append(id_f)
        if not include_inactive:
            query += " AND is_active = TRUE"
        query += " ORDER BY name, id_book"
        return [_build_book_record(row) for row in self._fetch_all(query, params)]

    def list_trade_labels(self, *, id_org: int) -> list[TradeLabelRecord]:
        rows = self._fetch_all(
            """
            SELECT id_label, id_org, code
            FROM trade_disc_labels
            WHERE id_org = %s
            ORDER BY code, id_label
            """,
            [id_org],
        )
        return [_build_trade_label_record(row) for row in rows]

    def list_counterparties(self, *, id_org: int, include_inactive: bool) -> list[CounterpartyRecord]:
        query = """
            SELECT id_ctpy, id_org, id_bank, ice_name, ext_code, is_active
            FROM counterparties
            WHERE id_org = %s
        """
        params: list[Any] = [id_org]
        if not include_inactive:
            query += " AND is_active = TRUE"
        query += " ORDER BY COALESCE(ice_name, ext_code), id_ctpy"
        return [_build_counterparty_record(row) for row in self._fetch_all(query, params)]

    def _fetch_all(self, query: str, params: list[Any]) -> list[dict[str, Any]]:
        connection = self._connection_or_raise()
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def _build_asset_class_record(row: dict[str, Any]) -> AssetClassRecord:
    return AssetClassRecord(
        id_ac=int(row["id_ac"]),
        code=row["code"],
        ice_code=row["ice_code"],
        name=row["name"],
        description=row["description"],
        sort_order=int(row["sort_order"]),
        is_active=bool(row["is_active"]),
    )


def _build_currency_record(row: dict[str, Any]) -> CurrencyRecord:
    return CurrencyRecord(
        id_ccy=int(row["id_ccy"]),
        code=row["code"],
        name=row["name"],
        symbol=row["symbol"],
        iso_numeric=row["iso_numeric"],
        decimals=int(row["decimals"]),
        sort_order=int(row["sort_order"]),
        is_active=bool(row["is_active"]),
    )


def _build_fund_record(row: dict[str, Any]) -> FundRecord:
    return FundRecord(
        id_f=int(row["id_f"]),
        id_org=int(row["id_org"]),
        id_ccy=int(row["id_ccy"]),
        name=row["name"],
        code=row["code"],
        fund_type=row["fund_type"],
        inception_date=row["inception_date"],
        is_active=bool(row["is_active"]),
    )


def _build_book_record(row: dict[str, Any]) -> BookRecord:
    return BookRecord(
        id_book=int(row["id_book"]),
        id_org=int(row["id_org"]),
        id_f=int(row["id_f"]),
        name=row["name"],
        parent_id=row["parent_id"],
        is_active=bool(row["is_active"]),
    )


def _build_trade_label_record(row: dict[str, Any]) -> TradeLabelRecord:
    return TradeLabelRecord(
        id_label=int(row["id_label"]),
        id_org=int(row["id_org"]),
        code=row["code"],
    )


def _build_counterparty_record(row: dict[str, Any]) -> CounterpartyRecord:
    ice_name = row["ice_name"]
    ext_code = row["ext_code"]
    display_name = ice_name or ext_code or f"Counterparty {row['id_ctpy']}"
    return CounterpartyRecord(
        id_ctpy=int(row["id_ctpy"]),
        id_org=int(row["id_org"]),
        id_bank=row["id_bank"],
        ice_name=ice_name,
        ext_code=ext_code,
        is_active=bool(row["is_active"]),
        display_name=display_name,
    )
