from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
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



class Di1DiscountCurve:
    """Zero curve built from B3 DI1 settlement PU values.

    B3 DI1 settlement quote (AdjstdQt) is treated as PU against the 100,000
    notional, so each vertex directly supplies a discount factor:

        DF(t) = PU / 100000

    Between observed vertices we interpolate log(DF) linearly by calendar
    date. This preserves positive discount factors and avoids silently mixing
    the DI1 252-business-day quotation convention with an options model that
    uses calendar-year time.

    Outside the observed range we use the continuous zero rate implied by the
    nearest vertex as a flat-rate extrapolation.
    """

    def __init__(self, ref_date: date, points: Iterable[Di1Point]) -> None:
        self.ref_date = ref_date
        valid = [
            point
            for point in points
            if point.expiration > ref_date
            and point.adjusted_quote is not None
            and Decimal("0") < point.adjusted_quote <= Decimal("100000")
        ]
        self.points = tuple(sorted(valid, key=lambda point: point.expiration))
        if not self.points:
            raise ValueError("DI1 curve requires at least one valid PU vertex")

    @staticmethod
    def _df(point: Di1Point) -> float:
        assert point.adjusted_quote is not None
        return float(point.adjusted_quote / Decimal("100000"))

    def discount_factor(self, target: date) -> float:
        if target <= self.ref_date:
            return 1.0

        target_days = (target - self.ref_date).days
        first = self.points[0]
        last = self.points[-1]

        if target <= first.expiration:
            vertex_days = (first.expiration - self.ref_date).days
            zero = -math.log(self._df(first)) / vertex_days
            return math.exp(-zero * target_days)

        if target >= last.expiration:
            vertex_days = (last.expiration - self.ref_date).days
            zero = -math.log(self._df(last)) / vertex_days
            return math.exp(-zero * target_days)

        for left, right in zip(self.points, self.points[1:]):
            if left.expiration <= target <= right.expiration:
                x0 = (left.expiration - self.ref_date).days
                x1 = (right.expiration - self.ref_date).days
                weight = (target_days - x0) / (x1 - x0)
                log_df = math.log(self._df(left)) + weight * (
                    math.log(self._df(right)) - math.log(self._df(left))
                )
                return math.exp(log_df)

        raise RuntimeError("target date was not bracketed by DI1 curve")

    def continuous_rate(self, target: date) -> float:
        """Calendar-year continuously compounded rate consistent with DI1 DF."""
        days = (target - self.ref_date).days
        if days <= 0:
            return 0.0
        df = self.discount_factor(target)
        return -math.log(df) / (days / 365.0)
