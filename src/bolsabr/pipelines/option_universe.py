from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Mapping

from bolsabr.b3.normalize import br_decimal, optional_int


@dataclass(frozen=True)
class OptionUniverseEntry:
    underlying: str
    listed_contracts: int
    calls: int
    puts: int
    expirations: int
    traded_contracts: int
    option_trades: int
    option_quantity: Decimal
    option_financial_volume: Decimal
    open_interest: int
    spot_available: bool
    spot: Decimal | None
    underlying_segment: str | None
    underlying_cfi: str | None
    underlying_description: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "underlying": self.underlying,
            "listed_contracts": self.listed_contracts,
            "calls": self.calls,
            "puts": self.puts,
            "expirations": self.expirations,
            "traded_contracts": self.traded_contracts,
            "option_trades": self.option_trades,
            "option_quantity": str(self.option_quantity),
            "option_financial_volume": str(self.option_financial_volume),
            "open_interest": self.open_interest,
            "spot_available": self.spot_available,
            "spot": str(self.spot) if self.spot is not None else None,
            "underlying_segment": self.underlying_segment,
            "underlying_cfi": self.underlying_cfi,
            "underlying_description": self.underlying_description,
        }


def _ticker(row: Mapping[str, str]) -> str:
    return (row.get("TckrSymb") or "").strip().upper()


def _underlying(row: Mapping[str, str]) -> str:
    return (
        row.get("Asst")
        or row.get("UndrlygTckrSymb1")
        or ""
    ).strip().upper()


def _is_equity_option(row: Mapping[str, str]) -> bool:
    return (row.get("SgmtNm") or "").strip().upper() in {
        "EQUITY CALL",
        "EQUITY PUT",
    }


def _option_side(row: Mapping[str, str]) -> str:
    segment = (row.get("SgmtNm") or "").strip().upper()
    if segment == "EQUITY CALL":
        return "CALL"
    if segment == "EQUITY PUT":
        return "PUT"
    return ""


def discover_option_universe(
    *,
    instrument_rows: Iterable[Mapping[str, str]],
    trade_rows: Iterable[Mapping[str, str]],
    open_interest_rows: Iterable[Mapping[str, str]],
    require_spot: bool = True,
) -> tuple[OptionUniverseEntry, ...]:
    """Describe listed equity-option underlyings using transparent activity facts.

    Ordering is deliberately lexicographic, not a weighted score:
    financial volume desc, traded contracts desc, open interest desc, ticker.
    """
    instruments = tuple(instrument_rows)
    trades = tuple(trade_rows)
    open_interest = tuple(open_interest_rows)

    option_rows = tuple(
        row
        for row in instruments
        if _is_equity_option(row) and _underlying(row) and _ticker(row)
    )

    options_by_underlying: dict[str, list[Mapping[str, str]]] = {}
    for row in option_rows:
        underlying = _underlying(row)
        options_by_underlying.setdefault(underlying, []).append(row)

    instruments_by_ticker = {
        _ticker(row): row
        for row in instruments
        if _ticker(row)
    }

    trades_by_ticker = {
        _ticker(row): row
        for row in trades
        if _ticker(row)
    }

    oi_by_ticker: dict[str, int] = {}
    for row in open_interest:
        ticker = _ticker(row)
        if not ticker:
            continue
        oi = optional_int(row.get("OpnIntrst"))
        total = optional_int(row.get("TtlPos"))
        if (oi is None or oi == 0) and total not in (None, 0):
            oi = total
        if oi is not None:
            oi_by_ticker[ticker] = oi

    results: list[OptionUniverseEntry] = []

    for underlying, rows in options_by_underlying.items():
        underlying_trade = trades_by_ticker.get(underlying)
        spot = (
            br_decimal(underlying_trade.get("LastPric"))
            if underlying_trade is not None
            else None
        )
        spot_available = spot is not None and spot > 0
        if require_spot and not spot_available:
            continue

        listed_tickers = {_ticker(row) for row in rows}
        calls = sum(1 for row in rows if _option_side(row) == "CALL")
        puts = sum(1 for row in rows if _option_side(row) == "PUT")
        expirations = {
            (row.get("XprtnDt") or "").strip()
            for row in rows
            if (row.get("XprtnDt") or "").strip()
        }

        traded_contracts = 0
        option_trades = 0
        option_quantity = Decimal("0")
        option_financial_volume = Decimal("0")

        for ticker in listed_tickers:
            trade = trades_by_ticker.get(ticker)
            if trade is None:
                continue

            trades_count = optional_int(trade.get("TradQty")) or 0
            quantity = br_decimal(trade.get("FinInstrmQty")) or Decimal("0")
            financial_volume = (
                br_decimal(trade.get("NtlFinVol"))
                or Decimal("0")
            )

            if (
                trades_count > 0
                or quantity > 0
                or financial_volume > 0
            ):
                traded_contracts += 1

            option_trades += trades_count
            option_quantity += quantity
            option_financial_volume += financial_volume

        aggregate_oi = sum(
            oi_by_ticker.get(ticker, 0)
            for ticker in listed_tickers
        )

        underlying_instrument = instruments_by_ticker.get(underlying)

        results.append(
            OptionUniverseEntry(
                underlying=underlying,
                listed_contracts=len(listed_tickers),
                calls=calls,
                puts=puts,
                expirations=len(expirations),
                traded_contracts=traded_contracts,
                option_trades=option_trades,
                option_quantity=option_quantity,
                option_financial_volume=option_financial_volume,
                open_interest=aggregate_oi,
                spot_available=spot_available,
                spot=spot,
                underlying_segment=(
                    (underlying_instrument.get("SgmtNm") or "").strip()
                    if underlying_instrument is not None
                    else None
                ) or None,
                underlying_cfi=(
                    (underlying_instrument.get("CFICd") or "").strip()
                    if underlying_instrument is not None
                    else None
                ) or None,
                underlying_description=(
                    (underlying_instrument.get("AsstDesc") or "").strip()
                    if underlying_instrument is not None
                    else None
                ) or None,
            )
        )

    return tuple(
        sorted(
            results,
            key=lambda item: (
                -item.option_financial_volume,
                -item.traded_contracts,
                -item.open_interest,
                item.underlying,
            ),
        )
    )


def select_option_universe(
    entries: Iterable[OptionUniverseEntry],
    *,
    limit: int,
    min_financial_volume: Decimal = Decimal("0"),
) -> tuple[OptionUniverseEntry, ...]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    if min_financial_volume < 0:
        raise ValueError("min_financial_volume must be >= 0")

    eligible = (
        entry
        for entry in entries
        if entry.option_financial_volume >= min_financial_volume
    )
    return tuple(list(eligible)[:limit])
