from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class CotahistRecord:
    trade_date: date
    bdi_code: str
    ticker: str
    market_type: int
    open: Decimal
    high: Decimal
    low: Decimal
    average: Decimal
    last: Decimal
    best_bid: Decimal
    best_ask: Decimal
    trades: int
    quantity: int
    financial_volume: Decimal
    exercise_price: Decimal
    expiration: date | None
    quote_factor: int
    isin: str


def _money(raw: str) -> Decimal:
    value = raw.strip() or "0"
    return Decimal(int(value)) / Decimal(100)


def _integer(raw: str) -> int:
    value = raw.strip()
    return int(value) if value else 0


def _date_yyyymmdd(raw: str) -> date | None:
    value = raw.strip()
    if not value or value == "00000000":
        return None
    return datetime.strptime(value, "%Y%m%d").date()


def parse_cotahist_line(line: str) -> CotahistRecord | None:
    """Parse one 245-byte COTAHIST quote record (record type 01).

    Positions follow the official B3 SeriesHistoricas layout (revision 02).
    Header (00) and trailer (99) return None.
    """
    if len(line.rstrip("\r\n")) < 245:
        raise ValueError("COTAHIST record must contain at least 245 characters")
    raw = line.rstrip("\r\n")
    record_type = raw[0:2]
    if record_type in {"00", "99"}:
        return None
    if record_type != "01":
        raise ValueError(f"Unsupported COTAHIST record type: {record_type!r}")

    trade_date = _date_yyyymmdd(raw[2:10])
    assert trade_date is not None
    return CotahistRecord(
        trade_date=trade_date,
        bdi_code=raw[10:12].strip(),
        ticker=raw[12:24].strip(),
        market_type=_integer(raw[24:27]),
        open=_money(raw[56:69]),
        high=_money(raw[69:82]),
        low=_money(raw[82:95]),
        average=_money(raw[95:108]),
        last=_money(raw[108:121]),
        best_bid=_money(raw[121:134]),
        best_ask=_money(raw[134:147]),
        trades=_integer(raw[147:152]),
        quantity=_integer(raw[152:170]),
        financial_volume=_money(raw[170:188]),
        exercise_price=_money(raw[188:201]),
        expiration=_date_yyyymmdd(raw[202:210]),
        quote_factor=_integer(raw[210:217]),
        isin=raw[230:242].strip(),
    )
