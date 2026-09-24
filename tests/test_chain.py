from datetime import date
from decimal import Decimal

import pytest

from bolsabr.b3.cotahist import CotahistRecord
from bolsabr.chain import build_option_chain


def test_build_chain_pairs_call_put_and_prefers_mid():
    ref = date(2026, 9, 22)
    instruments = [
        {
            "TckrSymb": "PETRJ400",
            "UndrlygTckrSymb1": "PETR4",
            "OptnTp": "Call",
            "ExrcPric": "40,00",
            "XprtnDt": "2026-10-16",
            "OptnStyle": "EURO",
        },
        {
            "TckrSymb": "PETRV400",
            "UndrlygTckrSymb1": "PETR4",
            "OptnTp": "Put",
            "ExrcPric": "40,00",
            "XprtnDt": "2026-10-16",
            "OptnStyle": "EURO",
        },
    ]
    trades = [
        {
            "RptDt": "22/09/2026", "TckrSymb": "PETR4", "LastPric": "38,00",
            "MinPric": "37,50", "MaxPric": "38,40", "TradAvrgPric": "38,00",
            "TradQty": "100", "FinInstrmQty": "1000000", "NtlFinVol": "38000000",
        },
        {
            "RptDt": "22/09/2026", "TckrSymb": "PETRJ400", "LastPric": "1,20",
            "MinPric": "1,00", "MaxPric": "1,30", "TradAvrgPric": "1,15",
            "TradQty": "50", "FinInstrmQty": "5000", "NtlFinVol": "6000",
        },
        {
            "RptDt": "22/09/2026", "TckrSymb": "PETRV400", "LastPric": "3,10",
            "MinPric": "2,90", "MaxPric": "3,20", "TradAvrgPric": "3,05",
            "TradQty": "60", "FinInstrmQty": "6000", "NtlFinVol": "18600",
        },
    ]
    oi = [
        {"RptDt": "22/09/2026", "TckrSymb": "PETRJ400", "OpnIntrst": "1000", "TtlPos": "1000"},
        {"RptDt": "22/09/2026", "TckrSymb": "PETRV400", "OpnIntrst": "1200", "TtlPos": "1200"},
    ]
    hist = [
        CotahistRecord(ref, "78", "PETRJ400", 70, Decimal("1"), Decimal("1.3"), Decimal("1"), Decimal("1.15"), Decimal("1.2"), Decimal("1.1"), Decimal("1.3"), 50, 5000, Decimal("6000"), Decimal("40"), date(2026,10,16), 1, "CALLISIN"),
        CotahistRecord(ref, "82", "PETRV400", 80, Decimal("2.9"), Decimal("3.2"), Decimal("2.9"), Decimal("3.05"), Decimal("3.1"), Decimal("3.0"), Decimal("3.2"), 60, 6000, Decimal("18600"), Decimal("40"), date(2026,10,16), 1, "PUTISIN"),
    ]

    chain = build_option_chain(
        underlying="PETR4",
        ref_date=ref,
        instrument_rows=instruments,
        trade_rows=trades,
        open_interest_rows=oi,
        cotahist_rows=hist,
        risk_free_rate=0.12,
        risk_free_rate_by_expiration=lambda expiry: 0.11 if expiry == date(2026, 10, 16) else 0.12,
    )

    assert chain.spot == 38.0
    assert len(chain.expirations) == 1
    assert chain.expirations[0].risk_free_rate == pytest.approx(0.11)
    row = chain.expirations[0].rows[0]
    assert row.strike == 40.0
    assert row.call is not None and row.put is not None
    assert row.call.price_basis == "MID"
    assert row.call.quote_state == "TWO_SIDED"
    assert row.call.spread_pct == pytest.approx((1.3 - 1.1) / 1.2 * 100)
    assert row.call.risk_free_rate == pytest.approx(0.11)
    assert row.call.price_for_model == pytest.approx(1.2)
    assert row.call.open_interest == 1000
    assert row.put.open_interest == 1200
    assert row.call.iv is not None
    assert row.call.greeks is not None
