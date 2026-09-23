from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Literal

OptionType = Literal["CALL", "PUT"]


@dataclass(frozen=True)
class Greeks:
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def intrinsic_value(spot: float, strike: float, option_type: OptionType) -> float:
    return max(spot - strike, 0.0) if option_type == "CALL" else max(strike - spot, 0.0)


def moneyness_pct(spot: float, strike: float) -> float:
    if spot <= 0:
        raise ValueError("spot must be positive")
    return (strike / spot - 1.0) * 100.0


def classify_moneyness(
    spot: float,
    strike: float,
    option_type: OptionType,
    atm_band_pct: float = 0.5,
) -> str:
    distance = abs(moneyness_pct(spot, strike))
    if distance <= atm_band_pct:
        return "ATM"
    if option_type == "CALL":
        return "ITM" if spot > strike else "OTM"
    return "ITM" if spot < strike else "OTM"


def black_scholes_merton_price(
    spot: float,
    strike: float,
    time_years: float,
    rate: float,
    volatility: float,
    option_type: OptionType,
    dividend_yield: float = 0.0,
) -> float:
    if spot <= 0 or strike <= 0:
        raise ValueError("spot and strike must be positive")
    if time_years <= 0:
        return intrinsic_value(spot, strike, option_type)
    if volatility <= 0:
        forward_spot = spot * math.exp(-dividend_yield * time_years)
        discounted_strike = strike * math.exp(-rate * time_years)
        return (
            max(forward_spot - discounted_strike, 0.0)
            if option_type == "CALL"
            else max(discounted_strike - forward_spot, 0.0)
        )

    sigma_sqrt_t = volatility * math.sqrt(time_years)
    d1 = (
        math.log(spot / strike)
        + (rate - dividend_yield + 0.5 * volatility * volatility) * time_years
    ) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t
    discounted_spot = spot * math.exp(-dividend_yield * time_years)
    discounted_strike = strike * math.exp(-rate * time_years)

    if option_type == "CALL":
        return discounted_spot * _norm_cdf(d1) - discounted_strike * _norm_cdf(d2)
    return discounted_strike * _norm_cdf(-d2) - discounted_spot * _norm_cdf(-d1)


def black_scholes_merton_greeks(
    spot: float,
    strike: float,
    time_years: float,
    rate: float,
    volatility: float,
    option_type: OptionType,
    dividend_yield: float = 0.0,
) -> Greeks:
    if min(spot, strike, time_years, volatility) <= 0:
        raise ValueError("spot, strike, time_years and volatility must be positive")

    sqrt_t = math.sqrt(time_years)
    d1 = (
        math.log(spot / strike)
        + (rate - dividend_yield + 0.5 * volatility * volatility) * time_years
    ) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t
    disc_q = math.exp(-dividend_yield * time_years)
    disc_r = math.exp(-rate * time_years)
    pdf = _norm_pdf(d1)

    if option_type == "CALL":
        delta = disc_q * _norm_cdf(d1)
        theta = (
            -(spot * disc_q * pdf * volatility) / (2.0 * sqrt_t)
            - rate * strike * disc_r * _norm_cdf(d2)
            + dividend_yield * spot * disc_q * _norm_cdf(d1)
        ) / 365.0
        rho = strike * time_years * disc_r * _norm_cdf(d2) / 100.0
    else:
        delta = disc_q * (_norm_cdf(d1) - 1.0)
        theta = (
            -(spot * disc_q * pdf * volatility) / (2.0 * sqrt_t)
            + rate * strike * disc_r * _norm_cdf(-d2)
            - dividend_yield * spot * disc_q * _norm_cdf(-d1)
        ) / 365.0
        rho = -strike * time_years * disc_r * _norm_cdf(-d2) / 100.0

    gamma = disc_q * pdf / (spot * volatility * sqrt_t)
    vega = spot * disc_q * pdf * sqrt_t / 100.0
    return Greeks(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)


def crr_american_price(
    spot: float,
    strike: float,
    time_years: float,
    rate: float,
    volatility: float,
    option_type: OptionType,
    dividend_yield: float = 0.0,
    steps: int = 300,
) -> float:
    """Cox-Ross-Rubinstein binomial pricer with early-exercise checks."""
    if spot <= 0 or strike <= 0 or volatility <= 0:
        raise ValueError("spot, strike and volatility must be positive")
    if time_years <= 0:
        return intrinsic_value(spot, strike, option_type)
    if steps < 2:
        raise ValueError("steps must be >= 2")

    dt = time_years / steps
    u = math.exp(volatility * math.sqrt(dt))
    d = 1.0 / u
    growth = math.exp((rate - dividend_yield) * dt)
    p = (growth - d) / (u - d)
    if not 0.0 <= p <= 1.0:
        raise ValueError(
            "CRR risk-neutral probability outside [0, 1]; increase steps or inspect inputs"
        )
    discount = math.exp(-rate * dt)

    values = [0.0] * (steps + 1)
    for j in range(steps + 1):
        node_spot = spot * (u**j) * (d ** (steps - j))
        values[j] = intrinsic_value(node_spot, strike, option_type)

    for i in range(steps - 1, -1, -1):
        for j in range(i + 1):
            continuation = discount * (p * values[j + 1] + (1.0 - p) * values[j])
            node_spot = spot * (u**j) * (d ** (i - j))
            exercise = intrinsic_value(node_spot, strike, option_type)
            values[j] = max(continuation, exercise)
    return values[0]


def implied_volatility(
    market_price: float,
    pricer: Callable[[float], float],
    *,
    lower: float = 1e-4,
    upper: float = 5.0,
    tolerance: float = 1e-7,
    max_iterations: int = 120,
) -> float:
    """Solve IV with a robust bisection method around a volatility-only pricer."""
    if market_price < 0:
        raise ValueError("market_price cannot be negative")
    # Some numerical models (notably CRR) are undefined for extremely low
    # volatilities when the risk-neutral probability falls outside [0, 1].
    # Move the lower bracket upward until the pricer enters its valid domain.
    lo = lower
    while lo < upper:
        try:
            lo_price = pricer(lo)
            break
        except ValueError:
            lo *= 2.0
    else:
        raise ValueError("could not find a valid lower volatility bound for pricer")

    hi = upper
    hi_price = pricer(hi)
    if market_price < lo_price - tolerance or market_price > hi_price + tolerance:
        raise ValueError(
            f"market price {market_price} is outside model bounds [{lo_price}, {hi_price}]"
        )
    for _ in range(max_iterations):
        mid = (lo + hi) / 2.0
        value = pricer(mid)
        diff = value - market_price
        if abs(diff) <= tolerance:
            return mid
        if diff < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def finite_difference_greeks(
    pricer: Callable[[float, float, float, float], float],
    *,
    spot: float,
    time_years: float,
    rate: float,
    volatility: float,
) -> Greeks:
    """Numerical Greeks for models without closed-form Greeks.

    ``pricer`` receives (spot, time_years, rate, volatility).
    Theta is per calendar day; Vega/Rho are per 1 percentage point.
    """
    ds = max(spot * 0.001, 0.01)
    dt = min(max(1.0 / 365.0, time_years * 0.01), time_years / 2.0)
    dv = 0.0001
    dr = 0.0001

    base = pricer(spot, time_years, rate, volatility)
    up_s = pricer(spot + ds, time_years, rate, volatility)
    dn_s = pricer(max(spot - ds, 1e-9), time_years, rate, volatility)
    delta = (up_s - dn_s) / (2.0 * ds)
    gamma = (up_s - 2.0 * base + dn_s) / (ds * ds)

    shorter_t = max(time_years - dt, 1e-9)
    theta = (pricer(spot, shorter_t, rate, volatility) - base) / (dt * 365.0)
    vega = (pricer(spot, time_years, rate, volatility + dv) - base) / dv / 100.0
    rho = (pricer(spot, time_years, rate + dr, volatility) - base) / dr / 100.0
    return Greeks(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)
