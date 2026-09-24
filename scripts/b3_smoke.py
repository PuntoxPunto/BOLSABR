from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

from bolsabr.b3.client import latest_final
from bolsabr.b3.cotahist import download_cotahist_daily
from bolsabr.b3.corporate_actions import get_cash_distributions_for_isin
from bolsabr.b3.di1 import Di1DiscountCurve, build_di1_points
from bolsabr.bcb.sgs import SELIC_DAILY_SERIES, fetch_series, selic_daily_to_continuous_annual
from bolsabr.chain import build_option_chain

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
    report: dict = {
        "run_date": date.today().isoformat(),
        "underlying": UNDERLYING,
        "datasets": {},
        "warnings": [],
    }

    snapshots = {}
    for table in ("instruments", "trades", "derivatives"):
        ref_date, dataset = latest_final(table, lookback_days=10)
        snapshots[table] = (ref_date, dataset)
        report["datasets"][table] = {
            "ref_date": ref_date.isoformat(),
            "status": dataset.status or "N/A",
            "rows": len(dataset.rows),
            "columns": len(dataset.columns),
            "column_sample": list(dataset.columns[:12]),
        }

    trade_ref_date = snapshots["trades"][0]
    instruments = snapshots["instruments"][1].rows
    trades = snapshots["trades"][1].rows
    derivatives = snapshots["derivatives"][1].rows

    option_rows = [
        row
        for row in instruments
        if (row.get("Asst") or row.get("UndrlygTckrSymb1") or "").strip().upper() == UNDERLYING
        and (row.get("SgmtNm") or "").strip().upper() in {"EQUITY CALL", "EQUITY PUT"}
    ]

    # Preserve real schema evidence when our assumed filter does not match B3.
    instrument_columns = snapshots["instruments"][1].columns
    relevant_columns = [
        col
        for col in instrument_columns
        if any(
            token in col.lower()
            for token in ("tckr", "undr", "optn", "exrc", "xprt", "sgmt", "asst", "scty", "spcf")
        )
    ]
    petr_candidates = [
        {col: row.get(col, "") for col in relevant_columns}
        for row in instruments
        if (row.get("TckrSymb") or "").strip().upper().startswith("PETR")
    ][:40]
    report["instrument_diagnostic"] = {
        "relevant_columns": relevant_columns,
        "petr_candidates": petr_candidates,
    }
    option_tickers = {
        (row.get("TckrSymb") or "").strip().upper()
        for row in option_rows
        if (row.get("TckrSymb") or "").strip()
    }

    di1_points = build_di1_points(
        instruments,
        trades,
        ref_date=trade_ref_date,
    )
    di1_curve = Di1DiscountCurve(trade_ref_date, di1_points) if di1_points else None
    report["di1"] = {
        "point_count": len(di1_points),
        "sample": [
            {
                "ticker": point.ticker,
                "expiration": point.expiration.isoformat(),
                "adjusted_quote": str(point.adjusted_quote) if point.adjusted_quote is not None else None,
                "adjusted_rate_pct": str(point.adjusted_rate_pct),
            }
            for point in di1_points[:12]
        ],
    }

    trade_rows = [
        row
        for row in trades
        if (row.get("TckrSymb") or "").strip().upper() in option_tickers | {UNDERLYING}
    ]
    oi_rows = [
        row
        for row in derivatives
        if (row.get("TckrSymb") or "").strip().upper() in option_tickers
    ]

    if not option_rows:
        out_dir = Path("artifacts")
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / "b3-petr4-smoke.json"
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(report["instrument_diagnostic"], indent=2, ensure_ascii=False))
        raise RuntimeError("No PETR4 equity option instruments found with Asst == PETR4")
    if not any((row.get("TckrSymb") or "").strip().upper() == UNDERLYING for row in trade_rows):
        raise RuntimeError("No PETR4 underlying quote found in TradeInformationConsolidated")

    cotahist_rows = ()
    try:
        cotahist_rows = download_cotahist_daily(
            trade_ref_date,
            tickers=option_tickers | {UNDERLYING},
        )
        valid_bid_ask = sum(
            1 for row in cotahist_rows if row.best_bid > 0 and row.best_ask >= row.best_bid
        )
        report["cotahist"] = {
            "ref_date": trade_ref_date.isoformat(),
            "records": len(cotahist_rows),
            "valid_bid_ask_records": valid_bid_ask,
            "coverage_pct": (
                round(valid_bid_ask / len(option_tickers) * 100.0, 2)
                if option_tickers
                else 0.0
            ),
        }
    except Exception as exc:
        report["warnings"].append(
            f"COTAHIST unavailable: {type(exc).__name__}: {exc}; chain will use LAST"
        )

    try:
        underlying_row = next(
            row
            for row in trade_rows
            if (row.get("TckrSymb") or "").strip().upper() == UNDERLYING
        )
        underlying_isin = (underlying_row.get("ISIN") or "").strip().upper()
        if not underlying_isin:
            raise RuntimeError("PETR4 ISIN missing from B3 trade snapshot")
        distributions = get_cash_distributions_for_isin("PETR", underlying_isin)
        future_rights = [
            item for item in distributions
            if item.last_date_with_rights is not None
            and item.last_date_with_rights >= trade_ref_date
        ]
        upcoming_payments = [
            item for item in distributions
            if item.payment_date is not None
            and item.payment_date >= trade_ref_date
        ]
        report["corporate_actions"] = {
            "isin": underlying_isin,
            "count": len(distributions),
            "raw_keys": sorted(distributions[0].raw.keys()) if distributions else [],
            "future_rights": [
                {
                    "action": item.corporate_action,
                    "approval_date": item.approval_date.isoformat() if item.approval_date else None,
                    "last_date_with_rights": (
                        item.last_date_with_rights.isoformat()
                        if item.last_date_with_rights else None
                    ),
                    "ex_date": item.ex_date.isoformat() if item.ex_date else None,
                    "payment_date": item.payment_date.isoformat() if item.payment_date else None,
                    "value_cash": str(item.value_cash) if item.value_cash is not None else None,
                    "isin": item.isin,
                }
                for item in future_rights[:20]
            ],
            "upcoming_payments": [
                {
                    "action": item.corporate_action,
                    "last_date_with_rights": (
                        item.last_date_with_rights.isoformat()
                        if item.last_date_with_rights else None
                    ),
                    "ex_date": item.ex_date.isoformat() if item.ex_date else None,
                    "payment_date": item.payment_date.isoformat() if item.payment_date else None,
                    "value_cash": str(item.value_cash) if item.value_cash is not None else None,
                    "isin": item.isin,
                }
                for item in upcoming_payments[:20]
            ],
        }
    except Exception as exc:
        report["warnings"].append(
            f"B3 corporate actions unavailable: {type(exc).__name__}: {exc}"
        )

    risk_free_rate = 0.15
    try:
        points = fetch_series(
            SELIC_DAILY_SERIES,
            trade_ref_date - timedelta(days=14),
            trade_ref_date,
        )
        if points:
            latest = points[-1]
            risk_free_rate = selic_daily_to_continuous_annual(latest.value)
            report["selic"] = {
                "series": SELIC_DAILY_SERIES,
                "date": latest.date.isoformat(),
                "daily_percent": latest.value,
                "continuous_annual_rate": risk_free_rate,
            }
        else:
            report["warnings"].append("BCB SGS returned no Selic points; using 15% fallback")
    except Exception as exc:  # smoke report should preserve B3 result even if BCB is unavailable
        report["warnings"].append(f"BCB SGS unavailable: {type(exc).__name__}: {exc}; using 15% fallback")

    chain = build_option_chain(
        underlying=UNDERLYING,
        ref_date=trade_ref_date,
        instrument_rows=option_rows,
        trade_rows=trade_rows,
        open_interest_rows=oi_rows,
        cotahist_rows=cotahist_rows,
        risk_free_rate=risk_free_rate,
        risk_free_rate_by_expiration=(
            di1_curve.continuous_rate if di1_curve is not None else None
        ),
    )

    report["petr4"] = {
        "instrument_rows": len(option_rows),
        "trade_rows": len(trade_rows),
        "open_interest_rows": len(oi_rows),
        "cotahist_rows": len(cotahist_rows),
        "spot": chain.spot,
        "expiration_count": len(chain.expirations),
        "strike_row_count": sum(len(exp.rows) for exp in chain.expirations),
        "sample": _sample_chain(chain),
        "benchmark_contracts": _benchmark_contracts(chain),
    }

    out_dir = Path("artifacts")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "b3-petr4-smoke.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report["datasets"], indent=2, ensure_ascii=False))
    print(
        f"PETR4: {len(option_rows)} instruments, {len(chain.expirations)} expirations, "
        f"{report['petr4']['strike_row_count']} strike rows; spot={chain.spot}; "
        f"cotahist={len(cotahist_rows)}"
    )
    print(f"Report: {out_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"B3 live smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
