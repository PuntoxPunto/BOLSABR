import math

import pytest

from bolsabr.analytics.options import (
    black_scholes_merton_greeks,
    black_scholes_merton_price,
    classify_moneyness,
    crr_american_price,
    implied_volatility,
    intrinsic_value,
)


def test_intrinsic_values():
    assert intrinsic_value(50, 45, "CALL") == 5
    assert intrinsic_value(50, 55, "CALL") == 0
    assert intrinsic_value(50, 55, "PUT") == 5


def test_moneyness_classification():
    assert classify_moneyness(50, 50.1, "CALL", atm_band_pct=0.5) == "ATM"
    assert classify_moneyness(50, 45, "CALL") == "ITM"
    assert classify_moneyness(50, 55, "PUT") == "ITM"


def test_black_scholes_reference_price():
    price = black_scholes_merton_price(100, 100, 1.0, 0.05, 0.20, "CALL")
    assert price == pytest.approx(10.4506, abs=1e-4)


def test_implied_volatility_recovers_sigma():
    target_sigma = 0.37
    market_price = black_scholes_merton_price(48, 50, 45 / 365, 0.12, target_sigma, "CALL")
    solved = implied_volatility(
        market_price,
        lambda sigma: black_scholes_merton_price(48, 50, 45 / 365, 0.12, sigma, "CALL"),
    )
    assert solved == pytest.approx(target_sigma, abs=1e-5)


def test_american_call_without_dividend_close_to_european():
    euro = black_scholes_merton_price(100, 100, 1.0, 0.05, 0.2, "CALL")
    american = crr_american_price(100, 100, 1.0, 0.05, 0.2, "CALL", steps=600)
    assert american == pytest.approx(euro, abs=0.03)


def test_greeks_are_finite_and_delta_in_range():
    g = black_scholes_merton_greeks(48, 50, 45 / 365, 0.12, 0.37, "CALL")
    assert 0 < g.delta < 1
    assert g.gamma > 0
    assert g.vega > 0
    assert all(math.isfinite(v) for v in (g.delta, g.gamma, g.theta, g.vega, g.rho))



def test_implied_volatility_handles_crr_low_sigma_invalid_domain():
    spot = 48.35
    strike = 48.36
    time_years = 24 / 365
    rate = 0.1279532702962247
    target_sigma = 0.42

    market_price = crr_american_price(
        spot,
        strike,
        time_years,
        rate,
        target_sigma,
        "CALL",
        steps=250,
    )
    solved = implied_volatility(
        market_price,
        lambda sigma: crr_american_price(
            spot,
            strike,
            time_years,
            rate,
            sigma,
            "CALL",
            steps=250,
        ),
    )
    assert solved == pytest.approx(target_sigma, abs=1e-5)
