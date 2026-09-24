from datetime import date
from decimal import Decimal

from bolsabr.b3.cotahist import CotahistRecord
from bolsabr.pipelines.eod_options import (
    build_option_chains_from_rows,
    normalize_underlyings,
    select_equity_option_rows,
)


def _instrument(ticker: str, underlying: str, option_type: str, strike: str):
    return {
        "TckrSymb": ticker,
        "Asst": underlying,
        "SgmtNm": "EQUITY CALL" if option_type == "Call" else "EQUITY PUT",
        "OptnTp": option_type,
        "ExrcPric": strike,
        "XprtnDt": "2026-10-16",
        "OptnStyle": "EURO",
    }


def _trade(ticker: str, last: str, qty: str = "1000"):
    return {
        "RptDt": "24/09/2026",
        "TckrSymb": ticker,
        "LastPric": last,
        "MinPric": last,
        "MaxPric": last,
        "TradAvrgPric": last,
        "TradQty": "10",
        "FinInstrmQty": qty,
        "NtlFinVol": "10000",
        "ISIN": f"BR{ticker[:4]}TEST000",
    }


def _hist(ticker: str, bid: str, ask: str):
    return CotahistRecord(
        trade_date=date(2026, 9, 24),
        bdi_code="82",
        ticker=ticker,
        market_type=80,
        open=Decimal("1"),
        high=Decimal("1"),
        low=Decimal("1"),
        average=Decimal("1"),
        last=Decimal("1"),
        best_bid=Decimal(bid),
        best_ask=Decimal(ask),
        trades=10,
        quantity=1000,
        financial_volume=Decimal("1000"),
        exercise_price=Decimal("0"),
        expiration=date(2026, 10, 16),
        quote_factor=1,
        isin="BRTEST",
    )


def test_normalize_underlyings_is_ordered_uppercase_and_unique():
    assert normalize_underlyings([" petr4 ", "VALE3", "PETR4"]) == (
        "PETR4",
        "VALE3",
    )


def test_select_equity_options_does_not_mix_underlyings():
    rows = [
        _instrument("PETRJ500", "PETR4", "Call", "50,00"),
        _instrument("VALEJ600", "VALE3", "Call", "60,00"),
    ]
    selected = select_equity_option_rows(rows, "PETR4")
    assert [row["TckrSymb"] for row in selected] == ["PETRJ500"]


def test_build_two_chains_from_shared_rows():
    instruments = [
        _instrument("PETRJ500", "PETR4", "Call", "50,00"),
        _instrument("PETRV500", "PETR4", "Put", "50,00"),
        _instrument("VALEJ600", "VALE3", "Call", "60,00"),
        _instrument("VALEV600", "VALE3", "Put", "60,00"),
    ]
    trades = [
        _trade("PETR4", "49,60"),
        _trade("PETRJ500", "2,20"),
        _trade("PETRV500", "2,50"),
        _trade("VALE3", "61,00"),
        _trade("VALEJ600", "3,10"),
        _trade("VALEV600", "1,80"),
    ]
    hist = [
        _hist("PETRJ500", "2.10", "2.30"),
        _hist("PETRV500", "2.40", "2.60"),
        _hist("VALEJ600", "3.00", "3.20"),
        _hist("VALEV600", "1.70", "1.90"),
    ]

    results = build_option_chains_from_rows(
        underlyings=["PETR4", "VALE3"],
        ref_date=date(2026, 9, 24),
        instrument_rows=instruments,
        trade_rows=trades,
        open_interest_rows=[],
        cotahist_rows=hist,
        risk_free_rate=0.12,
    )

    assert set(results) == {"PETR4", "VALE3"}

    petr = results["PETR4"]
    vale = results["VALE3"]

    assert petr.chain.spot == 49.60
    assert vale.chain.spot == 61.00
    assert petr.option_instrument_count == 2
    assert vale.option_instrument_count == 2
    assert petr.cotahist_row_count == 2
    assert vale.cotahist_row_count == 2
    assert petr.valid_bid_ask_count == 2
    assert vale.valid_bid_ask_count == 2

    petr_row = petr.chain.expirations[0].rows[0]
    vale_row = vale.chain.expirations[0].rows[0]

    assert petr_row.call is not None and petr_row.call.ticker == "PETRJ500"
    assert petr_row.put is not None and petr_row.put.ticker == "PETRV500"
    assert vale_row.call is not None and vale_row.call.ticker == "VALEJ600"
    assert vale_row.put is not None and vale_row.put.ticker == "VALEV600"

    assert petr.payload["underlying"]["ticker"] == "PETR4"
    assert vale.payload["underlying"]["ticker"] == "VALE3"
