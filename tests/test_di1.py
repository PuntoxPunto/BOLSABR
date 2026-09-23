from datetime import date
from decimal import Decimal

from bolsabr.b3.di1 import build_di1_points


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
