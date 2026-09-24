from __future__ import annotations

import argparse
import json
from pathlib import Path

from bolsabr.pipelines.eod_options import (
    fetch_eod_option_chains,
    normalize_underlyings,
)
from bolsabr.serving.snapshot_store import FilesystemSnapshotStore


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build one or more B3 EOD Option Chain API snapshots."
    )
    parser.add_argument(
        "underlyings",
        nargs="+",
        help="B3 underlying tickers, e.g. PETR4 VALE3 ITUB4",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/chains"),
        help="Directory for generated JSON files.",
    )
    parser.add_argument(
        "--publish-dir",
        type=Path,
        default=None,
        help="Optional serving snapshot root to publish generated chains.",
    )
    parser.add_argument(
        "--no-cotahist",
        action="store_true",
        help="Skip COTAHIST enrichment and use LAST-only fallback.",
    )
    args = parser.parse_args()

    underlyings = normalize_underlyings(args.underlyings)
    batch = fetch_eod_option_chains(
        underlyings,
        include_cotahist=not args.no_cotahist,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    store = (
        FilesystemSnapshotStore(args.publish_dir)
        if args.publish_dir is not None
        else None
    )

    generated: list[dict[str, object]] = []
    for ticker in underlyings:
        result = batch.chains.get(ticker)
        if result is None:
            continue

        output = args.output_dir / f"{ticker.lower()}-option-chain-v0.json"
        output.write_text(
            json.dumps(result.payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        published_path = None
        if store is not None:
            published = store.publish(result.payload)
            published_path = str(published.path)

        generated.append(
            {
                "ticker": ticker,
                "ref_date": result.ref_date.isoformat(),
                "spot": result.chain.spot,
                "contracts": result.option_instrument_count,
                "expirations": len(result.chain.expirations),
                "strike_rows": sum(
                    len(expiration.rows)
                    for expiration in result.chain.expirations
                ),
                "cotahist_rows": result.cotahist_row_count,
                "valid_bid_ask": result.valid_bid_ask_count,
                "output": str(output),
                "published": published_path,
            }
        )

    summary = {
        "ref_date": batch.ref_date.isoformat(),
        "requested": list(underlyings),
        "generated": generated,
        "di1_points": len(batch.di1_points),
        "fallback_rate_source": batch.fallback_rate_source,
        "warnings": list(batch.warnings),
    }
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    missing = [
        ticker
        for ticker in underlyings
        if ticker not in batch.chains
    ]
    if missing:
        raise RuntimeError(
            "No EOD Option Chain generated for: " + ", ".join(missing)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
