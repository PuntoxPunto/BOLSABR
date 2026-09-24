from decimal import Decimal

import pytest

from bolsabr.pipelines.option_universe import (
    discover_option_universe,
    select_option_universe,
)


def _option(
    ticker: str,
    underlying: str,
    side: str,
    expiration: str,
):
    return {
        "TckrSymb": ticker,
        "Asst": underlying,
        "SgmtNm": f"EQUITY {side}",
        "XprtnDt": expiration,
    }


def _trade(
    ticker: str,
    *,
    last: str = "10,00",
    trades: str = "0",
    quantity: str = "0",
    financial_volume: str = "0",
):
    return {
        "TckrSymb": ticker,
        "LastPric": last,
        "TradQty": trades,
        "FinInstrmQty": quantity,
        "NtlFinVol": financial_volume,
    }


def _oi(ticker: str, value: str):
    return {
        "TckrSymb": ticker,
        "OpnIntrst": value,
        "TtlPos": value,
    }


def test_discovery_aggregates_activity_by_underlying():
    instruments = [
        _option("AAA1C1", "AAA1", "CALL", "2026-10-16"),
        _option("AAA1P1", "AAA1", "PUT", "2026-10-16"),
        _option("AAA1C2", "AAA1", "CALL", "2026-11-20"),
        _option("BBB2C1", "BBB2", "CALL", "2026-10-16"),
        {"TckrSymb": "NOTOPT", "Asst": "CCC3", "SgmtNm": "CASH"},
    ]
    trades = [
        _trade("AAA1", last="25,00"),
        _trade("BBB2", last="30,00"),
        _trade(
            "AAA1C1",
            trades="10",
            quantity="1000",
            financial_volume="25000",
        ),
        _trade(
            "AAA1P1",
            trades="5",
            quantity="500",
            financial_volume="10000",
        ),
        _trade(
            "BBB2C1",
            trades="20",
            quantity="2000",
            financial_volume="50000",
        ),
    ]
    oi = [
        _oi("AAA1C1", "1000"),
        _oi("AAA1P1", "2000"),
        _oi("BBB2C1", "500"),
    ]

    entries = discover_option_universe(
        instrument_rows=instruments,
        trade_rows=trades,
        open_interest_rows=oi,
    )

    assert [entry.underlying for entry in entries] == ["BBB2", "AAA1"]

    aaa = next(entry for entry in entries if entry.underlying == "AAA1")
    assert aaa.listed_contracts == 3
    assert aaa.calls == 2
    assert aaa.puts == 1
    assert aaa.expirations == 2
    assert aaa.traded_contracts == 2
    assert aaa.option_trades == 15
    assert aaa.option_quantity == Decimal("1500")
    assert aaa.option_financial_volume == Decimal("35000")
    assert aaa.open_interest == 3000
    assert aaa.spot == Decimal("25.00")


def test_discovery_requires_spot_by_default():
    entries = discover_option_universe(
        instrument_rows=[
            _option("AAA1C1", "AAA1", "CALL", "2026-10-16"),
            _option("ZZZ9C1", "ZZZ9", "CALL", "2026-10-16"),
        ],
        trade_rows=[
            _trade("AAA1", last="25,00"),
            _trade("AAA1C1", financial_volume="1000"),
            _trade("ZZZ9C1", financial_volume="999999"),
        ],
        open_interest_rows=[],
    )

    assert [entry.underlying for entry in entries] == ["AAA1"]


def test_ranking_uses_traded_contracts_then_oi_after_equal_financial_volume():
    instruments = [
        _option("AAA1C1", "AAA1", "CALL", "2026-10-16"),
        _option("BBB2C1", "BBB2", "CALL", "2026-10-16"),
        _option("BBB2P1", "BBB2", "PUT", "2026-10-16"),
        _option("CCC3C1", "CCC3", "CALL", "2026-10-16"),
    ]
    trades = [
        _trade("AAA1"),
        _trade("BBB2"),
        _trade("CCC3"),
        _trade("AAA1C1", trades="10", financial_volume="10000"),
        _trade("BBB2C1", trades="5", financial_volume="5000"),
        _trade("BBB2P1", trades="5", financial_volume="5000"),
        _trade("CCC3C1", trades="10", financial_volume="10000"),
    ]
    oi = [
        _oi("AAA1C1", "1000"),
        _oi("BBB2C1", "10"),
        _oi("BBB2P1", "20"),
        _oi("CCC3C1", "2000"),
    ]

    entries = discover_option_universe(
        instrument_rows=instruments,
        trade_rows=trades,
        open_interest_rows=oi,
    )

    # BBB2 wins first tie-break because two option contracts traded.
    # CCC3 then beats AAA1 on aggregate OI.
    assert [entry.underlying for entry in entries] == [
        "BBB2",
        "CCC3",
        "AAA1",
    ]


def test_select_option_universe_applies_minimum_and_limit():
    entries = discover_option_universe(
        instrument_rows=[
            _option("AAA1C1", "AAA1", "CALL", "2026-10-16"),
            _option("BBB2C1", "BBB2", "CALL", "2026-10-16"),
            _option("CCC3C1", "CCC3", "CALL", "2026-10-16"),
        ],
        trade_rows=[
            _trade("AAA1"),
            _trade("BBB2"),
            _trade("CCC3"),
            _trade("AAA1C1", financial_volume="30000"),
            _trade("BBB2C1", financial_volume="20000"),
            _trade("CCC3C1", financial_volume="100"),
        ],
        open_interest_rows=[],
    )

    selected = select_option_universe(
        entries,
        limit=1,
        min_financial_volume=Decimal("1000"),
    )

    assert [entry.underlying for entry in selected] == ["AAA1"]

    with pytest.raises(ValueError):
        select_option_universe(entries, limit=0)
