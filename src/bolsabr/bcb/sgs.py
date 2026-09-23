from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SGS_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
SELIC_DAILY_SERIES = 11


@dataclass(frozen=True)
class SgsPoint:
    date: date
    value: float


def fetch_series(
    series_id: int,
    start: date,
    end: date,
    timeout: float = 30.0,
) -> tuple[SgsPoint, ...]:
    """Fetch a bounded SGS JSON range from Banco Central do Brasil."""
    query = urlencode(
        {
            "dataInicial": start.strftime("%d/%m/%Y"),
            "dataFinal": end.strftime("%d/%m/%Y"),
            "formato": "json",
        }
    )
    url = f"{SGS_BASE}.{series_id}/dados?{query}"
    request = Request(url, headers={"User-Agent": "BOLSABR/0.1"}, method="GET")
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed BCB host
        payload = json.loads(response.read().decode("utf-8"))
    return tuple(
        SgsPoint(
            date=date(
                int(item["data"][6:10]),
                int(item["data"][3:5]),
                int(item["data"][0:2]),
            ),
            value=float(str(item["valor"]).replace(",", ".")),
        )
        for item in payload
    )


def selic_daily_to_continuous_annual(
    daily_percent: float,
    business_days: int = 252,
) -> float:
    """Convert SGS 11 daily percentage to a flat continuously compounded annual rate.

    This is an explicit Phase-0 approximation, not a replacement for a DI1 term curve.
    """
    if daily_percent <= -100:
        raise ValueError("daily_percent must be greater than -100")
    daily_factor = 1.0 + daily_percent / 100.0
    effective_annual = daily_factor**business_days - 1.0
    return math.log1p(effective_annual)
