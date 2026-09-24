from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Callable, Iterable

from bolsabr.analytics.options import (
    Greeks,
    black_scholes_merton_greeks,
    black_scholes_merton_price,
    crr_american_price,
    finite_difference_greeks,
    implied_volatility,
    intrinsic_value,
)
from bolsabr.b3.cotahist import CotahistRecord
from bolsabr.b3.normalize import (
    DailyQuote,
    OpenInterest,
    OptionContract,
    normalize_daily_quote,
    normalize_open_interest,
    normalize_option_contract,
)


@dataclass(frozen=True)
class OptionLegSnapshot:
    ticker: str
    option_type: str
    exercise_style: str
    risk_free_rate: float
    last: float | None
    bid: float | None
    ask: float | None
    spread_pct: float | None
    quote_state: str
    volume: float | None
    financial_volume: float | None
    open_interest: int | None
    price_for_model: float | None
    price_basis: str | None
    intrinsic: float | None
    extrinsic: float | None
    iv: float | None
    greeks: Greeks | None


@dataclass(frozen=True)
class StrikeRow:
    strike: float
    call: OptionLegSnapshot | None
    put: OptionLegSnapshot | None


@dataclass(frozen=True)
class ExpirationChain:
    expiration: date
    days_to_expiration: int
    risk_free_rate: float
    rows: tuple[StrikeRow, ...]


@dataclass(frozen=True)
class OptionChain:
    ref_date: date
    underlying: str
    spot: float
    risk_free_rate: float
    dividend_yield: float
    expirations: tuple[ExpirationChain, ...]


def _to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _pricing_input(last: float | None, bid: float | None, ask: float | None) -> tuple[float | None, str | None]:
    if bid is not None and ask is not None and bid > 0 and ask >= bid:
        return (bid + ask) / 2.0, "MID"
    if last is not None and last > 0:
        return last, "LAST"
    return None, None


def _quote_state(
    last: float | None,
    bid: float | None,
    ask: float | None,
) -> tuple[str, float | None]:
    if bid is not None and ask is not None and bid > 0 and ask >= bid:
        mid = (bid + ask) / 2.0
        return "TWO_SIDED", ((ask - bid) / mid * 100.0 if mid > 0 else None)
    if (bid is not None and bid > 0) or (ask is not None and ask > 0):
        return "ONE_SIDED", None
    if last is not None and last > 0:
        return "LAST_ONLY", None
    return "NO_PRICE", None


def _analytics(
    contract: OptionContract,
    *,
    spot: float,
    ref_date: date,
    option_price: float | None,
    risk_free_rate: float,
    dividend_yield: float,
    american_steps: int,
) -> tuple[float | None, float | None, float | None, Greeks | None]:
    if option_price is None or option_price <= 0:
        return None, None, None, None
    strike = float(contract.strike)
    intrinsic = intrinsic_value(spot, strike, contract.option_type)  # type: ignore[arg-type]
    extrinsic = max(option_price - intrinsic, 0.0)
    days = (contract.expiration - ref_date).days
    if days <= 0:
        return intrinsic, extrinsic, None, None
    t = days / 365.0

    try:
        if contract.exercise_style == "AMERICAN":
            def price_at_sigma(sigma: float) -> float:
                return crr_american_price(
                    spot,
                    strike,
                    t,
                    risk_free_rate,
                    sigma,
                    contract.option_type,  # type: ignore[arg-type]
                    dividend_yield,
                    steps=american_steps,
                )

            iv = implied_volatility(option_price, price_at_sigma)

            def model(s: float, tt: float, r: float, sigma: float) -> float:
                return crr_american_price(
                    s,
                    strike,
                    tt,
                    r,
                    sigma,
                    contract.option_type,  # type: ignore[arg-type]
                    dividend_yield,
                    steps=american_steps,
                )

            greeks = finite_difference_greeks(
                model,
                spot=spot,
                time_years=t,
                rate=risk_free_rate,
                volatility=iv,
            )
        else:
            def price_at_sigma(sigma: float) -> float:
                return black_scholes_merton_price(
                    spot,
                    strike,
                    t,
                    risk_free_rate,
                    sigma,
                    contract.option_type,  # type: ignore[arg-type]
                    dividend_yield,
                )

            iv = implied_volatility(option_price, price_at_sigma)
            greeks = black_scholes_merton_greeks(
                spot,
                strike,
                t,
                risk_free_rate,
                iv,
                contract.option_type,  # type: ignore[arg-type]
                dividend_yield,
            )
        return intrinsic, extrinsic, iv, greeks
    except (ValueError, OverflowError):
        # Invalid/stale market observations must not poison the full chain.
        return intrinsic, extrinsic, None, None


def build_option_chain(
    *,
    underlying: str,
    ref_date: date,
    instrument_rows: Iterable[dict[str, str]],
    trade_rows: Iterable[dict[str, str]],
    open_interest_rows: Iterable[dict[str, str]],
    cotahist_rows: Iterable[CotahistRecord] = (),
    risk_free_rate: float,
    risk_free_rate_by_expiration: Callable[[date], float] | None = None,
    dividend_yield: float = 0.0,
    american_steps: int = 250,
) -> OptionChain:
    """Join B3 reference/trade/OI data into a frontend-ready option chain.

    Pricing preference for IV/Greeks is MID when COTAHIST EOD bid/ask is valid,
    otherwise the regular-session last price.
    """
    underlying = underlying.strip().upper()
    trades: dict[str, DailyQuote] = {}
    for row in trade_rows:
        ticker = (row.get("TckrSymb") or "").strip().upper()
        if ticker:
            trades[ticker] = normalize_daily_quote(row)

    underlying_quote = trades.get(underlying)
    if underlying_quote is None or underlying_quote.last is None:
        raise ValueError(f"No last price for underlying {underlying} on {ref_date}")
    spot = float(underlying_quote.last)

    oi_index: dict[str, OpenInterest] = {}
    for row in open_interest_rows:
        ticker = (row.get("TckrSymb") or "").strip().upper()
        if ticker:
            oi_index[ticker] = normalize_open_interest(row)

    cotahist_index = {row.ticker.upper(): row for row in cotahist_rows}

    contracts: list[OptionContract] = []
    for row in instrument_rows:
        row_underlying = (
            row.get("Asst") or row.get("UndrlygTckrSymb1") or ""
        ).strip().upper()
        if row_underlying != underlying:
            continue
        try:
            contract = normalize_option_contract(row)
        except ValueError:
            continue
        if contract.expiration < ref_date:
            continue
        contracts.append(contract)

    grouped: dict[date, dict[float, dict[str, OptionLegSnapshot]]] = {}
    for contract in contracts:
        quote = trades.get(contract.ticker)
        hist = cotahist_index.get(contract.ticker)
        oi = oi_index.get(contract.ticker)

        last = _to_float(quote.last) if quote else None
        bid = float(hist.best_bid) if hist and hist.best_bid > 0 else None
        ask = float(hist.best_ask) if hist and hist.best_ask > 0 else None
        price_for_model, price_basis = _pricing_input(last, bid, ask)
        quote_state, spread_pct = _quote_state(last, bid, ask)
        contract_rate = (
            risk_free_rate_by_expiration(contract.expiration)
            if risk_free_rate_by_expiration is not None
            else risk_free_rate
        )
        intrinsic, extrinsic, iv, greeks = _analytics(
            contract,
            spot=spot,
            ref_date=ref_date,
            option_price=price_for_model,
            risk_free_rate=contract_rate,
            dividend_yield=dividend_yield,
            american_steps=american_steps,
        )
        leg = OptionLegSnapshot(
            ticker=contract.ticker,
            option_type=contract.option_type,
            exercise_style=contract.exercise_style,
            risk_free_rate=contract_rate,
            last=last,
            bid=bid,
            ask=ask,
            spread_pct=spread_pct,
            quote_state=quote_state,
            volume=_to_float(quote.quantity) if quote else None,
            financial_volume=_to_float(quote.financial_volume) if quote else None,
            open_interest=oi.open_interest if oi else None,
            price_for_model=price_for_model,
            price_basis=price_basis,
            intrinsic=intrinsic,
            extrinsic=extrinsic,
            iv=iv,
            greeks=greeks,
        )
        expiry_bucket = grouped.setdefault(contract.expiration, {})
        strike_bucket = expiry_bucket.setdefault(float(contract.strike), {})
        strike_bucket[contract.option_type] = leg

    expirations: list[ExpirationChain] = []
    for expiry in sorted(grouped):
        expiry_rate = (
            risk_free_rate_by_expiration(expiry)
            if risk_free_rate_by_expiration is not None
            else risk_free_rate
        )
        rows = tuple(
            StrikeRow(
                strike=strike,
                call=grouped[expiry][strike].get("CALL"),
                put=grouped[expiry][strike].get("PUT"),
            )
            for strike in sorted(grouped[expiry])
        )
        expirations.append(
            ExpirationChain(
                expiration=expiry,
                days_to_expiration=(expiry - ref_date).days,
                risk_free_rate=expiry_rate,
                rows=rows,
            )
        )

    return OptionChain(
        ref_date=ref_date,
        underlying=underlying,
        spot=spot,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        expirations=tuple(expirations),
    )
