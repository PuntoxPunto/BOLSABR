from datetime import date
from decimal import Decimal

import pytest

from bolsabr.b3.di1 import Di1DiscountCurve, Di1Point, build_di1_points


def test_build_di1_points_preserves_b3_adjustment_rate():
    instruments = [
        {
            "TckrSymb": "DI1F27",
            "Asst": "DI1",
            "XprtnDt": "2027-01-04",
        },
        {
            "TckrSymb": "PETR4",
            "Asst": "PETR4",
            "XprtnDt": "",
        },
    ]
    trades = [
        {
            "TckrSymb": "DI1F27",
            "AdjstdQt": "95000,00",
            "AdjstdQtTax": "14,125",
        }
    ]

    points = build_di1_points(
        instruments,
        trades,
        ref_date=date(2026, 9, 22),
    )

    assert len(points) == 1
    assert points[0].ticker == "DI1F27"
    assert points[0].adjusted_rate_pct == Decimal("14.125")
    assert points[0].adjusted_rate_decimal == Decimal("0.14125")



def test_di1_discount_curve_hits_vertices_and_log_interpolates():
    points = (
        Di1Point("DI1V26", date(2026, 10, 1), Decimal("99645.13"), Decimal("13.653"), Decimal("0.13653")),
        Di1Point("DI1X26", date(2026, 11, 3), Decimal("98587.97"), Decimal("13.654"), Decimal("0.13654")),
    )
    curve = Di1DiscountCurve(date(2026, 9, 22), points)

    assert curve.discount_factor(date(2026, 10, 1)) == pytest.approx(0.9964513)
    assert curve.discount_factor(date(2026, 11, 3)) == pytest.approx(0.9858797)

    target = date(2026, 10, 16)
    rate = curve.continuous_rate(target)
    assert rate == pytest.approx(0.12779807, abs=1e-8)


def test_di1_curve_flat_zero_rate_extrapolation_before_first_vertex():
    points = (
        Di1Point("DI1V26", date(2026, 10, 1), Decimal("99645.13"), Decimal("13.653"), Decimal("0.13653")),
    )
    curve = Di1DiscountCurve(date(2026, 9, 22), points)
    r_first = curve.continuous_rate(date(2026, 10, 1))
    r_early = curve.continuous_rate(date(2026, 9, 25))
    assert r_early == pytest.approx(r_first)
