from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from bolsabr.pipelines.eod_options import fetch_eod_market_data
from bolsabr.pipelines.option_universe import (
    discover_option_universe,
    select_option_universe,
)


def _decimal_arg(value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(
            f"invalid decimal: {value!r}"
        ) from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Discover B3 equity-option underlyings and rank them "
            "by transparent option-activity metrics."
        )
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of ranked entries to select. Default: 50.",
    )
    parser.add_argument(
        "--min-financial-volume",
        type=_decimal_arg,
        default=Decimal("0"),
        help="Minimum aggregate option financial volume.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/universe.json"),
        help="JSON report destination.",
    )
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be >= 1")

    market = fetch_eod_market_data()
    discovered = discover_option_universe(
        instrument_rows=market.instruments,
        trade_rows=market.trades,
        open_interest_rows=market.derivatives,
    )
    selected = select_option_universe(
        discovered,
        limit=args.limit,
        min_financial_volume=args.min_financial_volume,
    )

    payload = {
        "ref_date": market.ref_date.isoformat(),
        "ranking": [
            "option_financial_volume_desc",
            "traded_contracts_desc",
            "open_interest_desc",
            "ticker_asc",
        ],
        "discovered_count": len(discovered),
        "selected_count": len(selected),
        "limit": args.limit,
        "min_financial_volume": str(args.min_financial_volume),
        "selected": [
            {
                "rank": rank,
                **entry.as_dict(),
            }
            for rank, entry in enumerate(selected, start=1)
        ],
        "all_discovered": [
            {
                "rank": rank,
                **entry.as_dict(),
            }
            for rank, entry in enumerate(discovered, start=1)
        ],
        "datasets": {
            name: {
                "ref_date": info.ref_date.isoformat(),
                "status": info.status,
                "row_count": info.row_count,
                "column_count": info.column_count,
            }
            for name, info in market.datasets.items()
        },
        "warnings": list(market.warnings),
    }

    output = json.dumps(payload, indent=2, ensure_ascii=False)
    print(output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
