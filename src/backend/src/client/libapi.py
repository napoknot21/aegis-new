from __future__ import annotations

"""
libapi.py
---------
Single gateway to all LIBAPI connections.

LIBAPI is your private package (not on PyPI) — it lives at a path on disk
defined per tenant in TenantConfig.libapi_abs_path.

HOW IT WORKS:
  1. Call setup_libapi_path(config) ONCE at app startup (done in app.py lifespan).
     This does sys.path.append(config.libapi_abs_path) so Python can find libapi.
  2. After that, all `from libapi.xxx import Xxx` work normally anywhere in the app.
  3. The get_*() functions here just instantiate the classes with retry logic.

WHY NOT sys.path.append inside each function:
  - It works but is wasteful — Python would re-check the path on every call.
  - Doing it once at startup is the standard pattern for vendored packages.
"""

import sys
import logging
from typing import Optional, Any

from src.config.tenant import TenantConfig

logger = logging.getLogger(__name__)


def setup_libapi_path(config: TenantConfig) -> None:
    """
    Register the LIBAPI package directory in sys.path.
    Call this ONCE at app startup before any libapi imports.

    After this runs, anywhere in the codebase you can do:
        from libapi.ice.trade_manager import TradeManager
        from libapi.pricers.fx import PricerFX
        etc.
    """
    path = config.libapi_abs_path

    if not path:
        logger.warning("[!] LIBAPI_ABS_PATH is not set in tenant config.")
        return

    if path not in sys.path:
        sys.path.append(path)
        logger.info(f"[+] LIBAPI path registered: {path}")


# ----------------------------------------------------------------
# TradeManager
# ----------------------------------------------------------------

def get_trade_manager(loopback: int = 3) -> Optional[Any]:
    """
    Instantiate and return a TradeManager.
    Assumes setup_libapi_path() was already called at startup.
    Retries up to `loopback` times on connection failure.
    """
    if loopback < 0:
        logger.error("[-] TradeManager connection failed after all retries.")
        return None

    try:
        from libapi.ice.trade_manager import TradeManager  # type: ignore
        instance = TradeManager()
        logger.info("[+] TradeManager connected.")
        return instance

    except Exception as e:
        logger.warning(f"[!] TradeManager failed: {e}. Retrying...")
        return get_trade_manager(loopback - 1)


# ----------------------------------------------------------------
# IceCalculator
# ----------------------------------------------------------------

def get_ice_calculator(loopback: int = 3) -> Optional[Any]:
    """
    Instantiate and return an IceCalculator.
    Assumes setup_libapi_path() was already called at startup.
    """
    if loopback < 0:
        logger.error("[-] IceCalculator connection failed after all retries.")
        return None

    try:
        from libapi.ice.calculator import IceCalculator  # type: ignore
        instance = IceCalculator()
        logger.info("[+] IceCalculator connected.")
        return instance

    except Exception as e:
        logger.warning(f"[!] IceCalculator failed: {e}. Retrying...")
        return get_ice_calculator(loopback - 1)


# ----------------------------------------------------------------
# Pricers
# ----------------------------------------------------------------

def get_pricer_fx() -> Optional[Any]:
    """Instantiate and return a PricerFX."""
    try:
        from libapi.pricers.fx import PricerFX  # type: ignore
        return PricerFX()
    except Exception as e:
        logger.error(f"[-] PricerFX init failed: {e}")
        return None


def get_pricer_eq() -> Optional[Any]:
    """Instantiate and return a PricerEQ."""
    try:
        from libapi.pricers.eq import PricerEQ  # type: ignore
        return PricerEQ()
    except Exception as e:
        logger.error(f"[-] PricerEQ init failed: {e}")
        return None