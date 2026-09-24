from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache


# Official B3 equity/derivatives market closures for 2026.
# Source:
# https://www.b3.com.br/pt_br/noticias/calendario-de-negociacao-da-b3-confira-o-funcionamento-da-bolsa-em-2026.htm
#
# Notes:
# - 18/02/2026 (Ash Wednesday) has special hours, but IS a trading day.
# - 09/07/2026 (Sao Paulo state holiday) has normal trading.
B3_CLOSED_DATES_2026 = frozenset(
    {
        date(2026, 1, 1),
        date(2026, 2, 16),
        date(2026, 2, 17),
        date(2026, 4, 3),
        date(2026, 4, 21),
        date(2026, 5, 1),
        date(2026, 6, 4),
        date(2026, 9, 7),
        date(2026, 10, 12),
        date(2026, 11, 2),
        date(2026, 11, 20),
        date(2026, 12, 24),
        date(2026, 12, 25),
        date(2026, 12, 31),
    }
)


@lru_cache(maxsize=None)
def closed_dates(year: int) -> frozenset[date]:
    """Return versioned B3 market-closure dates available to BOLSABR."""
    if year == 2026:
        return B3_CLOSED_DATES_2026
    raise LookupError(f"B3 market calendar not versioned for year {year}")


def is_trading_day(day: date) -> bool:
    if day.weekday() >= 5:
        return False
    return day not in closed_dates(day.year)


def next_trading_day(day: date) -> date:
    """First B3 trading session strictly after the supplied date."""
    candidate = day + timedelta(days=1)
    while not is_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def previous_trading_day(day: date) -> date:
    """Last B3 trading session strictly before the supplied date."""
    candidate = day - timedelta(days=1)
    while not is_trading_day(candidate):
        candidate -= timedelta(days=1)
    return candidate


def business_days_between(start: date, end: date) -> int:
    """Count B3 trading days in the half-open interval after start through end."""
    if end < start:
        return -business_days_between(end, start)
    count = 0
    candidate = start + timedelta(days=1)
    while candidate <= end:
        if is_trading_day(candidate):
            count += 1
        candidate += timedelta(days=1)
    return count
