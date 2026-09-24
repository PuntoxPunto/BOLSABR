from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal
from typing import Any

from bolsabr.b3.cotahist import CotahistRecord


def _positive(value: Decimal) -> float | None:
    return float(value) if value > 0 else None


def _quote_quality(
    record: CotahistRecord,
) -> tuple[str, float | None, list[str]]:
    bid = _positive(record.best_bid)
    ask = _positive(record.best_ask)
    last = _positive(record.last)

    flags: list[str] = []

    if bid is not None and ask is not None and ask >= bid:
        mid = (bid + ask) / 2.0
        spread_pct = ((ask - bid) / mid * 100.0) if mid > 0 else None
        state = "TWO_SIDED"
        if spread_pct is not None and spread_pct > 30.0:
            flags.append("WIDE_SPREAD_GT_30PCT")
    elif bid is not None or ask is not None:
        state = "ONE_SIDED"
        spread_pct = None
        flags.append("ONE_SIDED")
    elif last is not None:
        state = "LAST_ONLY"
        spread_pct = None
        flags.append("LAST_ONLY")
    else:
        state = "NO_PRICE"
        spread_pct = None
        flags.append("NO_PRICE")

    if record.trades <= 0:
        flags.append("NO_TRADES")

    return state, spread_pct, flags


def _contract_map(
    contracts: Iterable[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for contract in contracts:
        ticker = str(contract.get("ticker") or "").strip().upper()
        if ticker:
            result[ticker] = contract
    return result


def _expected_bdi(option_type: str | None) -> str | None:
    normalized = str(option_type or "").strip().upper()
    if normalized == "CALL":
        return "78"
    if normalized == "PUT":
        return "82"
    return None


def _matches_contract(
    record: CotahistRecord,
    contract: Mapping[str, Any],
) -> bool:
    expected_bdi = _expected_bdi(
        str(contract.get("type") or "")
    )
    if expected_bdi is not None and record.bdi_code != expected_bdi:
        return False

    raw_expiration = contract.get("expiration")
    if raw_expiration:
        try:
            expected_expiration = date.fromisoformat(
                str(raw_expiration)
            )
        except ValueError:
            return False
        if record.expiration != expected_expiration:
            return False

    raw_strike = contract.get("strike")
    if raw_strike is not None:
        try:
            expected_strike = Decimal(str(raw_strike))
        except Exception:
            return False
        if abs(record.exercise_price - expected_strike) > Decimal("0.011"):
            return False

    return True


def build_cotahist_backfill_points(
    *,
    underlying: str,
    contracts: Iterable[Mapping[str, Any]],
    records: Iterable[CotahistRecord],
) -> dict[str, list[dict[str, Any]]]:
    """Project official COTAHIST records into market-only history points.

    Analytics fields unavailable from COTAHIST alone remain null. Contract
    metadata from the persistent registry is used to reject ticker reuse with
    a different type, strike or expiration.
    """
    normalized_underlying = underlying.strip().upper()
    contract_by_ticker = _contract_map(contracts)
    if not contract_by_ticker:
        return {}

    records_tuple = tuple(records)

    underlying_by_date: dict[date, CotahistRecord] = {}
    for record in records_tuple:
        if record.ticker.strip().upper() != normalized_underlying:
            continue
        existing = underlying_by_date.get(record.trade_date)
        # Prefer standard-lot BDI 02 when the exact ticker appears more than once.
        if existing is None or (
            record.bdi_code == "02"
            and existing.bdi_code != "02"
        ):
            underlying_by_date[record.trade_date] = record

    result: dict[str, list[dict[str, Any]]] = {
        ticker: []
        for ticker in contract_by_ticker
    }

    for record in records_tuple:
        ticker = record.ticker.strip().upper()
        contract = contract_by_ticker.get(ticker)
        if contract is None:
            continue
        if not _matches_contract(record, contract):
            continue

        quote_state, spread_pct, flags = _quote_quality(record)
        underlying_record = underlying_by_date.get(record.trade_date)

        result[ticker].append(
            {
                "ref_date": record.trade_date.isoformat(),
                "source": "B3_COTAHIST_BACKFILL",
                "underlying_spot": (
                    _positive(underlying_record.last)
                    if underlying_record is not None
                    else None
                ),
                "last": _positive(record.last),
                "bid": _positive(record.best_bid),
                "ask": _positive(record.best_ask),
                "spread_pct": spread_pct,
                "quote_state": quote_state,
                "quality_flags": flags,
                "trade_count": record.trades,
                "volume": record.quantity,
                "financial_volume": float(record.financial_volume),
                "open_interest": None,
                "price_for_model": None,
                "price_basis": None,
                "risk_free_rate": None,
                "iv": None,
                "delta": None,
                "gamma": None,
                "theta": None,
                "vega": None,
                "rho": None,
                "intrinsic": None,
                "extrinsic": None,
            }
        )

    for ticker, points in result.items():
        result[ticker] = sorted(
            points,
            key=lambda point: point["ref_date"],
        )

    return result
