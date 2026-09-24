from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

from bolsabr.pipelines.eod_options import fetch_eod_market_data
from bolsabr.pipelines.option_universe import (
    discover_option_universe,
    select_option_universe,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover B3 equity-option underlyings by option activity."
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument(
        "--min-financial-volume",
        type=Decimal,
        default=Decimal("0"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    args = parser.parse_args()

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
        "selected": [
            {"rank": index, **entry.as_dict()}
            for index, entry in enumerate(selected, start=1)
        ],
    }

    output = json.dumps(payload, indent=2, ensure_ascii=False)
    print(output)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
