from decimal import Decimal

from bolsabr.b3.cotahist import parse_cotahist_line


def _put(buf: list[str], start: int, end: int, value: str) -> None:
    width = end - start
    text = value[:width].ljust(width)
    buf[start:end] = list(text)


def _put_num(buf: list[str], start: int, end: int, value: int) -> None:
    width = end - start
    buf[start:end] = list(str(value).zfill(width))


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
