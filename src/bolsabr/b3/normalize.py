from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class OptionContract:
    ticker: str
    underlying: str
    option_type: str
    strike: Decimal
    expiration: date
    exercise_style: str
    contract_multiplier: Decimal | None = None
    isin: str | None = None


@dataclass(frozen=True)
class DailyQuote:
    ticker: str
    ref_date: date
    low: Decimal | None
    high: Decimal | None
    average: Decimal | None
    last: Decimal | None
    trades: int | None
    quantity: Decimal | None
    financial_volume: Decimal | None


@dataclass(frozen=True)
class OpenInterest:
    ticker: str
    ref_date: date
    open_interest: int | None
    variation: int | None
    covered: int | None
    uncovered: int | None
    total_position: int | None


def br_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    raw = value.strip().replace("R$", "").replace(" ", "")
    if not raw:
        return None
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal value: {value!r}") from exc


def parse_date(value: str) -> date:
    raw = value.strip()[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unsupported B3 date format: {value!r}")


def optional_int(value: str | None) -> int | None:
    dec = br_decimal(value)
    return int(dec) if dec is not None else None


def normalize_option_contract(row: dict[str, str]) -> OptionContract:
    ticker = (row.get("TckrSymb") or "").strip().upper()
    underlying = (row.get("UndrlygTckrSymb1") or "").strip().upper()
    option_type = (row.get("OptnTp") or "").strip().upper()
    style = (row.get("OptnStyle") or "").strip().upper()
    strike = br_decimal(row.get("ExrcPric"))
    expiration = row.get("XprtnDt") or ""

    missing = [
        name
        for name, value in {
            "TckrSymb": ticker,
            "UndrlygTckrSymb1": underlying,
            "OptnTp": option_type,
            "OptnStyle": style,
            "ExrcPric": strike,
            "XprtnDt": expiration,
        }.items()
        if value in (None, "")
    ]
    if missing:
        raise ValueError(f"Option row missing required fields: {', '.join(missing)}")

    if option_type in {"COMPRA", "CALL", "C"}:
        option_type = "CALL"
    elif option_type in {"VENDA", "PUT", "P"}:
        option_type = "PUT"
    else:
        raise ValueError(f"Unknown option type: {option_type!r}")

    if style.startswith("AMER"):
        style = "AMERICAN"
    elif style.startswith("EURO"):
        style = "EUROPEAN"

    multiplier = br_decimal(row.get("CtrctMltplr"))
    return OptionContract(
        ticker=ticker,
        underlying=underlying,
        option_type=option_type,
        strike=strike,  # type: ignore[arg-type]
        expiration=parse_date(expiration),
        exercise_style=style,
        contract_multiplier=multiplier,
        isin=(row.get("ISIN") or "").strip() or None,
    )


def normalize_daily_quote(row: dict[str, str]) -> DailyQuote:
    return DailyQuote(
        ticker=(row.get("TckrSymb") or "").strip().upper(),
        ref_date=parse_date(row.get("RptDt") or ""),
        low=br_decimal(row.get("MinPric")),
        high=br_decimal(row.get("MaxPric")),
        average=br_decimal(row.get("TradAvrgPric")),
        last=br_decimal(row.get("LastPric")),
        trades=optional_int(row.get("TradQty")),
        quantity=br_decimal(row.get("FinInstrmQty")),
        financial_volume=br_decimal(row.get("NtlFinVol")),
    )


def normalize_open_interest(row: dict[str, str]) -> OpenInterest:
    oi = optional_int(row.get("OpnIntrst"))
    total = optional_int(row.get("TtlPos"))
    if (oi is None or oi == 0) and total not in (None, 0):
        oi = total
    return OpenInterest(
        ticker=(row.get("TckrSymb") or "").strip().upper(),
        ref_date=parse_date(row.get("RptDt") or ""),
        open_interest=oi,
        variation=optional_int(row.get("VartnOpnIntrst")),
        covered=optional_int(row.get("CvrdQty")),
        uncovered=optional_int(row.get("UcvrdQty")),
        total_position=total,
    )
