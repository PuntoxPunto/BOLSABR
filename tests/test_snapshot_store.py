from datetime import date

import pytest

from bolsabr.serving.snapshot_store import (
    FilesystemSnapshotStore,
    InvalidSnapshot,
    SnapshotNotFound,
    filter_expiration,
)


def _payload(ref_date: str = "2026-09-23", spot: float = 49.60):
    return {
        "schema_version": "0.1",
        "ref_date": ref_date,
        "market_data_source": "B3_EOD",
        "rate_source": "B3_DI1",
        "underlying": {"ticker": "PETR4", "spot": spot},
        "fallback_risk_free_rate": 0.12,
        "dividend_yield": 0.0,
        "expirations": [
            {
                "date": "2026-10-16",
                "type": "MONTHLY",
                "dte_calendar": 23,
                "dte_business": 16,
                "risk_free_rate": 0.125,
                "rows": [],
            },
            {
                "date": "2026-11-19",
                "type": "MONTHLY",
                "dte_calendar": 57,
                "dte_business": 39,
                "risk_free_rate": 0.123,
                "rows": [],
            },
        ],
    }


def test_publish_creates_immutable_dated_snapshot_and_latest(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    stored = store.publish(_payload())

    dated = tmp_path / "options" / "PETR4" / "2026-09-23.json"
    latest = tmp_path / "options" / "PETR4" / "latest.json"

    assert stored.path == dated
    assert dated.exists()
    assert latest.exists()
    assert store.load_latest("petr4").payload["underlying"]["spot"] == 49.60


def test_same_snapshot_is_idempotent(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    first = store.publish(_payload())
    second = store.publish(_payload())
    assert first.etag == second.etag


def test_dated_snapshot_cannot_be_silently_rewritten(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    store.publish(_payload(spot=49.60))

    with pytest.raises(InvalidSnapshot):
        store.publish(_payload(spot=50.00))


def test_new_date_advances_latest_without_changing_history(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    store.publish(_payload("2026-09-23", 49.60))
    store.publish(_payload("2026-09-24", 50.20))

    assert store.load("PETR4", date(2026, 9, 23)).payload["underlying"]["spot"] == 49.60
    assert store.load_latest("PETR4").ref_date == date(2026, 9, 24)
    assert store.load_latest("PETR4").payload["underlying"]["spot"] == 50.20


def test_filter_expiration_returns_same_contract_shape():
    filtered = filter_expiration(_payload(), date(2026, 10, 16))
    assert len(filtered["expirations"]) == 1
    assert filtered["expirations"][0]["date"] == "2026-10-16"


def test_missing_expiration_raises_not_found():
    with pytest.raises(SnapshotNotFound):
        filter_expiration(_payload(), date(2027, 1, 1))


def test_schema_version_is_enforced(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    payload = _payload()
    payload["schema_version"] = "9.9"
    with pytest.raises(InvalidSnapshot):
        store.publish(payload)



def test_list_latest_returns_only_published_asset_snapshots(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    store.publish(_payload())

    vale = _payload(spot=61.25)
    vale["underlying"]["ticker"] = "VALE3"
    store.publish(vale)

    assets = store.list_latest()
    assert [item.ticker for item in assets] == ["PETR4", "VALE3"]
    assert [item.payload["underlying"]["spot"] for item in assets] == [49.60, 61.25]
