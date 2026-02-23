from __future__ import annotations

"""
dependencies.py
---------------
FastAPI dependency injection.

Every route gets a TenantConfig and pre-built services injected via Depends().
This is the ONLY place where repositories are instantiated and wired together.

To migrate a domain to DB:
  - Set AEGIS_USE_DB=true in the tenant's .env
  - The factory below automatically uses StorageSubredRepository instead of LocalSubredRepository
  - Zero other changes needed
"""

import os
from functools import lru_cache
from fastapi import Depends, Header
from typing import Optional, Annotated

from src.config.tenant import TenantConfig, load_tenant_config
from src.services.subred_service import SubredService
from src.repositories.local.subred import LocalSubredRepository
from src.repositories.remote.subred import RemoteSubredRepository
from src.repositories.storage.subred import StorageSubredRepository


# ----------------------------------------------------------------
# Tenant config
# ----------------------------------------------------------------

def get_tenant_config(
    x_tenant_id: Annotated[Optional[str], Header()] = None
) -> TenantConfig:
    """
    Resolve tenant from the X-Tenant-Id request header.
    Falls back to AEGIS_TENANT_ID env var, then "default".

    In production behind a reverse proxy, the proxy injects
    X-Tenant-Id based on the subdomain or auth token.
    In dev, just set AEGIS_TENANT_ID in your .env.
    """
    tenant_id = x_tenant_id or os.getenv("AEGIS_TENANT_ID", "default")
    return load_tenant_config(tenant_id)


TenantDep = Annotated[TenantConfig, Depends(get_tenant_config)]


# ----------------------------------------------------------------
# Service factories — one per domain
# ----------------------------------------------------------------

def get_subred_service(config: TenantDep) -> SubredService:
    """
    Wires SubredService with the right repositories based on tenant config.

    Current state  (use_db=False): LocalSubredRepository  ← file-based cache
    After migration (use_db=True):  StorageSubredRepository ← database

    The live/remote source (RemoteSubredRepository) never changes.
    """
    live_repo = RemoteSubredRepository(config)

    if config.use_db:
        cache_repo = StorageSubredRepository(config)
    else:
        cache_repo = LocalSubredRepository(config) if config.use_cache else None

    return SubredService(live_repo=live_repo, cache_repo=cache_repo)


SubredServiceDep = Annotated[SubredService, Depends(get_subred_service)]

# Add more service factories here as you build them:
# def get_nav_service(config: TenantDep) -> NavService: ...
# def get_simm_service(config: TenantDep) -> SimmService: ...