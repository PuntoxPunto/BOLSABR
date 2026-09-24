from datetime import date
from decimal import Decimal

from bolsabr.b3.cotahist import CotahistRecord
from bolsabr.backfill.cotahist import build_cotahist_backfill_points


def _record(
    ticker: str,
    *,
    trade_date: date = date(2026, 9, 22),
    bdi_code: str = "78",
    last: str = "2.25",
    bid: str = "2.20",
    ask: str = "2.30",
    strike: str = "49.61",
    expiration: date | None = date(2026, 10, 16),
    trades: int = 123,
    quantity: int = 45600,
) -> CotahistRecord:
    return CotahistRecord(
        trade_date=trade_date,
        bdi_code=bdi_code,
        ticker=ticker,
        market_type=70 if bdi_code in {"78", "82"} else 10,
        open=Decimal(last),
        high=Decimal(last),
        low=Decimal(last),
        average=Decimal(last),
        last=Decimal(last),
        best_bid=Decimal(bid),
        best_ask=Decimal(ask),
        trades=trades,
        quantity=quantity,
        financial_volume=Decimal("102600.00"),
        exercise_price=Decimal(strike),
        expiration=expiration,
        quote_factor=1,
        isin="BRTEST000001",
    )


def _contract():
    return {
        "ticker": "PETRJ510",
        "underlying": "PETR4",
        "expiration": "2026-10-16",
        "expiration_type": "MONTHLY",
        "strike": 49.61,
        "type": "CALL",
        "exercise_style": "AMERICAN",
    }


def test_cotahist_backfill_projects_market_data_without_fabricating_analytics():
    records = [
        _record(
            "PETR4",
            bdi_code="02",
            last="49.60",
            bid="49.59",
            ask="49.61",
            strike="0",
            expiration=None,
        ),
        _record("PETRJ510"),
    ]

    projected = build_cotahist_backfill_points(
        underlying="PETR4",
        contracts=[_contract()],
        records=records,
    )

    points = projected["PETRJ510"]
    assert len(points) == 1
    point = points[0]

    assert point["ref_date"] == "2026-09-22"
    assert point["source"] == "B3_COTAHIST_BACKFILL"
    assert point["underlying_spot"] == 49.60
    assert point["last"] == 2.25
    assert point["bid"] == 2.20
    assert point["ask"] == 2.30
    assert point["quote_state"] == "TWO_SIDED"
    assert point["trade_count"] == 123
    assert point["volume"] == 45600

    assert point["open_interest"] is None
    assert point["iv"] is None
    assert point["delta"] is None
    assert point["risk_free_rate"] is None
    assert point["price_basis"] is None


def test_cotahist_backfill_rejects_wrong_option_side():
    projected = build_cotahist_backfill_points(
        underlying="PETR4",
        contracts=[_contract()],
        records=[_record("PETRJ510", bdi_code="82")],
    )
    assert projected["PETRJ510"] == []


def test_cotahist_backfill_rejects_reused_ticker_with_other_expiration():
    projected = build_cotahist_backfill_points(
        underlying="PETR4",
        contracts=[_contract()],
        records=[
            _record(
                "PETRJ510",
                expiration=date(2027, 10, 15),
            )
        ],
    )
    assert projected["PETRJ510"] == []


def test_cotahist_backfill_rejects_strike_mismatch():
    projected = build_cotahist_backfill_points(
        underlying="PETR4",
        contracts=[_contract()],
        records=[_record("PETRJ510", strike="55.00")],
    )
    assert projected["PETRJ510"] == []


def test_cotahist_backfill_marks_wide_spread():
    projected = build_cotahist_backfill_points(
        underlying="PETR4",
        contracts=[_contract()],
        records=[
            _record(
                "PETRJ510",
                bid="1.00",
                ask="2.00",
            )
        ],
    )
    point = projected["PETRJ510"][0]
    assert point["quote_state"] == "TWO_SIDED"
    assert "WIDE_SPREAD_GT_30PCT" in point["quality_flags"]
