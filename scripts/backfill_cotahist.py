from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from bolsabr.b3.cotahist import download_cotahist_annual
from bolsabr.backfill.cotahist import build_cotahist_backfill_points
from bolsabr.serving.snapshot_store import FilesystemSnapshotStore


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill registered option contracts from annual B3 COTAHIST."
    )
    parser.add_argument(
        "year",
        type=int,
        help="COTAHIST annual series year.",
    )
    parser.add_argument(
        "underlyings",
        nargs="+",
        help="Published underlyings, e.g. PETR4 VALE3.",
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=Path("data/serving"),
        help="Serving store root.",
    )
    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        default=None,
        help="Optional YYYY-MM-DD lower bound.",
    )
    parser.add_argument(
        "--end",
        type=date.fromisoformat,
        default=None,
        help="Optional YYYY-MM-DD upper bound.",
    )
    args = parser.parse_args()

    store = FilesystemSnapshotStore(args.snapshot_dir)
    underlyings = tuple(
        dict.fromkeys(
            item.strip().upper()
            for item in args.underlyings
            if item.strip()
        )
    )
    if not underlyings:
        raise ValueError("at least one underlying is required")

    contracts_by_underlying: dict[str, tuple[dict, ...]] = {}
    wanted: set[str] = set(underlyings)

    for underlying in underlyings:
        contracts = store.list_contracts(underlying=underlying)
        if not contracts:
            raise RuntimeError(
                f"no registered contracts for {underlying}; publish a snapshot first"
            )
        contracts_by_underlying[underlying] = contracts
        wanted.update(
            str(item["ticker"]).strip().upper()
            for item in contracts
        )

    records = download_cotahist_annual(
        args.year,
        tickers=wanted,
        start=args.start,
        end=args.end,
    )

    summary: dict[str, object] = {
        "year": args.year,
        "start": args.start.isoformat() if args.start else None,
        "end": args.end.isoformat() if args.end else None,
        "record_count": len(records),
        "underlyings": {},
    }

    underlying_summary: dict[str, object] = {}
    for underlying in underlyings:
        projected = build_cotahist_backfill_points(
            underlying=underlying,
            contracts=contracts_by_underlying[underlying],
            records=records,
        )

        contract_counts: dict[str, int] = {}
        for contract, points in projected.items():
            if not points:
                continue
            store.publish_cotahist_backfill(
                underlying=underlying,
                contract=contract,
                year=args.year,
                points=points,
            )
            contract_counts[contract] = len(points)

        underlying_summary[underlying] = {
            "registered_contracts": len(
                contracts_by_underlying[underlying]
            ),
            "backfilled_contracts": len(contract_counts),
            "backfilled_points": sum(contract_counts.values()),
            "contracts": contract_counts,
        }

    summary["underlyings"] = underlying_summary
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
