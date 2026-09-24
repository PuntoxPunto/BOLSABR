from datetime import date
from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

import pytest

import bolsabr.b3.cotahist as cotahist_module
from bolsabr.b3.cotahist import (
    cotahist_annual_url,
    cotahist_daily_url,
    download_cotahist_annual,
    parse_cotahist_line,
)


def _put(buf: list[str], start: int, end: int, value: str) -> None:
    width = end - start
    text = value[:width].ljust(width)
    buf[start:end] = list(text)


def _put_num(buf: list[str], start: int, end: int, value: int) -> None:
    width = end - start
    buf[start:end] = list(str(value).zfill(width))


def _cotahist_line(
    trade_date: str,
    ticker: str,
    *,
    market_type: int = 70,
    last_cents: int = 225,
    bid_cents: int = 220,
    ask_cents: int = 230,
) -> str:
    buf = list(" " * 245)
    _put(buf, 0, 2, "01")
    _put(buf, 2, 10, trade_date)
    _put(buf, 10, 12, "78")
    _put(buf, 12, 24, ticker)
    _put_num(buf, 24, 27, market_type)
    _put_num(buf, 56, 69, last_cents)
    _put_num(buf, 69, 82, last_cents)
    _put_num(buf, 82, 95, last_cents)
    _put_num(buf, 95, 108, last_cents)
    _put_num(buf, 108, 121, last_cents)
    _put_num(buf, 121, 134, bid_cents)
    _put_num(buf, 134, 147, ask_cents)
    _put_num(buf, 147, 152, 10)
    _put_num(buf, 152, 170, 1000)
    _put_num(buf, 170, 188, 225000)
    _put_num(buf, 188, 201, 4000)
    _put(buf, 202, 210, "20261016")
    _put_num(buf, 210, 217, 1)
    _put(buf, 230, 242, "BRTEST000001")
    return "".join(buf)


def _annual_zip(year: int, lines: list[str]) -> bytes:
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        archive.writestr(
            f"COTAHIST_A{year}.TXT",
            "\n".join(
                [
                    "00" + " " * 243,
                    *lines,
                    "99" + " " * 243,
                ]
            ),
        )
    return payload.getvalue()


def test_parse_cotahist_option_record_with_bid_ask():
    buf = list(" " * 245)
    _put(buf, 0, 2, "01")
    _put(buf, 2, 10, "20260922")
    _put(buf, 10, 12, "78")
    _put(buf, 12, 24, "PETRJ400")
    _put_num(buf, 24, 27, 70)
    _put_num(buf, 56, 69, 210)
    _put_num(buf, 69, 82, 240)
    _put_num(buf, 82, 95, 190)
    _put_num(buf, 95, 108, 218)
    _put_num(buf, 108, 121, 225)
    _put_num(buf, 121, 134, 220)
    _put_num(buf, 134, 147, 230)
    _put_num(buf, 147, 152, 123)
    _put_num(buf, 152, 170, 45600)
    _put_num(buf, 170, 188, 10260000)
    _put_num(buf, 188, 201, 4000)
    _put(buf, 202, 210, "20261016")
    _put_num(buf, 210, 217, 1)
    _put(buf, 230, 242, "BRPETRACNPR6")

    row = parse_cotahist_line("".join(buf))
    assert row is not None
    assert row.ticker == "PETRJ400"
    assert row.best_bid == Decimal("2.2")
    assert row.best_ask == Decimal("2.3")
    assert row.exercise_price == Decimal("40")
    assert row.expiration.isoformat() == "2026-10-16"


def test_daily_cotahist_url():
    assert cotahist_daily_url(date(2026, 9, 22)).endswith(
        "/COTAHIST_D22092026.ZIP"
    )


def test_annual_cotahist_url():
    assert cotahist_annual_url(2026).endswith("/COTAHIST_A2026.ZIP")
    with pytest.raises(ValueError):
        cotahist_annual_url(1985)


def test_download_annual_streams_and_filters_ticker_and_date(monkeypatch):
    zip_payload = _annual_zip(
        2026,
        [
            _cotahist_line("20260922", "PETRJ400"),
            _cotahist_line("20260923", "PETRJ400"),
            _cotahist_line("20260924", "VALEJ600"),
        ],
    )

    monkeypatch.setattr(
        cotahist_module,
        "urlopen",
        lambda request, timeout: BytesIO(zip_payload),
    )

    rows = download_cotahist_annual(
        2026,
        tickers={"PETRJ400"},
        start=date(2026, 9, 23),
        end=date(2026, 9, 24),
    )

    assert len(rows) == 1
    assert rows[0].ticker == "PETRJ400"
    assert rows[0].trade_date == date(2026, 9, 23)


def test_annual_bounds_must_belong_to_selected_year():
    with pytest.raises(ValueError):
        download_cotahist_annual(
            2026,
            start=date(2025, 12, 31),
        )
