from __future__ import annotations

import os
import logging
import datetime as dt

from logging.handlers import TimedRotatingFileHandler
from typing import Optional


def log(message: str, level: str = "info", module: str = "aegis"):
    """
    Log a message at the given level.
    Also prints to stdout so it's visible during dev.
    """
    logger = get_logger(module)
    level = level.lower()

    if level == "debug":
        logger.debug(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    elif level == "critical":
        logger.critical(message)
    else:
        logger.info(message)

    print(f"\n{message}")


def get_logger(name: str = "aegis", logs_dir: Optional[str] = None) -> logging.Logger:
    """
    Create or retrieve a named logger.
    Writes to a daily rotating file + stdout.

    logs_dir comes from TenantConfig.logs_dir — different per tenant.
    Falls back to ./logs if not provided.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ---- File handler ----
    logs_dir = logs_dir or os.getenv("LOGS_DIR_ABS_PATH", "./logs")
    os.makedirs(logs_dir, exist_ok=True)

    filename = f"aegis_{dt.datetime.now().strftime('%Y-%m-%d')}.log"
    log_path = os.path.join(logs_dir, filename)

    file_handler = TimedRotatingFileHandler(
        filename=log_path,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
        utc=False,
        delay=True
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # ---- Console handler ----
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger