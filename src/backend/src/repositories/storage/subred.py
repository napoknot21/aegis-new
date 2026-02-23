from __future__ import annotations

"""
StorageSubredRepository
-----------------------
Database-backed implementation. NOT YET IMPLEMENTED.

When you're ready to migrate:
1. Implement the methods below using SQLAlchemy or your ORM of choice
2. Set AEGIS_USE_DB=true in the tenant's .env
3. Run scripts/migrate_to_db.py once to seed historical data
4. Done — nothing else changes
"""

import polars as pl
from typing import Optional, Dict, Tuple

from src.repositories.base.subred import BaseSubredRepository
from src.config.tenant import TenantConfig


class StorageSubredRepository(BaseSubredRepository):

    def __init__(self, config: TenantConfig):
        self._db_url = config.db_url
        # self._session = SessionLocal(db_url)  ← wire up when implementing

    def fetch_aum(self, date=None, books_by_fund=None) -> Optional[Dict]:
        raise NotImplementedError

    def fetch_raw(self, date=None, books_by_fund=None, schema_overrides=None) -> Tuple[Optional[pl.DataFrame], Optional[str]]:
        raise NotImplementedError

    def save_aum(self, aum_dict: Dict, date=None) -> bool:
        raise NotImplementedError

    def save_raw(self, dataframe: pl.DataFrame, date=None) -> bool:
        raise NotImplementedError

    def exists(self, date=None) -> bool:
        raise NotImplementedError