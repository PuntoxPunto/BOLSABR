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


def _etag(payload: Mapping[str, Any]) -> str:
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
            etag=_etag(materialized),
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
            etag=_etag(payload),
            path=path,
        )


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
