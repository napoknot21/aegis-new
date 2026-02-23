from __future__ import annotations

import os
import re
import math
import time
import hashlib
import calendar

import pandas as pd
import polars as pl
import datetime as dt

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from src.utils.logger import log


def date_to_str(date: Optional[str | dt.date | dt.datetime] = None, format: str = "%Y-%m-%d") -> str:
    """
    Convert a date/datetime/string to a "YYYY-MM-DD" string.
    If date is None, returns today.
    """
    if date is None:
        date_obj = dt.datetime.now()

    elif isinstance(date, dt.datetime):
        date_obj = date

    elif isinstance(date, dt.date):
        date_obj = dt.datetime.combine(date, dt.time.min)

    elif isinstance(date, str):
        try:
            date_obj = dt.datetime.strptime(date, format)
        except ValueError:
            try:
                date_obj = dt.datetime.fromisoformat(date)
            except ValueError:
                raise ValueError(f"Unrecognized date format: '{date}'")

    else:
        raise TypeError("date must be a string, datetime, date or None")

    return date_obj.strftime(format)


def str_to_date(date: Optional[str | dt.date | dt.datetime] = None, format: str = "%Y-%m-%d") -> dt.date:
    """Convert anything date-like to a dt.date object."""
    if date is None:
        return dt.date.today()
    if isinstance(date, dt.datetime):
        return date.date()
    if isinstance(date, dt.date):
        return date
    if isinstance(date, str):
        return dt.datetime.strptime(date, format).date()
    raise TypeError(f"Cannot convert {type(date)} to date")


def shift_months(date: Optional[str | dt.date | dt.datetime] = None, months: int = 1) -> dt.date:
    """Add N months to a date, clamping to end of month if needed."""
    date_obj = str_to_date(date)
    y0, m0 = date_obj.year, date_obj.month
    i = (m0 - 1) + months
    y = y0 + i // 12
    m = (i % 12) + 1
    last = calendar.monthrange(y, m)[1]
    return dt.date(y, m, min(date_obj.day, last))


def monday_of_week(date: Optional[str | dt.date | dt.datetime] = None) -> dt.date:
    """Return the Monday of the week containing the given date."""
    date_obj = str_to_date(date)
    return date_obj - dt.timedelta(days=date_obj.weekday())


def check_email_format(email: str) -> bool:
    """Basic regex check for email format."""
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email) is not None


def dataframe_fingerprint(dataframe: pl.DataFrame) -> str:
    """Fast deterministic MD5 fingerprint of a Polars DataFrame."""
    h = dataframe.hash_rows(seed=0).to_numpy()
    return hashlib.md5(h.tobytes()).hexdigest()


def format_numeric_columns_to_string(
    df: pl.DataFrame,
    columns: Optional[List[str]] = None,
    decimals: int = 2,
    thousand_sep: str = ",",
    decimal_sep: str = ".",
) -> pl.DataFrame:
    """
    Convert numeric columns to human-readable formatted strings.
    Example: 1234567.89 → "1,234,567.89"
    If columns=None, all numeric columns are formatted.
    """
    if columns is None:
        numeric_types = {
            pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.Int128,
            pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
            pl.Float32, pl.Float64,
        }
        columns = [c for c, t in df.schema.items() if t in numeric_types]

    fmt = f"{{:,.{decimals}f}}"
    exprs = []

    for col in columns:
        exprs.append(
            pl.col(col)
            .cast(pl.Float64, strict=False)
            .map_elements(
                lambda x, f=fmt: (
                    " - "
                    if x is None or (isinstance(x, float) and math.isnan(x))
                    else f.format(x).replace(",", thousand_sep).replace(".", decimal_sep)
                ),
                return_dtype=pl.Utf8,
            )
            .alias(col)
        )

    return df.with_columns(exprs)


def get_most_recent_file_for_date(
    date: str | dt.datetime | dt.date,
    fundation: str,
    directory_map: Dict,
    regex: re.Pattern,
    extension: str = ".xlsx",
) -> Optional[Path]:
    """
    Find the most recent file for a given date and fund directory.
    Scans the directory, matches filename against regex, picks latest timestamp.
    """
    start = time.time()
    date = date_to_str(date)
    target_day = dt.datetime.strptime(date, "%Y-%m-%d").date()
    dir_abs_path = directory_map.get(fundation)

    best_ts: Optional[dt.datetime] = None
    best_path: Optional[Path] = None

    root = Path(dir_abs_path)
    with os.scandir(root) as it:
        for entry in it:
            if not entry.is_file():
                continue
            if not entry.name.lower().endswith(extension):
                continue
            stem = os.path.splitext(entry.name)[0]
            m = regex.match(stem)
            if not m:
                continue
            day_str, hhmm_str = m.group(1), m.group(2)
            try:
                d = dt.datetime.strptime(day_str, "%Y-%m-%d").date()
                t = dt.datetime.strptime(hhmm_str, "%H-%M").time()
            except ValueError:
                continue
            if d != target_day:
                continue
            ts = dt.datetime.combine(d, t)
            if best_ts is None or ts > best_ts:
                best_ts = ts
                best_path = Path(entry.path)

    log(f"[*] Search done in {time.time() - start:.2f} seconds")
    return best_path


def get_most_recent_file(
    fundation: str,
    directory_map: Dict,
    regex: re.Pattern,
    extension: str = ".xlsx",
) -> Optional[Path]:
    """
    Find the most recent file overall (no date filter) for a given fund directory.
    """
    start = time.time()
    dir_abs_path = directory_map.get(fundation)
    root = Path(dir_abs_path)

    best_ts: Optional[dt.datetime] = None
    best_path: Optional[Path] = None

    with os.scandir(root) as it:
        for entry in it:
            if not entry.is_file():
                continue
            if not entry.name.lower().endswith(extension):
                continue
            stem = os.path.splitext(entry.name)[0]
            m = regex.match(stem)
            if not m:
                continue
            day_str, hhmm_str = m.group(1), m.group(2)
            try:
                d = dt.datetime.strptime(day_str, "%Y-%m-%d").date()
                t = dt.datetime.strptime(hhmm_str, "%H-%M").time()
            except ValueError:
                continue
            ts = dt.datetime.combine(d, t)
            if best_ts is None or ts > best_ts:
                best_ts = ts
                best_path = Path(entry.path)

    log(f"[*] Search most recent file done in {time.time() - start:.2f} seconds")
    return best_path


def date_cast_expr_from_utf8(
    col: str,
    *,
    to_datetime: bool = False,
    formats: list[str] | None = None,
    allow_us_mdy: bool = False,
    enable_excel_serial: bool = True,
) -> pl.Expr:
    """
    Parse messy date strings with multiple format attempts + Excel serial fallback.
    Returns a Polars Expr aliased to `col`.
    """
    fmts = formats or [
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%b %e, %Y",
        "%b %-d, %Y",
        "%Y.%m.%d",
    ]
    if allow_us_mdy:
        fmts.append("%m/%d/%Y")

    txt = (
        pl.col(col).cast(pl.Utf8, strict=False)
        .str.replace_all("\u00A0", " ")
        .str.replace_all(r"[ ]{2,}", " ")
        .str.strip_chars()
    )

    parsed = [
        txt.str.strptime(
            pl.Datetime if to_datetime else pl.Date,
            format=f,
            strict=False,
            exact=False,
        )
        for f in fmts
    ]

    out = parsed[0]
    for p in parsed[1:]:
        out = out.fill_null(p)

    if enable_excel_serial:
        excel_fallback = (
            pl.when(pl.col(col).cast(pl.Float64, strict=False).is_not_null())
            .then(
                (pl.datetime(1899, 12, 30) + pl.duration(
                    days=pl.col(col).cast(pl.Float64, strict=False).round(0).cast(pl.Int64)
                )).cast(pl.Datetime if to_datetime else pl.Date, strict=False)
            )
        )
        out = out.fill_null(excel_fallback)

    return out.alias(col)


def numeric_cast_expr_from_utf8(
    col: str,
    target_dtype: pl.PolarsDataType,
    decimal: str = ".",
    int_rounding: str = "nearest",
) -> pl.Expr:
    """
    Clean and cast a string column to a numeric Polars dtype.
    Handles: spaces, NBSP, %, currency symbols, parentheses negatives, thousands separators.
    """
    e = pl.col(col).cast(pl.Utf8, strict=False)
    e = (
        e.str.strip_chars()
        .str.replace_all(r"\s+", "")
        .str.replace_all(r"[%€$£]", "")
        .str.replace_all(r"\(([^)]+)\)", r"-$1")
    )

    if decimal == ".":
        e = e.str.replace_all(",", "")
    elif decimal == ",":
        e = e.str.replace_all(r"\.", "").str.replace_all(",", ".")
    else:
        raise ValueError('decimal must be "." or ","')

    e_float = e.cast(pl.Float64, strict=False)

    if target_dtype in (pl.Float32, pl.Float64):
        return e_float.alias(col)

    if int_rounding == "nearest":
        e_int = e_float.round(0)
    elif int_rounding == "floor":
        e_int = e_float.floor()
    elif int_rounding == "ceil":
        e_int = e_float.ceil()
    elif int_rounding == "truncate":
        e_int = pl.when(e_float < 0).then(e_float.ceil()).otherwise(e_float.floor())
    else:
        raise ValueError('int_rounding must be "nearest" | "floor" | "ceil" | "truncate"')

    return e_int.cast(target_dtype, strict=False).alias(col)


def normalize_fx_dict(
    raw_fx: Optional[Dict[str, float]] = None,
    ends_with: str = "-X",
    start_with: str = "EUR",
) -> Optional[Dict[str, float]]:
    """
    Normalize Yahoo Finance FX tickers into {currency: rate_per_EUR}.
    Example: {'EURUSD=X': 1.1, 'EURCHF=X': 0.95} → {'EUR': 1.0, 'USD': 1.1, 'CHF': 0.95}
    """
    normalized: Dict[str, float] = {"EUR": 1.0}

    for pair, val in raw_fx.items():
        if pd.isna(val):
            continue
        name = str(pair).upper()
        if name.endswith(ends_with):
            name = name[:-2]
        if name.startswith(start_with) and len(name) >= 6:
            ccy = name[3:6]
            normalized[ccy] = float(val)

    return normalized


def exclude_token_cols_from_df(dataframe: pl.DataFrame, column: str, token: str) -> pl.DataFrame:
    """Filter out rows where `column` contains `token` (case-insensitive)."""
    return dataframe.filter(~pl.col(column).str.contains(rf"(?i){token}"))


def filter_token_col_from_df(dataframe: pl.DataFrame, column: str, token: str) -> pl.DataFrame:
    """Keep only rows where `column` contains `token` (case-insensitive)."""
    if token is None or column is None:
        return dataframe
    return dataframe.filter(pl.col(column).str.contains(rf"(?i){token}"))