from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable

from bolsabr.b3.normalize import br_decimal, parse_date


@dataclass(frozen=True)
class Di1Point:
    ticker: str
    expiration: date
    adjusted_quote: Decimal | None
    adjusted_rate_pct: Decimal
    adjusted_rate_decimal: Decimal


def build_di1_points(
    instrument_rows: Iterable[dict[str, str]],
    trade_rows: Iterable[dict[str, str]],
    *,
    ref_date: date,
) -> tuple[Di1Point, ...]:
    """Build raw DI1 curve vertices from B3 EOD instrument/trade datasets.

    `AdjstdQtTax` is preserved in the B3 quoted annual percentage convention.
    We intentionally do not convert/interpolate it here: the pricing layer must
    explicitly choose the day-count/capitalization convention used for options.
    """
    expirations: dict[str, date] = {}
    for row in instrument_rows:
        ticker = (row.get("TckrSymb") or "").strip().upper()
        asset = (row.get("Asst") or "").strip().upper()
        if asset != "DI1" and not ticker.startswith("DI1"):
            continue
        expiration_raw = (row.get("XprtnDt") or "").strip()
        if not ticker or not expiration_raw:
            continue
        try:
            expiration = parse_date(expiration_raw)
        except ValueError:
            continue
        if expiration > ref_date:
            expirations[ticker] = expiration

    points: list[Di1Point] = []
    for row in trade_rows:
        ticker = (row.get("TckrSymb") or "").strip().upper()
        expiration = expirations.get(ticker)
        if expiration is None:
            continue
        rate_pct = br_decimal(row.get("AdjstdQtTax"))
        if rate_pct is None or rate_pct <= 0:
            continue
        points.append(
            Di1Point(
                ticker=ticker,
                expiration=expiration,
                adjusted_quote=br_decimal(row.get("AdjstdQt")),
                adjusted_rate_pct=rate_pct,
                adjusted_rate_decimal=rate_pct / Decimal(100),
            )
        )

    points.sort(key=lambda point: point.expiration)
    return tuple(points)
