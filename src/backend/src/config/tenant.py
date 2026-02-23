from __future__ import annotations

"""
tenant.py
---------
Defines the TenantConfig dataclass and its loader.

A "tenant" in Aegis is one client deployment. Each tenant has:
  - Its own file paths (where their Excel files live on the server)
  - Its own LIBAPI connection settings (URL, credentials)
  - Its own fund/book mappings (some clients have different fund structures)
  - A use_db flag that switches the entire backend from file-based to DB-based
    without any code change — just flip the env var AEGIS_USE_DB=true

How to add a new tenant:
  1. Create a new .env file for them (e.g. .env.client_xyz)
  2. Set AEGIS_TENANT_ID=client_xyz
  3. Fill in their specific paths and fund names
  4. Done — no code changes needed
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict
from dotenv import load_dotenv


def _load_env (tenant_id : Optional[int | str] = None) -> None:
    """
    Load the right .env file for this tenant.
    Falls back to .env if no tenant-specific file exists.
    
    Priority:
      1. .env.{tenant_id}   (tenant-specific)
      2. .env               (default / dev)
    """
    if tenant_id :
        
        tenant_id = str(tenant_id) if isinstance(tenant_id, int) else tenant_id
        tenant_env = f".env.{tenant_id}"
        
        if os.path.exists(tenant_env) :
            
            load_dotenv(tenant_env, override=True)
            return

    load_dotenv(override=True)


@dataclass
class TenantConfig:
    """
    All runtime configuration for one tenant.
    
    Populated from environment variables — never hardcoded.
    Passed down to repositories and services via dependency injection.
    """

    tenant_id: str

    # ----------------------------------------------------------------
    # Fund identity
    # ----------------------------------------------------------------
    fund_hv: str = ""
    fund_wr: str = ""

    # ----------------------------------------------------------------
    # LIBAPI (external datacenter)
    # ----------------------------------------------------------------
    libapi_abs_path: str = ""          # path to the libapi package on this machine

    # ----------------------------------------------------------------
    # File paths — all per-tenant, all from env
    # ----------------------------------------------------------------
    subred_cache_dir: str = ""

    simm_paths: Dict[str, str] = field(default_factory=dict)       # fund → dir
    nav_portfolio_paths: Dict[str, str] = field(default_factory=dict)
    nav_estimate_paths: Dict[str, str] = field(default_factory=dict)
    expiries_paths: Dict[str, str] = field(default_factory=dict)
    cash_paths: Dict[str, str] = field(default_factory=dict)
    collateral_paths: Dict[str, str] = field(default_factory=dict)
    leverages_paths: Dict[str, str] = field(default_factory=dict)
    greeks_paths: Dict[str, str] = field(default_factory=dict)
    screeners_paths: Dict[str, str] = field(default_factory=dict)
    concentration_paths: Dict[str, str] = field(default_factory=dict)

    payments_dir: str = ""
    payments_db_path: str = ""
    payments_beneficiary_db_path: str = ""
    payments_excel_template_path: str = ""
    securities_db_path: str = ""

    trade_recap_dir: str = ""
    trade_recap_raw_dir: str = ""

    logs_dir: str = ""

    # ----------------------------------------------------------------
    # Database (future)
    # ----------------------------------------------------------------
    db_url: Optional[str] = None

    # ----------------------------------------------------------------
    # Feature flags
    # ----------------------------------------------------------------
    use_db: bool = False           # False = read from files, True = read from DB
    use_cache: bool = True         # whether to use the local file cache


def load_tenant_config(tenant_id: Optional[str] = None) -> TenantConfig:
    """
    Build a TenantConfig from environment variables.
    
    Call this once at app startup (via FastAPI lifespan or Depends).
    
    Args:
        tenant_id: Override tenant ID. If None, reads AEGIS_TENANT_ID from env.
    """
    tenant_id = tenant_id or os.getenv("AEGIS_TENANT_ID", "default")
    _load_env(tenant_id)

    # Read fund names first — used to build path dicts below
    fund_hv = os.getenv("FUND_HV", "")
    fund_wr = os.getenv("FUND_WR", "")

    return TenantConfig(
        tenant_id=tenant_id,

        fund_hv=fund_hv,
        fund_wr=fund_wr,

        libapi_abs_path=os.getenv("LIBAPI_ABS_PATH", ""),

        # SubRed
        subred_cache_dir=os.getenv("SUBRED_AUM_CACHE_ABS_PATH", ""),

        # SIMM
        simm_paths={
            fund_hv: os.getenv("SIMM_FUND_HV_DIR_PATH", ""),
            fund_wr: os.getenv("SIMM_FUND_WR_DIR_PATH", ""),
        },

        # NAV
        nav_portfolio_paths={
            fund_hv: os.getenv("NAV_PORTFOLIO_FUND_HV_DIR_PATH", ""),
            fund_wr: os.getenv("NAV_PORTFOLIO_FUND_WR_DIR_PATH", ""),
        },
        nav_estimate_paths={
            fund_hv: os.getenv("NAV_ESTIMATE_FUND_HV_DIR_PATH", ""),
            fund_wr: os.getenv("NAV_ESTIMATE_FUND_WR_DIR_PATH", ""),
        },

        # Expiries
        expiries_paths={
            fund_hv: os.getenv("EXPIRIES_FUND_HV_DIR_PATH", ""),
            fund_wr: os.getenv("EXPIRIES_FUND_WR_DIR_PATH", ""),
        },

        # Cash / Collateral
        cash_paths={
            fund_hv: os.getenv("CASH_FUND_HV_FILE_PATH", ""),
            fund_wr: os.getenv("CASH_FUND_WR_FILE_PATH", ""),
        },
        collateral_paths={
            fund_hv: os.getenv("COLLAT_FUND_HV_FILE_PATH", ""),
            fund_wr: os.getenv("COLLAT_FUND_WR_FILE_PATH", ""),
        },

        # Leverages
        leverages_paths={
            fund_hv: os.getenv("LEVERAGES_FUND_HV_DIR_PATH", ""),
            fund_wr: os.getenv("LEVERAGES_FUND_WR_DIR_PATH", ""),
        },

        # Greeks
        greeks_paths={
            fund_hv: os.getenv("GREEKS_FUND_HV_DIR_ABS", ""),
            fund_wr: os.getenv("GREEKS_FUND_WR_DIR_ABS", ""),
        },

        # Screeners
        screeners_paths={
            fund_hv: os.getenv("SCREENERS_FUND_HV_DIR_ABS", ""),
            fund_wr: os.getenv("SCREENERS_FUND_WR_DIR_ABS", ""),
        },

        # Concentration
        concentration_paths={
            fund_hv: os.getenv("CONCENTRATION_FUND_HV_DIR_ABS", ""),
            fund_wr: os.getenv("CONCENTRATION_FUND_WR_DIR_ABS", ""),
        },

        # Payments
        payments_dir=os.getenv("PAYMENTS_DIR_ABS_PATH", ""),
        payments_db_path=os.getenv("PAYMENTS_DB_ABS_PATH", ""),
        payments_beneficiary_db_path=os.getenv("PAYMENTS_BENECIFIARY_DB_ABS_PATH", ""),
        payments_excel_template_path=os.getenv("PAYMENTS_EXCEL_TEMPLATE_ABS_PATH", ""),
        securities_db_path=os.getenv("SECURITIES_DB_ABS_PATH", ""),

        # Trade Recap
        trade_recap_dir=os.getenv("TRADE_RECAP_ABS_PATH", ""),
        trade_recap_raw_dir=os.getenv("TREADE_RECAP_DATA_RAW_DIR_ABS_PATH", ""),

        # Logs
        logs_dir=os.getenv("LOGS_DIR_ABS_PATH", ""),

        # DB
        db_url=os.getenv("AEGIS_DB_URL"),

        # Feature flags
        use_db=os.getenv("AEGIS_USE_DB", "false").lower() == "true",
        use_cache=os.getenv("AEGIS_USE_CACHE", "true").lower() == "true",
    )