from __future__ import annotations

"""
LocalSubredRepository
---------------------
Reads and writes SubRed/AUM data from local file cache.
  - Aggregated AUM  → {date}_aum.json
  - Raw trade legs  → {date}_aum_raw.xlsx

Migrated from: src/core/data/subred.py
"""

import os
import re
import json
import datetime as dt
import polars as pl

from typing import Optional, Dict, Tuple

from src.repositories.base.subred import BaseSubredRepository
from src.config.tenant import TenantConfig
from src.config.schema import SUBRED_COLUMNS_READ, SUBRED_STRUCT_COLUMNS
from src.utils.formatters import date_to_str
from src.utils.data_io import export_dataframe_to_excel, load_excel_to_dataframe

# Filename patterns — kept in schema or passed via config
_AUM_FILENAME_REGEX     = re.compile(r"^(\d{4}-\d{2}-\d{2})_aum\.json$", re.IGNORECASE)
_AUM_RAW_FILENAME_REGEX = re.compile(r"^(\d{4}-\d{2}-\d{2})_aum_raw\.xlsx$", re.IGNORECASE)


class LocalSubredRepository(BaseSubredRepository):
    """
    File-based cache for SubRed AUM data.
    The cache_dir comes from TenantConfig — different per tenant.
    """

    def __init__(self, config: TenantConfig):
        self._cache_dir = config.subred_cache_dir
        self._books_by_fund = {
            config.fund_hv: os.getenv("SUBRED_BOOK_HV", ""),
            config.fund_wr: os.getenv("SUBRED_BOOK_WR", ""),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _scan(self, date_str: str, regex: re.Pattern) -> Optional[str]:
        os.makedirs(self._cache_dir, exist_ok=True)
        with os.scandir(self._cache_dir) as it:
            for entry in it:
                if not entry.is_file():
                    continue
                m = regex.match(entry.name)
                if m and m.groups()[0] == date_str:
                    return entry.name
        return None

    def _aum_file(self, date_str: str) -> Optional[str]:
        return self._scan(date_str, _AUM_FILENAME_REGEX)

    def _raw_file(self, date_str: str) -> Optional[str]:
        return self._scan(date_str, _AUM_RAW_FILENAME_REGEX)

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------

    def fetch_aum(self, date=None, books_by_fund=None) -> Optional[Dict]:
        date_str = date_to_str(date)
        filename = self._aum_file(date_str)
        if filename is None:
            return None
        try:
            with open(os.path.join(self._cache_dir, filename), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[-] LocalSubredRepository.fetch_aum error: {e}")
            return None

    def fetch_raw(self, date=None, books_by_fund=None, schema_overrides=None) -> Tuple[Optional[pl.DataFrame], Optional[str]]:
        date_str = date_to_str(date)
        schema_overrides = schema_overrides or SUBRED_COLUMNS_READ
        filename = self._raw_file(date_str)
        if filename is None:
            return None, None
        try:
            df, md5 = load_excel_to_dataframe(
                os.path.join(self._cache_dir, filename),
                schema_overrides=schema_overrides
            )
            return df, md5
        except Exception as e:
            print(f"[-] LocalSubredRepository.fetch_raw error: {e}")
            return None, None

    def save_aum(self, aum_dict: Dict, date=None) -> bool:
        if not aum_dict:
            return False
        date_str = date_to_str(date)
        os.makedirs(self._cache_dir, exist_ok=True)
        path = os.path.join(self._cache_dir, f"{date_str}_aum.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(aum_dict, f, indent=4)
            return True
        except Exception as e:
            print(f"[-] LocalSubredRepository.save_aum error: {e}")
            return False

    def save_raw(self, dataframe: Optional[pl.DataFrame], date=None) -> bool:
        if dataframe is None:
            return False
        date_str = date_to_str(date)
        os.makedirs(self._cache_dir, exist_ok=True)
        path = os.path.join(self._cache_dir, f"{date_str}_aum_raw.xlsx")
        status = export_dataframe_to_excel(dataframe, output_abs_path=path)
        return status.get("success", False)

    def exists(self, date=None) -> bool:
        return self._aum_file(date_to_str(date)) is not None