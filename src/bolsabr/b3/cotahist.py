from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile

COTAHIST_BASE_URL = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist"


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



def cotahist_daily_url(ref_date: date) -> str:
    filename = f"COTAHIST_D{ref_date.strftime('%d%m%Y')}.ZIP"
    return f"{COTAHIST_BASE_URL}/{filename}"


def download_cotahist_daily(
    ref_date: date,
    *,
    tickers: set[str] | None = None,
    timeout: float = 60.0,
) -> tuple[CotahistRecord, ...]:
    """Download one official daily COTAHIST ZIP and return parsed records.

    The B3 historical-series endpoint uses COTAHIST_DDDMMYYYY.ZIP for
    daily files in the current year. Filtering while parsing avoids
    retaining the full daily market file when only a chain is needed.
    """
    date_str = ref_date.strftime("%d%m%Y")
    zip_name = f"COTAHIST_D{date_str}.ZIP"
    txt_name = f"COTAHIST_D{date_str}.TXT"
    request = Request(
        f"{COTAHIST_BASE_URL}/{zip_name}",
        headers={
            "User-Agent": "Mozilla/5.0 BOLSABR/0.1",
            "Accept": "application/zip,application/octet-stream,*/*",
            "Referer": "https://www.b3.com.br/",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed B3 host
            payload = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Unable to download B3 COTAHIST {zip_name}: {exc}") from exc

    if payload[:20].lstrip().lower().startswith(b"<!doctype html") or payload[:10].lstrip().lower().startswith(b"<html"):
        raise RuntimeError("B3 returned HTML instead of COTAHIST ZIP (possible CAPTCHA/block)")

    try:
        with ZipFile(BytesIO(payload)) as archive:
            names = archive.namelist()
            member = next((name for name in names if name.upper().endswith(txt_name)), None)
            if member is None:
                member = next((name for name in names if name.upper().endswith(".TXT")), None)
            if member is None:
                raise RuntimeError(f"No TXT member found in {zip_name}: {names[:5]}")
            text = archive.read(member).decode("latin-1")
    except BadZipFile as exc:
        raise RuntimeError(f"Invalid ZIP returned for {zip_name}") from exc

    wanted = {ticker.upper() for ticker in tickers} if tickers else None
    records: list[CotahistRecord] = []
    for line in text.splitlines():
        if len(line) < 2 or line[:2] in {"00", "99"}:
            continue
        if line[:2] != "01":
            continue
        if wanted is not None:
            ticker = line[12:24].strip().upper()
            if ticker not in wanted:
                continue
        record = parse_cotahist_line(line)
        if record is not None:
            records.append(record)
    return tuple(records)
