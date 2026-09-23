from __future__ import annotations

import csv
import io
import json
import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE = "https://arquivos.b3.com.br"
DOWNLOAD_TOKEN_URL = f"{API_BASE}/api/download/requestname"
DOWNLOAD_CSV_URL = f"{API_BASE}/api/download/"

TABLES = {
    "instruments": "InstrumentsConsolidated",
    "trades": "TradeInformationConsolidated",
    "derivatives": "DerivativesOpenPosition",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": API_BASE,
    "Referer": f"{API_BASE}/",
}


@dataclass(frozen=True)
class B3Csv:
    columns: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    status: str


def parse_b3_csv(payload: bytes | str) -> B3Csv:
    """Parse B3 semicolon-delimited CSVs.

    B3's files are commonly ISO-8859-1 and may start with
    ``Status do Arquivo: Final`` / ``Parcial``. DerivativesOpenPosition
    may start directly with the header.
    """
    text = payload.decode("iso-8859-1") if isinstance(payload, bytes) else payload
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [line for line in lines if line.strip()]
    if not lines:
        return B3Csv((), (), "")

    status = ""
    header_idx = 0
    if lines[0].lstrip("\ufeff").startswith("Status do Arquivo"):
        status = lines[0].split(":", 1)[-1].strip() if ":" in lines[0] else ""
        header_idx = 1

    if header_idx >= len(lines):
        return B3Csv((), (), status)

    reader = csv.reader(io.StringIO("\n".join(lines[header_idx:])), delimiter=";")
    raw = list(reader)
    if not raw:
        return B3Csv((), (), status)

    columns = tuple(col.strip().lstrip("\ufeff") for col in raw[0])
    rows: list[dict[str, str]] = []
    for values in raw[1:]:
        if not values or not any(v.strip() for v in values):
            continue
        padded = list(values[: len(columns)]) + [""] * max(0, len(columns) - len(values))
        rows.append(dict(zip(columns, (v.strip() for v in padded), strict=True)))
    return B3Csv(columns, tuple(rows), status)


def _get(url: str, *, timeout: float = 60.0, retries: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(retries):
        request = Request(url, headers=_HEADERS, method="GET")
        try:
            with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed B3 host
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(1.0 * (attempt + 1))
    assert last_error is not None
    raise last_error


def request_download_token(api_name: str, ref_date: date) -> str | None:
    query = urlencode({"fileName": api_name, "date": ref_date.isoformat()})
    try:
        payload = _get(f"{DOWNLOAD_TOKEN_URL}?{query}", timeout=20.0)
    except HTTPError as exc:
        if exc.code == 400:
            return None
        raise
    data = json.loads(payload.decode("utf-8"))
    return data.get("token") or None


def download_table(table: str, ref_date: date) -> B3Csv | None:
    """Download and parse a B3 public-data table for a specific date."""
    api_name = TABLES.get(table)
    if api_name is None:
        raise ValueError(f"Unknown B3 table: {table!r}. Expected one of {sorted(TABLES)}")
    token = request_download_token(api_name, ref_date)
    if not token:
        return None
    query = urlencode({"token": token})
    payload = _get(f"{DOWNLOAD_CSV_URL}?{query}", timeout=300.0)
    return parse_b3_csv(payload)


def latest_final(table: str, today: date | None = None, lookback_days: int = 7) -> tuple[date, B3Csv]:
    """Return the latest available non-partial snapshot within ``lookback_days``."""
    current = today or date.today()
    for offset in range(lookback_days + 1):
        ref_date = current - timedelta(days=offset)
        data = download_table(table, ref_date)
        if data is None:
            continue
        if data.status.lower() == "parcial":
            continue
        return ref_date, data
    raise LookupError(f"No final B3 snapshot found for {table!r} in the last {lookback_days + 1} days")


def select(rows: Iterable[dict[str, str]], **equals: str) -> list[dict[str, str]]:
    """Small helper for deterministic exact filtering of normalized raw rows."""
    return [row for row in rows if all((row.get(key) or "").strip() == value for key, value in equals.items())]
