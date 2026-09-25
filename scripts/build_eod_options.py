from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from bolsabr.pipelines.eod_options import (
    build_eod_option_batch,
    fetch_eod_market_data,
    normalize_underlyings,
)
from bolsabr.pipelines.option_universe import (
    discover_option_universe,
    select_option_universe,
)
from bolsabr.serving.snapshot_store import FilesystemSnapshotStore


def _decimal_arg(value: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(
            f"invalid decimal: {value!r}"
        ) from exc
    if result < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build one or more B3 EOD Option Chain API snapshots "
            "from a single shared market-data download."
        )
    )
    parser.add_argument(
        "underlyings",
        nargs="*",
        help="Manual B3 underlying tickers, e.g. PETR4 VALE3 ITUB4",
    )
    parser.add_argument(
        "--auto-universe",
        action="store_true",
        help=(
            "Discover equity-option underlyings from the same B3 snapshot "
            "and select them by transparent option activity metrics."
        ),
    )
    parser.add_argument(
        "--universe-limit",
        type=int,
        default=20,
        help="Maximum underlyings in auto mode. Default: 20.",
    )
    parser.add_argument(
        "--universe-kind",
        choices=("stocks", "all"),
        default="stocks",
        help=(
            "Asset class in auto mode. 'stocks' accepts B3/CFI common "
            "and preferred shares (ES/EP); 'all' keeps every discovered "
            "option underlying. Default: stocks."
        ),
    )
    parser.add_argument(
        "--min-financial-volume",
        type=_decimal_arg,
        default=Decimal("0"),
        help=(
            "Minimum aggregate option financial volume in auto mode. "
            "Default: 0."
        ),
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

    if args.auto_universe and args.underlyings:
        parser.error(
            "manual underlyings cannot be combined with --auto-universe"
        )
    if not args.auto_universe and not args.underlyings:
        parser.error(
            "provide underlyings or use --auto-universe"
        )
    if args.universe_limit < 1:
        parser.error("--universe-limit must be >= 1")

    # Common B3/BCB tables and DI1 are downloaded once. The same rows power
    # universe discovery and all selected chain builds.
    market = fetch_eod_market_data()

    universe_report: dict[str, object] | None = None
    if args.auto_universe:
        discovered = discover_option_universe(
            instrument_rows=market.instruments,
            trade_rows=market.trades,
            open_interest_rows=market.derivatives,
        )
        selected = select_option_universe(
            discovered,
            limit=args.universe_limit,
            min_financial_volume=args.min_financial_volume,
            asset_classes=(
                {"STOCK"}
                if args.universe_kind == "stocks"
                else None
            ),
        )
        underlyings = tuple(
            entry.underlying
            for entry in selected
        )
        if not underlyings:
            raise RuntimeError(
                "auto universe selection returned no underlyings"
            )

        universe_report = {
            "mode": "auto",
            "ranking": [
                "option_financial_volume_desc",
                "traded_contracts_desc",
                "open_interest_desc",
                "ticker_asc",
            ],
            "discovered_count": len(discovered),
            "selected_count": len(selected),
            "limit": args.universe_limit,
            "universe_kind": args.universe_kind,
            "asset_classes": (
                ["STOCK"]
                if args.universe_kind == "stocks"
                else None
            ),
            "min_financial_volume": str(
                args.min_financial_volume
            ),
            "selected": [
                {
                    "rank": index,
                    **entry.as_dict(),
                }
                for index, entry in enumerate(selected, start=1)
            ],
            "all_discovered": [
                {
                    "rank": index,
                    **entry.as_dict(),
                }
                for index, entry in enumerate(discovered, start=1)
            ],
        }
    else:
        underlyings = normalize_underlyings(args.underlyings)
        universe_report = {
            "mode": "manual",
            "selected_count": len(underlyings),
            "selected": list(underlyings),
        }

    batch = build_eod_option_batch(
        market,
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

        output = (
            args.output_dir
            / f"{ticker.lower()}-option-chain-v0.json"
        )
        output.write_text(
            json.dumps(
                result.payload,
                ensure_ascii=False,
                indent=2,
            ),
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

    universe_path = args.output_dir / "universe.json"
    universe_path.write_text(
        json.dumps(
            {
                "ref_date": market.ref_date.isoformat(),
                **(universe_report or {}),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    summary = {
        "ref_date": batch.ref_date.isoformat(),
        "requested": list(underlyings),
        "generated": generated,
        "di1_points": len(batch.di1_points),
        "fallback_rate_source": batch.fallback_rate_source,
        "warnings": list(batch.warnings),
        "universe_report": str(universe_path),
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
            "No EOD Option Chain generated for: "
            + ", ".join(missing)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
