from __future__ import annotations

from typing import Any
import re

from bolsabr.b3.trading_calendar import business_days_between
from bolsabr.chain import OptionChain, OptionLegSnapshot


SCHEMA_VERSION = "0.1"

_WEEKLY_TICKER = re.compile(r"W[1-5]$")


def _expiration_type(rows) -> str:
    """Classify expiry from B3's own weekly option ticker suffix W1..W5."""
    tickers = [
        leg.ticker
        for row in rows
        for leg in (row.call, row.put)
        if leg is not None
    ]
    return "WEEKLY" if any(_WEEKLY_TICKER.search(ticker) for ticker in tickers) else "MONTHLY"


def _leg_to_dict(leg: OptionLegSnapshot | None) -> dict[str, Any] | None:
    if leg is None:
        return None
    return {
        "ticker": leg.ticker,
        "type": leg.option_type,
        "exercise_style": leg.exercise_style,
        "pricing_model": leg.pricing_model,
        "market": {
            "last": leg.last,
            "bid": leg.bid,
            "ask": leg.ask,
            "spread_pct": leg.spread_pct,
            "quote_state": leg.quote_state,
            "quality_flags": list(leg.quality_flags),
            "trade_count": leg.trade_count,
            "volume": leg.volume,
            "financial_volume": leg.financial_volume,
            "open_interest": leg.open_interest,
        },
        "analytics_input": {
            "price": leg.price_for_model,
            "price_basis": leg.price_basis,
            "risk_free_rate": leg.risk_free_rate,
        },
        "analytics": {
            "intrinsic": leg.intrinsic,
            "extrinsic": leg.extrinsic,
            "iv": leg.iv,
            "delta": leg.greeks.delta if leg.greeks else None,
            "gamma": leg.greeks.gamma if leg.greeks else None,
            "theta": leg.greeks.theta if leg.greeks else None,
            "vega": leg.greeks.vega if leg.greeks else None,
            "rho": leg.greeks.rho if leg.greeks else None,
        },
    }


def option_chain_to_dict(
    chain: OptionChain,
    *,
    rate_source: str = "B3_DI1",
    market_data_source: str = "B3_EOD",
) -> dict[str, Any]:
    expirations: list[dict[str, Any]] = []

    for expiration in chain.expirations:
        try:
            dte_business = business_days_between(chain.ref_date, expiration.expiration)
        except LookupError:
            dte_business = None

        expirations.append(
            {
                "date": expiration.expiration.isoformat(),
                "type": _expiration_type(expiration.rows),
                "dte_calendar": expiration.days_to_expiration,
                "dte_business": dte_business,
                "risk_free_rate": expiration.risk_free_rate,
                "rows": [
                    {
                        "strike": row.strike,
                        "call": _leg_to_dict(row.call),
                        "put": _leg_to_dict(row.put),
                    }
                    for row in expiration.rows
                ],
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "ref_date": chain.ref_date.isoformat(),
        "market_data_source": market_data_source,
        "rate_source": rate_source,
        "underlying": {
            "ticker": chain.underlying,
            "spot": chain.spot,
        },
        "fallback_risk_free_rate": chain.risk_free_rate,
        "dividend_yield": chain.dividend_yield,
        "expirations": expirations,
    }
