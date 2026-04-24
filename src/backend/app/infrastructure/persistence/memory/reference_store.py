from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import random

from app.domain.reference.entities import (
    AssetClassRecord,
    BookRecord,
    CounterpartyRecord,
    CurrencyRecord,
    FundRecord,
    TradeLabelRecord,
)
from app.domain.shared.entities import QuoteRecord


def _default_asset_classes() -> list[AssetClassRecord]:
    return [
        AssetClassRecord(1, "FX", "FX", "Foreign Exchange", "FX spot, forwards, swaps, options, and structured FX products.", 10, True),
        AssetClassRecord(2, "EQUITY", "EQ", "Equity", "Listed equities and equity-linked instruments.", 20, True),
        AssetClassRecord(3, "CASH", "Cash", "Cash", "Cash and cash equivalents including deposits and money market instruments.", 25, True),
        AssetClassRecord(4, "RATES", "IR", "Rates", "Interest-rate products including swaps, swaptions, and bonds.", 30, True),
        AssetClassRecord(5, "COMMODITY", "CD", "Commodity", "Commodity-linked derivatives and underlyings.", 40, True),
        AssetClassRecord(6, "HYBRID", "HB", "Hybrid", "Hybrid and cross-asset products combining multiple risk buckets.", 55, True),
        AssetClassRecord(7, "OTHER", None, "Other", "Temporary fallback for instruments not yet classified.", 999, True),
    ]


def _default_currencies() -> list[CurrencyRecord]:
    return [
        CurrencyRecord(1, "EUR", "Euro", "EUR", 978, 3, 10, True),
        CurrencyRecord(2, "USD", "US Dollar", "$", 840, 3, 20, True),
        CurrencyRecord(3, "GBP", "Pound Sterling", "GBP", 826, 3, 30, True),
        CurrencyRecord(4, "CHF", "Swiss Franc", "CHF", 756, 3, 40, True),
        CurrencyRecord(5, "JPY", "Japanese Yen", "JPY", 392, 3, 50, True),
    ]


def _default_quotes() -> list[QuoteRecord]:
    return [
        QuoteRecord(1, "finance", "Abraham Lincoln", "Discipline is choosing between what you want now and what you want most."),
        QuoteRecord(2, "finance", "Warren Buffett", "Risk comes from not knowing what you're doing."),
        QuoteRecord(3, "finance", "Warren Buffett", "The first rule is not to lose. The second rule is not to forget the first rule."),
        QuoteRecord(4, "finance", "Robert Arnott", "In investing, what is comfortable is rarely profitable."),
    ]


@dataclass(slots=True)
class InMemoryReferenceStore:
    asset_classes: list[AssetClassRecord] = field(default_factory=_default_asset_classes)
    currencies: list[CurrencyRecord] = field(default_factory=_default_currencies)
    quotes: list[QuoteRecord] = field(default_factory=_default_quotes)
    funds: list[FundRecord] = field(default_factory=list)
    books: list[BookRecord] = field(default_factory=list)
    trade_labels: list[TradeLabelRecord] = field(default_factory=list)
    counterparties: list[CounterpartyRecord] = field(default_factory=list)


class InMemoryReferenceUnitOfWork:
    def __init__(self, store: InMemoryReferenceStore):
        self._store = store
        self._working: InMemoryReferenceStore | None = None
        self._committed = False

    def __enter__(self) -> "InMemoryReferenceUnitOfWork":
        self._working = deepcopy(self._store)
        self._committed = False
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None or not self._committed:
            self.rollback()

    def commit(self) -> None:
        if self._working is None:
            return
        self._store.asset_classes = deepcopy(self._working.asset_classes)
        self._store.currencies = deepcopy(self._working.currencies)
        self._store.quotes = deepcopy(self._working.quotes)
        self._store.funds = deepcopy(self._working.funds)
        self._store.books = deepcopy(self._working.books)
        self._store.trade_labels = deepcopy(self._working.trade_labels)
        self._store.counterparties = deepcopy(self._working.counterparties)
        self._committed = True

    def rollback(self) -> None:
        self._working = None
        self._committed = False

    def list_asset_classes(self, *, include_inactive: bool) -> list[AssetClassRecord]:
        rows = self._state().asset_classes
        if include_inactive:
            return list(rows)
        return [row for row in rows if row.is_active]

    def list_currencies(self, *, include_inactive: bool) -> list[CurrencyRecord]:
        rows = self._state().currencies
        if include_inactive:
            return list(rows)
        return [row for row in rows if row.is_active]

    def list_funds(
        self,
        *,
        id_org: int,
        accessible_fund_ids: list[int] | None,
        include_inactive: bool,
    ) -> list[FundRecord]:
        rows = [row for row in self._state().funds if row.id_org == id_org]
        if accessible_fund_ids is not None:
            allowed = set(accessible_fund_ids)
            rows = [row for row in rows if row.id_f in allowed]
        if include_inactive:
            return rows
        return [row for row in rows if row.is_active]

    def list_books(
        self,
        *,
        id_org: int,
        id_f: int | None,
        accessible_fund_ids: list[int] | None,
        include_inactive: bool,
    ) -> list[BookRecord]:
        rows = [row for row in self._state().books if row.id_org == id_org and (id_f is None or row.id_f == id_f)]
        if accessible_fund_ids is not None:
            allowed = set(accessible_fund_ids)
            rows = [row for row in rows if row.id_f in allowed]
        if include_inactive:
            return rows
        return [row for row in rows if row.is_active]

    def list_trade_labels(self, *, id_org: int) -> list[TradeLabelRecord]:
        return [row for row in self._state().trade_labels if row.id_org == id_org]

    def list_counterparties(self, *, id_org: int, include_inactive: bool) -> list[CounterpartyRecord]:
        rows = [row for row in self._state().counterparties if row.id_org == id_org]
        if include_inactive:
            return rows
        return [row for row in rows if row.is_active]

    def get_random_quote(self) -> QuoteRecord | None:
        """Get a random active quote for the login page"""
        rows = [row for row in self._state().quotes if row.is_active]
        if not rows:
            return None
        return random.choice(rows)

    def _state(self) -> InMemoryReferenceStore:
        if self._working is None:
            raise RuntimeError("Unit of work not started.")
        return self._working
