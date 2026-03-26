from __future__ import annotations

import datetime as dt
from typing import Optional

from src.utils.formatters import str_to_date


def previous_business_day(date: Optional[str | dt.datetime | dt.date] = None) -> dt.date:
    """
    Return the given date, adjusted back to Friday if it falls on a weekend.
    Does NOT handle public holidays.
    """
    date = str_to_date(date)
    while date.weekday() >= 5:  # 5=Saturday, 6=Sunday
        date -= dt.timedelta(days=1)
    return date


def monday_of_week(date: Optional[str | dt.datetime | dt.date] = None) -> dt.date:
    """Return the Monday of the week containing the given date."""
    date = str_to_date(date)
    return date - dt.timedelta(days=date.weekday())


def get_qtd_start(date_ref: Optional[str | dt.datetime | dt.date] = None) -> dt.date:
    """
    Return the day before the first day of the current quarter.
    Used as the QTD start reference.
    """
    date_ref = str_to_date(date_ref)
    quarter = (date_ref.month - 1) // 3 + 1
    first_month = 3 * (quarter - 1) + 1
    first_day = dt.date(date_ref.year, first_month, 1)
    return first_day - dt.timedelta(days=1)


def get_mtd_start(date_ref: Optional[str | dt.datetime | dt.date] = None) -> dt.date:
    """
    Return the day before the first day of the current month.
    Used as the MTD start reference.
    """
    date_ref = str_to_date(date_ref)
    first_day = date_ref.replace(day=1)
    return first_day - dt.timedelta(days=1)

def resolve_trade_dates(date: Optional[str] = None, 
                        trade_date: Optional[str] = None) -> tuple[dt.date, dt.date]:
    """
    Resolves a base string date and a trade string date into Python dt.date.
    If they are missing, it defaults to the previous business day.
    """
    d = previous_business_day(date) if date else previous_business_day(dt.date.today())
    td = previous_business_day(trade_date) if trade_date else previous_business_day(dt.date.today())
    return d, td