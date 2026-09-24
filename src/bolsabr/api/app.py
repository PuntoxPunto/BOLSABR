from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

from bolsabr.serving.snapshot_store import (
    FilesystemSnapshotStore,
    InvalidSnapshot,
    SnapshotNotFound,
    filter_expiration,
    payload_etag,
)

DEFAULT_SNAPSHOT_DIR = Path("data/serving")


def _cache_headers(etag: str) -> dict[str, str]:
    return {
        "Cache-Control": "public, max-age=300, stale-while-revalidate=3600",
        "ETag": f'"{etag}"',
    }


def create_app(
    snapshot_dir: str | Path | None = None,
) -> FastAPI:
    root = Path(
        snapshot_dir
        or os.environ.get("BOLSABR_SNAPSHOT_DIR")
        or DEFAULT_SNAPSHOT_DIR
    )
    store = FilesystemSnapshotStore(root)

    api = FastAPI(
        title="BOLSABR API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url=None,
    )

    @api.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @api.get("/v1/assets")
    def list_assets(
        request: Request,
        q: str | None = Query(default=None, max_length=32),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> Response:
        try:
            snapshots = store.list_latest()
        except (InvalidSnapshot, ValueError) as exc:
            raise HTTPException(status_code=500, detail="Invalid asset catalog snapshot") from exc

        query = (q or "").strip().upper()
        items: list[dict[str, Any]] = []
        for snapshot in snapshots:
            if query and query not in snapshot.ticker:
                continue
            underlying = snapshot.payload.get("underlying") or {}
            expirations = snapshot.payload.get("expirations") or []
            items.append(
                {
                    "ticker": snapshot.ticker,
                    "ref_date": snapshot.ref_date.isoformat(),
                    "spot": underlying.get("spot"),
                    "expiration_count": len(expirations),
                    "market_data_source": snapshot.payload.get("market_data_source"),
                }
            )
            if len(items) >= limit:
                break

        payload = {"assets": items}
        headers = _cache_headers(payload_etag(payload))
        if request.headers.get("if-none-match") == headers["ETag"]:
            return Response(status_code=304, headers=headers)
        return JSONResponse(content=payload, headers=headers)

    @api.get("/v1/assets/{ticker}/options")
    def get_options(
        ticker: str,
        request: Request,
        expiration: date | None = Query(default=None),
    ) -> Response:
        try:
            snapshot = store.load_latest(ticker)
            payload: dict[str, Any] = snapshot.payload
            if expiration is not None:
                payload = filter_expiration(payload, expiration)
        except SnapshotNotFound as exc:
            raise HTTPException(status_code=404, detail="Option Chain snapshot not found") from exc
        except (InvalidSnapshot, ValueError) as exc:
            raise HTTPException(status_code=500, detail="Invalid Option Chain snapshot") from exc

        response_etag = snapshot.etag if expiration is None else payload_etag(payload)
        headers = _cache_headers(response_etag)
        if request.headers.get("if-none-match") == headers["ETag"]:
            return Response(status_code=304, headers=headers)

        return JSONResponse(
            content=payload,
            headers=headers,
        )

    return api


app = create_app()
