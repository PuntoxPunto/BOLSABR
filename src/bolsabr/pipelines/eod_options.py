from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Callable, Iterable, Mapping, Sequence

from bolsabr.api_schema import option_chain_to_dict
from bolsabr.b3.client import B3Csv, latest_final
from bolsabr.b3.cotahist import CotahistRecord, download_cotahist_daily
from bolsabr.b3.di1 import Di1DiscountCurve, Di1Point, build_di1_points
from bolsabr.bcb.sgs import (
    SELIC_DAILY_SERIES,
    fetch_series,
    selic_daily_to_continuous_annual,
)
from bolsabr.chain import OptionChain, build_option_chain


@dataclass(frozen=True)
class DatasetSnapshotInfo:
    ref_date: date
    status: str
    row_count: int
    column_count: int


@dataclass(frozen=True)
class GeneratedOptionChain:
    underlying: str
    ref_date: date
    chain: OptionChain
    payload: dict[str, Any]
    option_instrument_count: int
    trade_row_count: int
    open_interest_row_count: int
    cotahist_row_count: int
    valid_bid_ask_count: int
    underlying_isin: str | None


@dataclass(frozen=True)
class EodOptionBatch:
    ref_date: date
    chains: dict[str, GeneratedOptionChain]
    datasets: dict[str, DatasetSnapshotInfo]
    di1_points: tuple[Di1Point, ...]
    fallback_risk_free_rate: float
    fallback_rate_source: str
    warnings: tuple[str, ...]


def normalize_underlyings(underlyings: Iterable[str]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for raw in underlyings:
        ticker = raw.strip().upper()
        if not ticker:
            continue
        if not ticker.replace("-", "").isalnum():
            raise ValueError(f"invalid underlying ticker: {raw!r}")
        if ticker not in seen:
            seen.add(ticker)
            ordered.append(ticker)
    if not ordered:
        raise ValueError("at least one underlying is required")
    return tuple(ordered)


def select_equity_option_rows(
    instrument_rows: Iterable[dict[str, str]],
    underlying: str,
) -> tuple[dict[str, str], ...]:
    ticker = underlying.strip().upper()
    return tuple(
        row
        for row in instrument_rows
        if (
            row.get("Asst")
            or row.get("UndrlygTckrSymb1")
            or ""
        ).strip().upper()
        == ticker
        and (row.get("SgmtNm") or "").strip().upper()
        in {"EQUITY CALL", "EQUITY PUT"}
    )


def _ticker(row: Mapping[str, str]) -> str:
    return (row.get("TckrSymb") or "").strip().upper()


def _partition_rows(
    rows: Iterable[dict[str, str]],
    wanted: set[str],
) -> tuple[dict[str, str], ...]:
    return tuple(row for row in rows if _ticker(row) in wanted)


def _underlying_isin(
    trade_rows: Iterable[dict[str, str]],
    underlying: str,
) -> str | None:
    ticker = underlying.strip().upper()
    row = next((row for row in trade_rows if _ticker(row) == ticker), None)
    if row is None:
        return None
    raw = (row.get("ISIN") or "").strip().upper()
    return raw or None


def build_option_chains_from_rows(
    *,
    underlyings: Sequence[str],
    ref_date: date,
    instrument_rows: Iterable[dict[str, str]],
    trade_rows: Iterable[dict[str, str]],
    open_interest_rows: Iterable[dict[str, str]],
    cotahist_rows: Iterable[CotahistRecord] = (),
    risk_free_rate: float,
    risk_free_rate_by_expiration: Callable[[date], float] | None = None,
) -> dict[str, GeneratedOptionChain]:
    normalized = normalize_underlyings(underlyings)
    instruments = tuple(instrument_rows)
    trades = tuple(trade_rows)
    open_interest = tuple(open_interest_rows)
    cotahist = tuple(cotahist_rows)

    results: dict[str, GeneratedOptionChain] = {}

    for underlying in normalized:
        option_rows = select_equity_option_rows(instruments, underlying)
        if not option_rows:
            continue

        option_tickers = {
            _ticker(row)
            for row in option_rows
            if _ticker(row)
        }
        wanted_trade_tickers = option_tickers | {underlying}

        selected_trades = _partition_rows(trades, wanted_trade_tickers)
        if not any(_ticker(row) == underlying for row in selected_trades):
            continue

        selected_oi = _partition_rows(open_interest, option_tickers)
        selected_cotahist = tuple(
            row
            for row in cotahist
            if row.ticker.strip().upper() in wanted_trade_tickers
        )

        chain = build_option_chain(
            underlying=underlying,
            ref_date=ref_date,
            instrument_rows=option_rows,
            trade_rows=selected_trades,
            open_interest_rows=selected_oi,
            cotahist_rows=selected_cotahist,
            risk_free_rate=risk_free_rate,
            risk_free_rate_by_expiration=risk_free_rate_by_expiration,
        )

        valid_bid_ask = sum(
            1
            for row in selected_cotahist
            if row.best_bid > 0 and row.best_ask >= row.best_bid
        )

        results[underlying] = GeneratedOptionChain(
            underlying=underlying,
            ref_date=ref_date,
            chain=chain,
            payload=option_chain_to_dict(chain),
            option_instrument_count=len(option_rows),
            trade_row_count=len(selected_trades),
            open_interest_row_count=len(selected_oi),
            cotahist_row_count=len(selected_cotahist),
            valid_bid_ask_count=valid_bid_ask,
            underlying_isin=_underlying_isin(selected_trades, underlying),
        )

    return results


def _snapshot_info(ref_date: date, dataset: B3Csv) -> DatasetSnapshotInfo:
    return DatasetSnapshotInfo(
        ref_date=ref_date,
        status=dataset.status or "N/A",
        row_count=len(dataset.rows),
        column_count=len(dataset.columns),
    )


def _fetch_selic_fallback(
    ref_date: date,
    warnings: list[str],
) -> tuple[float, str]:
    try:
        points = fetch_series(
            SELIC_DAILY_SERIES,
            ref_date - timedelta(days=14),
            ref_date,
        )
        if points:
            latest = points[-1]
            return (
                selic_daily_to_continuous_annual(latest.value),
                f"BCB_SGS_{SELIC_DAILY_SERIES}:{latest.date.isoformat()}",
            )
        warnings.append("BCB SGS returned no Selic points; using 15% fallback")
    except Exception as exc:
        warnings.append(
            f"BCB SGS unavailable: {type(exc).__name__}: {exc}; using 15% fallback"
        )
    return 0.15, "FALLBACK_15PCT"


def fetch_eod_option_chains(
    underlyings: Sequence[str],
    *,
    today: date | None = None,
    lookback_days: int = 10,
    include_cotahist: bool = True,
) -> EodOptionBatch:
    normalized = normalize_underlyings(underlyings)
    warnings: list[str] = []

    snapshots: dict[str, tuple[date, B3Csv]] = {}
    for table in ("instruments", "trades", "derivatives"):
        snapshots[table] = latest_final(
            table,
            today=today,
            lookback_days=lookback_days,
        )

    trade_ref_date = snapshots["trades"][0]
    instruments = snapshots["instruments"][1].rows
    trades = snapshots["trades"][1].rows
    derivatives = snapshots["derivatives"][1].rows

    di1_points = build_di1_points(
        instruments,
        trades,
        ref_date=trade_ref_date,
    )
    di1_curve = (
        Di1DiscountCurve(trade_ref_date, di1_points)
        if di1_points
        else None
    )

    fallback_rate, fallback_source = _fetch_selic_fallback(
        trade_ref_date,
        warnings,
    )

    options_by_underlying = {
        underlying: select_equity_option_rows(instruments, underlying)
        for underlying in normalized
    }
    all_option_tickers = {
        _ticker(row)
        for rows in options_by_underlying.values()
        for row in rows
        if _ticker(row)
    }
    wanted_cotahist = all_option_tickers | set(normalized)

    cotahist_rows: tuple[CotahistRecord, ...] = ()
    if include_cotahist and wanted_cotahist:
        try:
            cotahist_rows = download_cotahist_daily(
                trade_ref_date,
                tickers=wanted_cotahist,
            )
        except Exception as exc:
            warnings.append(
                f"COTAHIST unavailable: {type(exc).__name__}: {exc}; chains will use LAST"
            )

    chains = build_option_chains_from_rows(
        underlyings=normalized,
        ref_date=trade_ref_date,
        instrument_rows=instruments,
        trade_rows=trades,
        open_interest_rows=derivatives,
        cotahist_rows=cotahist_rows,
        risk_free_rate=fallback_rate,
        risk_free_rate_by_expiration=(
            di1_curve.continuous_rate
            if di1_curve is not None
            else None
        ),
    )

    missing = [ticker for ticker in normalized if ticker not in chains]
    if missing:
        warnings.append(
            "No option chain produced for: " + ", ".join(missing)
        )

    return EodOptionBatch(
        ref_date=trade_ref_date,
        chains=chains,
        datasets={
            table: _snapshot_info(ref_date, dataset)
            for table, (ref_date, dataset) in snapshots.items()
        },
        di1_points=di1_points,
        fallback_risk_free_rate=fallback_rate,
        fallback_rate_source=fallback_source,
        warnings=tuple(warnings),
    )
