from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "0.1"


class SnapshotNotFound(LookupError):
    pass


class InvalidSnapshot(ValueError):
    pass


@dataclass(frozen=True)
class StoredSnapshot:
    ticker: str
    ref_date: date
    payload: dict[str, Any]
    etag: str
    path: Path


def _normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not normalized or not normalized.replace("-", "").isalnum():
        raise ValueError(f"invalid ticker: {ticker!r}")
    return normalized


def _validate_payload(payload: Mapping[str, Any], ticker: str | None = None) -> tuple[str, date]:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise InvalidSnapshot(
            f"unsupported schema_version={payload.get('schema_version')!r}; expected {SCHEMA_VERSION}"
        )

    underlying = payload.get("underlying")
    if not isinstance(underlying, Mapping):
        raise InvalidSnapshot("snapshot missing underlying object")

    snapshot_ticker = str(underlying.get("ticker") or "").strip().upper()
    if not snapshot_ticker:
        raise InvalidSnapshot("snapshot missing underlying.ticker")

    if ticker is not None and snapshot_ticker != _normalize_ticker(ticker):
        raise InvalidSnapshot(
            f"snapshot ticker {snapshot_ticker} does not match requested {ticker}"
        )

    raw_ref_date = payload.get("ref_date")
    try:
        ref_date = date.fromisoformat(str(raw_ref_date))
    except ValueError as exc:
        raise InvalidSnapshot(f"invalid ref_date: {raw_ref_date!r}") from exc

    expirations = payload.get("expirations")
    if not isinstance(expirations, list):
        raise InvalidSnapshot("snapshot missing expirations array")

    return snapshot_ticker, ref_date


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def payload_etag(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


class FilesystemSnapshotStore:
    """Immutable EOD Option Chain snapshots with an atomic latest pointer copy."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def _ticker_dir(self, ticker: str) -> Path:
        return self.root / "options" / _normalize_ticker(ticker)

    def _snapshot_path(
        self,
        ticker: str,
        *,
        ref_date: date | None = None,
        latest: bool = False,
    ) -> Path:
        directory = self._ticker_dir(ticker)
        if latest:
            return directory / "latest.json"
        if ref_date is None:
            raise ValueError("ref_date is required unless latest=True")
        return directory / f"{ref_date.isoformat()}.json"

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def publish(self, payload: Mapping[str, Any]) -> StoredSnapshot:
        ticker, ref_date = _validate_payload(payload)
        materialized = dict(payload)
        content = _canonical_bytes(materialized)

        dated_path = self._snapshot_path(ticker, ref_date=ref_date)
        latest_path = self._snapshot_path(ticker, latest=True)

        # Immutable dated snapshot. If it already exists with different bytes,
        # fail instead of rewriting market history silently.
        if dated_path.exists():
            existing = dated_path.read_bytes()
            if existing != content:
                raise InvalidSnapshot(
                    f"snapshot already exists with different content: {dated_path}"
                )
        else:
            self._atomic_write(dated_path, content)

        # latest.json is an atomic copy/pointer representation for filesystem V1.
        self._atomic_write(latest_path, content)

        return StoredSnapshot(
            ticker=ticker,
            ref_date=ref_date,
            payload=materialized,
            etag=payload_etag(materialized),
            path=dated_path,
        )

    def load_latest(self, ticker: str) -> StoredSnapshot:
        return self._load_path(
            ticker,
            self._snapshot_path(ticker, latest=True),
        )

    def load(self, ticker: str, ref_date: date) -> StoredSnapshot:
        return self._load_path(
            ticker,
            self._snapshot_path(ticker, ref_date=ref_date),
        )

    def list_versions(
        self,
        ticker: str,
        *,
        start: date | None = None,
        end: date | None = None,
    ) -> tuple[StoredSnapshot, ...]:
        directory = self._ticker_dir(ticker)
        if not directory.exists():
            return ()

        versions: list[tuple[date, Path]] = []
        for path in directory.glob("*.json"):
            if path.name == "latest.json":
                continue
            try:
                ref_date = date.fromisoformat(path.stem)
            except ValueError:
                continue
            if start is not None and ref_date < start:
                continue
            if end is not None and ref_date > end:
                continue
            versions.append((ref_date, path))

        versions.sort(key=lambda item: item[0])
        return tuple(
            self._load_path(ticker, path)
            for _, path in versions
        )

    def list_latest(self) -> tuple[StoredSnapshot, ...]:
        options_root = self.root / "options"
        if not options_root.exists():
            return ()

        snapshots: list[StoredSnapshot] = []
        for directory in sorted(
            (path for path in options_root.iterdir() if path.is_dir()),
            key=lambda path: path.name,
        ):
            latest = directory / "latest.json"
            if not latest.exists():
                continue
            snapshots.append(self._load_path(directory.name, latest))
        return tuple(snapshots)

    def find_contract(self, contract: str) -> dict[str, Any]:
        wanted = _normalize_contract_ticker(contract)
        for snapshot in self.list_latest():
            try:
                return contract_detail_from_payload(snapshot.payload, wanted)
            except SnapshotNotFound:
                continue
        raise SnapshotNotFound(f"option contract not found: {wanted}")

    def list_contracts(
        self,
        *,
        underlying: str | None = None,
        query: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        underlying_filter = (
            _normalize_ticker(underlying)
            if underlying is not None and underlying.strip()
            else None
        )
        query_filter = (
            _normalize_contract_ticker(query)
            if query is not None and query.strip()
            else None
        )

        results: list[dict[str, Any]] = []
        for snapshot in self.list_latest():
            if underlying_filter is not None and snapshot.ticker != underlying_filter:
                continue
            for item in iter_contract_summaries(snapshot.payload):
                if query_filter is not None and query_filter not in item["ticker"]:
                    continue
                results.append(item)

        return tuple(sorted(results, key=lambda item: item["ticker"]))

    def contract_history(
        self,
        contract: str,
        *,
        start: date | None = None,
        end: date | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        wanted = _normalize_contract_ticker(contract)

        current = self.find_contract(wanted)
        underlying = str(current["underlying"]["ticker"]).strip().upper()

        points: list[dict[str, Any]] = []
        for snapshot in self.list_versions(
            underlying,
            start=start,
            end=end,
        ):
            try:
                detail = contract_detail_from_payload(
                    snapshot.payload,
                    wanted,
                )
            except SnapshotNotFound:
                continue

            contract_data = detail["contract"]
            market = contract_data["market"]
            analytics_input = contract_data["analytics_input"]
            analytics = contract_data["analytics"]

            points.append(
                {
                    "ref_date": snapshot.ref_date.isoformat(),
                    "underlying_spot": detail["underlying"].get("spot"),
                    "last": market.get("last"),
                    "bid": market.get("bid"),
                    "ask": market.get("ask"),
                    "spread_pct": market.get("spread_pct"),
                    "quote_state": market.get("quote_state"),
                    "quality_flags": list(market.get("quality_flags") or []),
                    "trade_count": market.get("trade_count"),
                    "volume": market.get("volume"),
                    "financial_volume": market.get("financial_volume"),
                    "open_interest": market.get("open_interest"),
                    "price_for_model": analytics_input.get("price"),
                    "price_basis": analytics_input.get("price_basis"),
                    "risk_free_rate": analytics_input.get("risk_free_rate"),
                    "iv": analytics.get("iv"),
                    "delta": analytics.get("delta"),
                    "gamma": analytics.get("gamma"),
                    "theta": analytics.get("theta"),
                    "vega": analytics.get("vega"),
                    "rho": analytics.get("rho"),
                    "intrinsic": analytics.get("intrinsic"),
                    "extrinsic": analytics.get("extrinsic"),
                }
            )

        if not points:
            raise SnapshotNotFound(
                f"no historical observations found for option contract: {wanted}"
            )

        if len(points) > limit:
            points = points[-limit:]

        return {
            "schema_version": SCHEMA_VERSION,
            "contract": wanted,
            "underlying": underlying,
            "start_date": points[0]["ref_date"],
            "end_date": points[-1]["ref_date"],
            "observations": len(points),
            "points": points,
        }

    def _load_path(self, ticker: str, path: Path) -> StoredSnapshot:
        if not path.exists():
            raise SnapshotNotFound(str(path))

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise InvalidSnapshot(f"could not read snapshot {path}: {exc}") from exc

        if not isinstance(payload, dict):
            raise InvalidSnapshot("snapshot root must be a JSON object")

        normalized_ticker, ref_date = _validate_payload(payload, ticker)
        return StoredSnapshot(
            ticker=normalized_ticker,
            ref_date=ref_date,
            payload=payload,
            etag=payload_etag(payload),
            path=path,
        )


def _normalize_contract_ticker(contract: str) -> str:
    normalized = contract.strip().upper()
    if not normalized or not normalized.replace("-", "").isalnum():
        raise ValueError(f"invalid option contract ticker: {contract!r}")
    return normalized


def iter_contract_summaries(
    payload: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    underlying = payload.get("underlying")
    expirations = payload.get("expirations")
    if not isinstance(underlying, Mapping) or not isinstance(expirations, list):
        raise InvalidSnapshot("snapshot missing underlying/expirations")

    underlying_ticker = str(underlying.get("ticker") or "").strip().upper()
    ref_date = str(payload.get("ref_date") or "")
    results: list[dict[str, Any]] = []

    for expiration in expirations:
        if not isinstance(expiration, Mapping):
            continue
        expiration_date = expiration.get("date")
        expiration_type = expiration.get("type")
        rows = expiration.get("rows")
        if not isinstance(rows, list):
            continue

        for row in rows:
            if not isinstance(row, Mapping):
                continue
            strike = row.get("strike")
            for side in ("call", "put"):
                leg = row.get(side)
                if not isinstance(leg, Mapping):
                    continue
                market = leg.get("market")
                analytics = leg.get("analytics")
                if not isinstance(market, Mapping):
                    market = {}
                if not isinstance(analytics, Mapping):
                    analytics = {}

                ticker = str(leg.get("ticker") or "").strip().upper()
                if not ticker:
                    continue

                results.append(
                    {
                        "ticker": ticker,
                        "underlying": underlying_ticker,
                        "ref_date": ref_date,
                        "expiration": expiration_date,
                        "expiration_type": expiration_type,
                        "strike": strike,
                        "type": leg.get("type"),
                        "exercise_style": leg.get("exercise_style"),
                        "quote_state": market.get("quote_state"),
                        "last": market.get("last"),
                        "bid": market.get("bid"),
                        "ask": market.get("ask"),
                        "open_interest": market.get("open_interest"),
                        "volume": market.get("volume"),
                        "iv": analytics.get("iv"),
                    }
                )

    return tuple(results)


def contract_detail_from_payload(
    payload: Mapping[str, Any],
    contract: str,
) -> dict[str, Any]:
    wanted = _normalize_contract_ticker(contract)

    underlying = payload.get("underlying")
    expirations = payload.get("expirations")
    if not isinstance(underlying, Mapping) or not isinstance(expirations, list):
        raise InvalidSnapshot("snapshot missing underlying/expirations")

    for expiration in expirations:
        if not isinstance(expiration, Mapping):
            continue
        rows = expiration.get("rows")
        if not isinstance(rows, list):
            continue

        for row in rows:
            if not isinstance(row, Mapping):
                continue
            for side in ("call", "put"):
                leg = row.get(side)
                if not isinstance(leg, Mapping):
                    continue
                if str(leg.get("ticker") or "").strip().upper() != wanted:
                    continue

                return {
                    "schema_version": SCHEMA_VERSION,
                    "ref_date": payload.get("ref_date"),
                    "market_data_source": payload.get("market_data_source"),
                    "rate_source": payload.get("rate_source"),
                    "underlying": dict(underlying),
                    "contract": {
                        "ticker": wanted,
                        "type": leg.get("type"),
                        "exercise_style": leg.get("exercise_style"),
                        "pricing_model": leg.get("pricing_model"),
                        "strike": row.get("strike"),
                        "expiration": expiration.get("date"),
                        "expiration_type": expiration.get("type"),
                        "dte_calendar": expiration.get("dte_calendar"),
                        "dte_business": expiration.get("dte_business"),
                        "market": dict(leg.get("market") or {}),
                        "analytics_input": dict(leg.get("analytics_input") or {}),
                        "analytics": dict(leg.get("analytics") or {}),
                    },
                }

    raise SnapshotNotFound(f"option contract not found: {wanted}")


def filter_expiration(
    payload: Mapping[str, Any],
    expiration: date,
) -> dict[str, Any]:
    expirations = payload.get("expirations")
    if not isinstance(expirations, list):
        raise InvalidSnapshot("snapshot missing expirations array")

    wanted = expiration.isoformat()
    matches = [
        item
        for item in expirations
        if isinstance(item, Mapping) and item.get("date") == wanted
    ]
    if not matches:
        raise SnapshotNotFound(f"expiration not found: {wanted}")

    filtered = dict(payload)
    filtered["expirations"] = [dict(matches[0])]
    return filtered
