import math

import pytest

from bolsabr.bcb.sgs import selic_daily_to_continuous_annual


def test_daily_selic_conversion_is_reversible_by_factor():
    daily_pct = 0.055
    r_cont = selic_daily_to_continuous_annual(daily_pct)
    annual_factor = math.exp(r_cont)
    assert annual_factor == pytest.approx((1 + daily_pct / 100) ** 252)
    assert r_cont > 0
