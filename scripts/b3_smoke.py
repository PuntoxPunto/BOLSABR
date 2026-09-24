from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from bolsabr.b3.corporate_actions import get_cash_distributions_for_isin
from bolsabr.pipelines.eod_options import fetch_eod_option_chains

UNDERLYING = "PETR4"
BENCHMARK_TICKERS = {"PETRV483", "PETRK442", "PETRL56"}


def _sample_chain(chain, max_strikes: int = 7) -> list[dict]:
    """Return ATM-centered rows so the smoke artifact is benchmark-friendly."""
    output: list[dict] = []
    for expiration in chain.expirations[:5]:
        nearest = sorted(
            expiration.rows,
            key=lambda row: abs(row.strike - chain.spot),
        )[:max_strikes]
        rows = []
        for row in sorted(nearest, key=lambda row: row.strike):
            rows.append(
                {
                    "strike": row.strike,
                    "call": None
                    if row.call is None
                    else {
                        "ticker": row.call.ticker,
                        "pricing_model": row.call.pricing_model,
                        "last": row.call.last,
                        "bid": row.call.bid,
                        "ask": row.call.ask,
                        "spread_pct": row.call.spread_pct,
                        "quote_state": row.call.quote_state,
                        "quality_flags": list(row.call.quality_flags),
                        "trade_count": row.call.trade_count,
                        "oi": row.call.open_interest,
                        "price_basis": row.call.price_basis,
                        "price_for_model": row.call.price_for_model,
                        "iv": row.call.iv,
                        "delta": row.call.greeks.delta if row.call.greeks else None,
                    },
                    "put": None
                    if row.put is None
                    else {
                        "ticker": row.put.ticker,
                        "pricing_model": row.put.pricing_model,
                        "last": row.put.last,
                        "bid": row.put.bid,
                        "ask": row.put.ask,
                        "spread_pct": row.put.spread_pct,
                        "quote_state": row.put.quote_state,
                        "quality_flags": list(row.put.quality_flags),
                        "trade_count": row.put.trade_count,
                        "oi": row.put.open_interest,
                        "price_basis": row.put.price_basis,
                        "price_for_model": row.put.price_for_model,
                        "iv": row.put.iv,
                        "delta": row.put.greeks.delta if row.put.greeks else None,
                    },
                }
            )
        output.append(
            {
                "expiration": expiration.expiration.isoformat(),
                "days_to_expiration": expiration.days_to_expiration,
                "risk_free_rate": expiration.risk_free_rate,
                "rows": rows,
            }
        )
    return output


def _benchmark_contracts(chain) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for expiration in chain.expirations:
        for row in expiration.rows:
            for leg in (row.call, row.put):
                if leg is None or leg.ticker not in BENCHMARK_TICKERS:
                    continue
                found[leg.ticker] = {
                    "expiration": expiration.expiration.isoformat(),
                    "days_to_expiration": expiration.days_to_expiration,
                    "strike": row.strike,
                    "type": leg.option_type,
                    "exercise_style": leg.exercise_style,
                    "risk_free_rate": leg.risk_free_rate,
                    "pricing_model": leg.pricing_model,
                    "last": leg.last,
                    "bid": leg.bid,
                    "ask": leg.ask,
                    "spread_pct": leg.spread_pct,
                    "quote_state": leg.quote_state,
                    "quality_flags": list(leg.quality_flags),
                    "trade_count": leg.trade_count,
                    "oi": leg.open_interest,
                    "price_basis": leg.price_basis,
                    "price_for_model": leg.price_for_model,
                    "intrinsic": leg.intrinsic,
                    "extrinsic": leg.extrinsic,
                    "iv": leg.iv,
                    "delta": leg.greeks.delta if leg.greeks else None,
                    "gamma": leg.greeks.gamma if leg.greeks else None,
                    "theta": leg.greeks.theta if leg.greeks else None,
                    "vega": leg.greeks.vega if leg.greeks else None,
                    "rho": leg.greeks.rho if leg.greeks else None,
                }
    return found


def main() -> int:
    batch = fetch_eod_option_chains([UNDERLYING])
    result = batch.chains.get(UNDERLYING)
    if result is None:
        raise RuntimeError(
            f"No {UNDERLYING} Option Chain generated: {batch.warnings}"
        )

    chain = result.chain
    report: dict = {
        "run_date": date.today().isoformat(),
        "underlying": UNDERLYING,
        "datasets": {
            name: {
                "ref_date": info.ref_date.isoformat(),
                "status": info.status,
                "rows": info.row_count,
                "columns": info.column_count,
            }
            for name, info in batch.datasets.items()
        },
        "warnings": list(batch.warnings),
        "di1": {
            "point_count": len(batch.di1_points),
            "sample": [
                {
                    "ticker": point.ticker,
                    "expiration": point.expiration.isoformat(),
                    "adjusted_quote": (
                        str(point.adjusted_quote)
                        if point.adjusted_quote is not None
                        else None
                    ),
                    "adjusted_rate_pct": str(point.adjusted_rate_pct),
                }
                for point in batch.di1_points[:12]
            ],
        },
        "fallback_rate": {
            "source": batch.fallback_rate_source,
            "continuous_annual_rate": batch.fallback_risk_free_rate,
        },
        "cotahist": {
            "ref_date": result.ref_date.isoformat(),
            "records": result.cotahist_row_count,
            "valid_bid_ask_records": result.valid_bid_ask_count,
            "coverage_pct": (
                round(
                    result.valid_bid_ask_count
                    / result.option_instrument_count
                    * 100.0,
                    2,
                )
                if result.option_instrument_count
                else 0.0
            ),
        },
    }

    try:
        underlying_isin = result.underlying_isin
        if not underlying_isin:
            raise RuntimeError(f"{UNDERLYING} ISIN missing from B3 trade snapshot")

        distributions = get_cash_distributions_for_isin(
            UNDERLYING[:4],
            underlying_isin,
        )
        future_rights = [
            item
            for item in distributions
            if item.last_date_with_rights is not None
            and item.last_date_with_rights >= result.ref_date
        ]
        upcoming_payments = [
            item
            for item in distributions
            if item.payment_date is not None
            and item.payment_date >= result.ref_date
        ]
        report["corporate_actions"] = {
            "isin": underlying_isin,
            "count": len(distributions),
            "raw_keys": (
                sorted(distributions[0].raw.keys())
                if distributions
                else []
            ),
            "future_rights": [
                {
                    "action": item.corporate_action,
                    "approval_date": (
                        item.approval_date.isoformat()
                        if item.approval_date
                        else None
                    ),
                    "last_date_with_rights": (
                        item.last_date_with_rights.isoformat()
                        if item.last_date_with_rights
                        else None
                    ),
                    "ex_date": item.ex_date.isoformat() if item.ex_date else None,
                    "payment_date": (
                        item.payment_date.isoformat()
                        if item.payment_date
                        else None
                    ),
                    "value_cash": (
                        str(item.value_cash)
                        if item.value_cash is not None
                        else None
                    ),
                    "isin": item.isin,
                }
                for item in future_rights[:20]
            ],
            "upcoming_payments": [
                {
                    "action": item.corporate_action,
                    "last_date_with_rights": (
                        item.last_date_with_rights.isoformat()
                        if item.last_date_with_rights
                        else None
                    ),
                    "ex_date": item.ex_date.isoformat() if item.ex_date else None,
                    "payment_date": (
                        item.payment_date.isoformat()
                        if item.payment_date
                        else None
                    ),
                    "value_cash": (
                        str(item.value_cash)
                        if item.value_cash is not None
                        else None
                    ),
                    "isin": item.isin,
                }
                for item in upcoming_payments[:20]
            ],
        }
    except Exception as exc:
        report["warnings"].append(
            f"B3 corporate actions unavailable: {type(exc).__name__}: {exc}"
        )

    report["petr4"] = {
        "instrument_rows": result.option_instrument_count,
        "trade_rows": result.trade_row_count,
        "open_interest_rows": result.open_interest_row_count,
        "cotahist_rows": result.cotahist_row_count,
        "spot": chain.spot,
        "expiration_count": len(chain.expirations),
        "strike_row_count": sum(
            len(expiration.rows)
            for expiration in chain.expirations
        ),
        "sample": _sample_chain(chain),
        "benchmark_contracts": _benchmark_contracts(chain),
    }

    out_dir = Path("artifacts")
    out_dir.mkdir(exist_ok=True)

    chain_path = out_dir / "petr4-option-chain-v0.json"
    chain_path.write_text(
        json.dumps(result.payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    report["api_output"] = {
        "schema_version": result.payload["schema_version"],
        "path": str(chain_path),
        "expiration_count": len(result.payload["expirations"]),
    }

    report_path = out_dir / "b3-petr4-smoke.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(report["datasets"], indent=2, ensure_ascii=False))
    print(
        f"{UNDERLYING}: {result.option_instrument_count} instruments, "
        f"{len(chain.expirations)} expirations, "
        f"{report['petr4']['strike_row_count']} strike rows; "
        f"spot={chain.spot}; cotahist={result.cotahist_row_count}"
    )
    print(f"Report: {report_path}")
    print(f"Option Chain API: {chain_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"B3 live smoke failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise
