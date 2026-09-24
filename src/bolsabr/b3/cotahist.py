from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from io import TextIOWrapper
from shutil import copyfileobj
from tempfile import SpooledTemporaryFile
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


def cotahist_annual_url(year: int) -> str:
    if year < 1986:
        raise ValueError("B3 COTAHIST annual series starts in 1986")
    return f"{COTAHIST_BASE_URL}/COTAHIST_A{year}.ZIP"


def _download_cotahist_zip(
    *,
    zip_name: str,
    txt_name: str,
    tickers: set[str] | None = None,
    start: date | None = None,
    end: date | None = None,
    timeout: float = 120.0,
) -> tuple[CotahistRecord, ...]:
    if start is not None and end is not None and start > end:
        raise ValueError("start must be <= end")

    request = Request(
        f"{COTAHIST_BASE_URL}/{zip_name}",
        headers={
            "User-Agent": "Mozilla/5.0 BOLSABR/0.1",
            "Accept": "application/zip,application/octet-stream,*/*",
            "Referer": "https://www.b3.com.br/",
        },
        method="GET",
    )

    wanted = {ticker.upper() for ticker in tickers} if tickers else None
    start_raw = start.strftime("%Y%m%d") if start is not None else None
    end_raw = end.strftime("%Y%m%d") if end is not None else None

    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed B3 host
            # Annual files can be large. Spill to disk after 8 MB instead of
            # retaining the whole ZIP and decompressed TXT in process memory.
            with SpooledTemporaryFile(max_size=8 * 1024 * 1024) as spool:
                copyfileobj(response, spool)
                spool.seek(0)
                head = spool.read(64).lstrip().lower()
                if head.startswith(b"<!doctype html") or head.startswith(b"<html"):
                    raise RuntimeError(
                        "B3 returned HTML instead of COTAHIST ZIP "
                        "(possible CAPTCHA/block)"
                    )
                spool.seek(0)

                try:
                    with ZipFile(spool) as archive:
                        names = archive.namelist()
                        expected = txt_name.upper()
                        member = next(
                            (
                                name
                                for name in names
                                if name.upper().endswith(expected)
                            ),
                            None,
                        )
                        if member is None:
                            member = next(
                                (
                                    name
                                    for name in names
                                    if name.upper().endswith(".TXT")
                                ),
                                None,
                            )
                        if member is None:
                            raise RuntimeError(
                                f"No TXT member found in {zip_name}: {names[:5]}"
                            )

                        records: list[CotahistRecord] = []
                        with archive.open(member) as raw_member:
                            with TextIOWrapper(
                                raw_member,
                                encoding="latin-1",
                                newline="",
                            ) as text:
                                for line in text:
                                    if len(line) < 24 or line[:2] != "01":
                                        continue

                                    raw_date = line[2:10]
                                    if start_raw is not None and raw_date < start_raw:
                                        continue
                                    if end_raw is not None and raw_date > end_raw:
                                        continue

                                    if wanted is not None:
                                        ticker = line[12:24].strip().upper()
                                        if ticker not in wanted:
                                            continue

                                    record = parse_cotahist_line(line)
                                    if record is not None:
                                        records.append(record)
                        return tuple(records)
                except BadZipFile as exc:
                    raise RuntimeError(
                        f"Invalid ZIP returned for {zip_name}"
                    ) from exc
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(
            f"Unable to download B3 COTAHIST {zip_name}: {exc}"
        ) from exc


def download_cotahist_daily(
    ref_date: date,
    *,
    tickers: set[str] | None = None,
    timeout: float = 60.0,
) -> tuple[CotahistRecord, ...]:
    """Download one official daily COTAHIST ZIP and return parsed records."""
    date_str = ref_date.strftime("%d%m%Y")
    return _download_cotahist_zip(
        zip_name=f"COTAHIST_D{date_str}.ZIP",
        txt_name=f"COTAHIST_D{date_str}.TXT",
        tickers=tickers,
        start=ref_date,
        end=ref_date,
        timeout=timeout,
    )


def download_cotahist_annual(
    year: int,
    *,
    tickers: set[str] | None = None,
    start: date | None = None,
    end: date | None = None,
    timeout: float = 180.0,
) -> tuple[CotahistRecord, ...]:
    """Download one official annual COTAHIST series and stream filtered rows.

    The current-year annual series is cumulative through the latest available
    trading day. Date bounds, when provided, must belong to the selected year.
    """
    if year < 1986:
        raise ValueError("B3 COTAHIST annual series starts in 1986")
    for bound in (start, end):
        if bound is not None and bound.year != year:
            raise ValueError(
                f"COTAHIST annual bound {bound} is outside year {year}"
            )

    return _download_cotahist_zip(
        zip_name=f"COTAHIST_A{year}.ZIP",
        txt_name=f"COTAHIST_A{year}.TXT",
        tickers=tickers,
        start=start,
        end=end,
        timeout=timeout,
    )
