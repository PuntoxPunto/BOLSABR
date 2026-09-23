from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

from bolsabr.b3.client import latest_final
from bolsabr.bcb.sgs import SELIC_DAILY_SERIES, fetch_series, selic_daily_to_continuous_annual
from bolsabr.chain import build_option_chain

UNDERLYING = "PETR4"


def _sample_chain(chain, max_strikes: int = 7) -> list[dict]:
    output: list[dict] = []
    for expiration in chain.expirations[:3]:
        rows = []
        for row in expiration.rows[:max_strikes]:
            rows.append(
                {
                    "strike": row.strike,
                    "call": None
                    if row.call is None
                    else {
                        "ticker": row.call.ticker,
                        "last": row.call.last,
                        "oi": row.call.open_interest,
                        "price_basis": row.call.price_basis,
                        "iv": row.call.iv,
                        "delta": row.call.greeks.delta if row.call.greeks else None,
                    },
                    "put": None
                    if row.put is None
                    else {
                        "ticker": row.put.ticker,
                        "last": row.put.last,
                        "oi": row.put.open_interest,
                        "price_basis": row.put.price_basis,
                        "iv": row.put.iv,
                        "delta": row.put.greeks.delta if row.put.greeks else None,
                    },
                }
            )
        output.append(
            {
                "expiration": expiration.expiration.isoformat(),
                "days_to_expiration": expiration.days_to_expiration,
                "rows": rows,
            }
        )
    return output


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
        if (row.get("UndrlygTckrSymb1") or "").strip().upper() == UNDERLYING
    ]
    option_tickers = {
        (row.get("TckrSymb") or "").strip().upper()
        for row in option_rows
        if (row.get("TckrSymb") or "").strip()
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
        raise RuntimeError("No PETR4 option instruments found in B3 InstrumentsConsolidated")
    if not any((row.get("TckrSymb") or "").strip().upper() == UNDERLYING for row in trade_rows):
        raise RuntimeError("No PETR4 underlying quote found in TradeInformationConsolidated")

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
        risk_free_rate=risk_free_rate,
    )

    report["petr4"] = {
        "instrument_rows": len(option_rows),
        "trade_rows": len(trade_rows),
        "open_interest_rows": len(oi_rows),
        "spot": chain.spot,
        "expiration_count": len(chain.expirations),
        "strike_row_count": sum(len(exp.rows) for exp in chain.expirations),
        "sample": _sample_chain(chain),
    }

    out_dir = Path("artifacts")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "b3-petr4-smoke.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report["datasets"], indent=2, ensure_ascii=False))
    print(
        f"PETR4: {len(option_rows)} instruments, {len(chain.expirations)} expirations, "
        f"{report['petr4']['strike_row_count']} strike rows; spot={chain.spot}"
    )
    print(f"Report: {out_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"B3 live smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
