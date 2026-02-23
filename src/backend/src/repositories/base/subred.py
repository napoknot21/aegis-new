from __future__ import annotations

import datetime as dt
import polars as pl
from abc import ABC, abstractmethod
from typing import Optional, Dict, Tuple, List


class BaseSubredRepository(ABC) :

    @abstractmethod
    def fetch_aum(
        self,
        date : Optional[str | dt.datetime | dt.date] = None,
        books_by_fund : Optional[List[str]] = None
    ) -> Optional[Dict] : ...

    @abstractmethod
    def fetch_raw(
        self,
        date : Optional[str | dt.datetime | dt.date] = None,
        books_by_fund : Optional[List[str]] = None,
        schema_overrides : Optional[Dict] = None
    ) -> Tuple[Optional[pl.DataFrame], Optional[str]] : ...

    @abstractmethod
    def save_aum(
        self,
        aum_dict : Dict,
        date : Optional[str | dt.datetime | dt.date] = None
    ) -> bool : ...

    @abstractmethod
    def save_raw(self, dataframe: pl.DataFrame, date=None) -> bool: ...

    @abstractmethod
    def exists(self, date=None) -> bool: ...