from datetime import date

import pytest

from bolsabr.b3.trading_calendar import (
    business_days_between,
    is_trading_day,
    next_trading_day,
    previous_trading_day,
)


def test_2026_official_b3_calendar_exceptions():
    assert not is_trading_day(date(2026, 9, 7))
    assert not is_trading_day(date(2026, 12, 24))
    assert not is_trading_day(date(2026, 12, 31))
    assert is_trading_day(date(2026, 2, 18))
    assert is_trading_day(date(2026, 7, 9))


def test_next_trading_day_derives_petr4_ex_date():
    assert next_trading_day(date(2026, 8, 21)) == date(2026, 8, 24)


def test_next_trading_day_skips_weekend_and_october_holiday():
    assert next_trading_day(date(2026, 10, 9)) == date(2026, 10, 13)


def test_previous_trading_day_skips_market_closure():
    assert previous_trading_day(date(2026, 9, 8)) == date(2026, 9, 4)


def test_business_days_between():
    assert business_days_between(date(2026, 8, 21), date(2026, 8, 24)) == 1


def test_unknown_year_fails_closed():
    with pytest.raises(LookupError):
        is_trading_day(date(2027, 1, 4))
