from __future__ import annotations

"""
RemoteSubredRepository
----------------------
Fetches SubRed/AUM data from the external datacenter via LIBAPI (TradeManager).
Read-only source — save operations are intentional no-ops.

Migrated from: src/core/api/subred.py
"""

import sys
import datetime as dt
import polars as pl

from typing import Optional, Dict, Tuple, List

from src.repositories.base.subred import BaseSubredRepository
from src.config.tenant import TenantConfig
from src.config.schema import SUBRED_COLS_NEEDED, SUBRED_STRUCT_COLUMNS

from src.client.libapi import get_trade_manager # type:ignore

from src.utils.formatters import str_to_date, format_numeric_columns_to_string


class RemoteSubredRepository(BaseSubredRepository):
    """
    Live data from the external datacenter via LIBAPI TradeManager.
    This source is always available — it doesn't need a 'exists()' check.
    """

    def __init__(self, config: TenantConfig, loopback: int = 5):
        self._config = config
        self._loopback = loopback
        self._books_by_fund = {
            config.fund_hv: self._get_book_hv(),
            config.fund_wr: self._get_book_wr(),
        }

    def _get_book_hv(self):
        import os
        return os.getenv("SUBRED_BOOK_HV", "")

    def _get_book_wr(self):
        import os
        return os.getenv("SUBRED_BOOK_WR", "")

    # ------------------------------------------------------------------
    # Internal helpers (from src/core/api/subred.py)
    # ------------------------------------------------------------------

    def _api_call(self, date=None, books_by_fund=None, schema_overrides=None, loopback=None) -> Optional[pl.DataFrame]:
        loopback = self._loopback if loopback is None else loopback
        if loopback < 0:
            print("[-] RemoteSubredRepository: API call failed after retries.")
            return None

        schema_overrides = schema_overrides or SUBRED_COLS_NEEDED
        books_by_fund = books_by_fund or self._books_by_fund
        books = list(books_by_fund.values())

        trade_manager = get_trade_manager(self._config)
        if trade_manager is None:
            return None

        response = trade_manager.get_info_trades_from_books(books=books)
        if response is None:
            print("[!] RemoteSubredRepository: Empty response, retrying...")
            return self._api_call(date, books_by_fund, schema_overrides, loopback - 1)

        tradelegs: List[Dict] = response.get("tradeLegs", [])
        return pl.DataFrame(tradelegs, schema_overrides=schema_overrides).select(list(schema_overrides.keys()))

    def _clean(self, df: pl.DataFrame, books_by_fund=None, fmt="%Y-%m-%d") -> Optional[pl.DataFrame]:
        if df is None:
            return None

        books_by_fund = books_by_fund or self._books_by_fund

        df = df.filter(pl.col("tradeType") == "SUBRED")
        df = df.sort(pl.col("instrument").struct.field("deliveryDate").str.to_date(fmt))
        df = df.with_columns([
            pl.when(pl.col("tradeLegCode") == "RED")
              .then(-pl.col("instrument").struct.field("notional"))
              .otherwise(pl.col("instrument").struct.field("notional"))
              .alias("signed_notional")
        ])
        return df.group_by("bookName").agg([
            pl.col("signed_notional").sum().alias("total_signed_notional").cast(pl.Int128),
            pl.col("instrument").struct.field("currency").first().alias("currency"),
        ])

    def _to_fund_dict(self, df: pl.DataFrame, books_by_fund=None) -> Optional[Dict]:
        books_by_fund = books_by_fund or self._books_by_fund
        aum = {row["bookName"]: row for row in df.to_dicts()}
        result = {}
        for fund, book in books_by_fund.items():
            entry = aum.get(book)
            if entry:
                result[fund] = {
                    "amount": entry["total_signed_notional"],
                    "currency": entry["currency"],
                }
        return result

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------

    def fetch_aum(self, date=None, books_by_fund=None) -> Optional[Dict]:
        date = str_to_date(date)
        raw = self._api_call(date=date, books_by_fund=books_by_fund)
        if raw is None:
            return None
        cleaned = self._clean(raw, books_by_fund)
        cleaned = format_numeric_columns_to_string(cleaned)
        return self._to_fund_dict(cleaned, books_by_fund)

    def fetch_raw(self, date=None, books_by_fund=None, schema_overrides=None) -> Tuple[Optional[pl.DataFrame], Optional[str]]:
        date = str_to_date(date)
        raw = self._api_call(date=date, books_by_fund=books_by_fund, schema_overrides=schema_overrides)
        if raw is None:
            return None, None
        filtered = raw.filter(pl.col("tradeType") == "SUBRED")
        return filtered, None   # no md5 for live remote calls

    # Read-only — save ops are no-ops
    def save_aum(self, aum_dict, date=None) -> bool:
        return True

    def save_raw(self, dataframe, date=None) -> bool:
        return True

    def exists(self, date=None) -> bool:
        return True     # datacenter is always considered available; fetch handles failures