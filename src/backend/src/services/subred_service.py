from __future__ import annotations

import datetime as dt
import polars as pl
from typing import Optional, Dict, Tuple

from src.repositories.base.subred import BaseSubredRepository
from src.models.subred import SubredAUMResponse, SubredFundEntry
from src.utils.formatters import date_to_str


class SubredService :

    def __init__ (
            
            self,
            live_repo : BaseSubredRepository,
            cache_repo : Optional[BaseSubredRepository] = None
        
        ) :
        """
        
        """
        self.live = live_repo
        self.cache = cache_repo


    def get_aum (
            
            self,
            date : Optional[str | dt.datetime | dt.date] = None,
            books_by_fund = None,
            force_refresh = False
        
        ) -> Optional[SubredAUMResponse] :
        """
        
        """
        date_str = date_to_str(date)

        if not force_refresh and self.cache and self.cache.exists(date) :
            
            data = self.cache.fetch_aum(date, books_by_fund)
            
            if data :
                return self._to_response(data, date_str, source="local")

        data = self.live.fetch_aum(date, books_by_fund)
        
        if data is None :
            return None

        if self.cache :
            self.cache.save_aum(data, date)

        response = self._to_response(data, date_str, source="remote") 
        
        return response
     

    def get_raw(self, date=None, books_by_fund=None, schema_overrides=None, force_refresh=False) -> Tuple[Optional[pl.DataFrame], Optional[str]]:
        date_str = date_to_str(date)

        if not force_refresh and self.cache and self.cache.exists(date):
            df, md5 = self.cache.fetch_raw(date, books_by_fund, schema_overrides)
            if df is not None:
                return df, md5

        df, md5 = self.live.fetch_raw(date, books_by_fund, schema_overrides)
        if df is None:
            return None, None

        if self.cache:
            self.cache.save_raw(df, date)

        return df, md5

    def save_aum_manually(self, aum_dict: Dict, date=None) -> bool:
        if not self.cache:
            return False
        return self.cache.save_aum(aum_dict, date)

    def _to_response(self, data: Dict, date_str: str, source: str) -> SubredAUMResponse:
        return SubredAUMResponse(
            funds={f: SubredFundEntry(amount=e["amount"], currency=e["currency"]) for f, e in data.items()},
            date=date_str,
            source=source,
        )