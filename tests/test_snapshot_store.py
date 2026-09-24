from datetime import date

import pytest

from bolsabr.serving.snapshot_store import (
    FilesystemSnapshotStore,
    InvalidSnapshot,
    SnapshotNotFound,
    filter_expiration,
)


def _option_leg(ticker: str, option_type: str):
    return {
        "ticker": ticker,
        "type": option_type,
        "exercise_style": "EUROPEAN",
        "pricing_model": "BSM_EUROPEAN",
        "market": {
            "last": 2.20,
            "bid": 2.10,
            "ask": 2.30,
            "spread_pct": 9.09,
            "quote_state": "TWO_SIDED",
            "quality_flags": [],
            "trade_count": 100,
            "volume": 10000,
            "financial_volume": 22000,
            "open_interest": 25000,
        },
        "analytics_input": {
            "price": 2.20,
            "price_basis": "MID",
            "risk_free_rate": 0.125,
        },
        "analytics": {
            "intrinsic": 0.0,
            "extrinsic": 2.20,
            "iv": 0.40,
            "delta": 0.55 if option_type == "CALL" else -0.45,
            "gamma": 0.08,
            "theta": -0.05,
            "vega": 0.04,
            "rho": 0.01,
        },
    }


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
                "rows": [
                    {
                        "strike": 49.61,
                        "call": _option_leg("PETRJ510", "CALL"),
                        "put": _option_leg("PETRV510", "PUT"),
                    }
                ],
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



def test_find_contract_returns_compact_contract_detail(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    store.publish(_payload())

    detail = store.find_contract("petrj510")
    assert detail["underlying"]["ticker"] == "PETR4"
    assert detail["contract"]["ticker"] == "PETRJ510"
    assert detail["contract"]["strike"] == 49.61
    assert detail["contract"]["expiration"] == "2026-10-16"
    assert detail["contract"]["market"]["bid"] == 2.10
    assert detail["contract"]["analytics"]["iv"] == 0.40


def test_list_contracts_supports_underlying_and_query(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    store.publish(_payload())

    vale = _payload(spot=61.25)
    vale["underlying"]["ticker"] = "VALE3"
    vale["expirations"][0]["rows"][0]["call"]["ticker"] = "VALEJ700"
    vale["expirations"][0]["rows"][0]["put"]["ticker"] = "VALEV700"
    store.publish(vale)

    all_contracts = store.list_contracts()
    assert {item["ticker"] for item in all_contracts} == {
        "PETRJ510",
        "PETRV510",
        "VALEJ700",
        "VALEV700",
    }

    petr = store.list_contracts(underlying="PETR4")
    assert {item["ticker"] for item in petr} == {"PETRJ510", "PETRV510"}

    queried = store.list_contracts(query="VALEJ")
    assert [item["ticker"] for item in queried] == ["VALEJ700"]


def test_find_missing_contract_raises_not_found(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    store.publish(_payload())
    with pytest.raises(SnapshotNotFound):
        store.find_contract("ABCDJ999")



def _history_payload(
    ref_date: str,
    *,
    spot: float,
    last: float,
    iv: float,
    open_interest: int,
    volume: int,
):
    payload = _payload(ref_date, spot)
    leg = payload["expirations"][0]["rows"][0]["call"]
    leg["market"]["last"] = last
    leg["market"]["bid"] = round(last - 0.1, 2)
    leg["market"]["ask"] = round(last + 0.1, 2)
    leg["market"]["open_interest"] = open_interest
    leg["market"]["volume"] = volume
    leg["analytics_input"]["price"] = last
    leg["analytics"]["iv"] = iv
    return payload


def test_list_versions_is_chronological_and_excludes_latest_alias(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    store.publish(_history_payload(
        "2026-09-22", spot=49.10, last=2.00, iv=0.40,
        open_interest=1000, volume=100,
    ))
    store.publish(_history_payload(
        "2026-09-23", spot=49.60, last=2.20, iv=0.43,
        open_interest=1200, volume=150,
    ))
    store.publish(_history_payload(
        "2026-09-24", spot=50.10, last=2.40, iv=0.45,
        open_interest=1400, volume=200,
    ))

    versions = store.list_versions("PETR4")
    assert [item.ref_date.isoformat() for item in versions] == [
        "2026-09-22",
        "2026-09-23",
        "2026-09-24",
    ]


def test_contract_history_projects_real_snapshot_points_without_interpolation(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    store.publish(_history_payload(
        "2026-09-22", spot=49.10, last=2.00, iv=0.40,
        open_interest=1000, volume=100,
    ))

    missing = _history_payload(
        "2026-09-23", spot=49.60, last=2.20, iv=0.43,
        open_interest=1200, volume=150,
    )
    missing["expirations"][0]["rows"][0]["call"] = None
    store.publish(missing)

    store.publish(_history_payload(
        "2026-09-24", spot=50.10, last=2.40, iv=0.45,
        open_interest=1400, volume=200,
    ))

    history = store.contract_history("PETRJ510")

    assert history["contract"] == "PETRJ510"
    assert history["underlying"] == "PETR4"
    assert history["observations"] == 2
    assert [point["ref_date"] for point in history["points"]] == [
        "2026-09-22",
        "2026-09-24",
    ]
    assert [point["last"] for point in history["points"]] == [2.00, 2.40]
    assert [point["iv"] for point in history["points"]] == [0.40, 0.45]
    assert [point["open_interest"] for point in history["points"]] == [1000, 1400]


def test_contract_history_filters_dates_and_keeps_most_recent_limit(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    for day, last in [(22, 2.00), (23, 2.20), (24, 2.40)]:
        store.publish(_history_payload(
            f"2026-09-{day}",
            spot=49.0 + (day - 22) * 0.5,
            last=last,
            iv=0.40 + (day - 22) * 0.02,
            open_interest=1000 + (day - 22) * 100,
            volume=100 + (day - 22) * 50,
        ))

    limited = store.contract_history("PETRJ510", limit=2)
    assert [point["ref_date"] for point in limited["points"]] == [
        "2026-09-23",
        "2026-09-24",
    ]

    filtered = store.contract_history(
        "PETRJ510",
        start=date(2026, 9, 23),
        end=date(2026, 9, 23),
    )
    assert filtered["observations"] == 1
    assert filtered["points"][0]["ref_date"] == "2026-09-23"



def test_historical_publish_does_not_move_latest_backwards(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)

    newest = _payload("2026-09-24", 50.20)
    oldest = _payload("2026-09-22", 49.10)

    store.publish(newest)
    store.publish(oldest)

    latest = store.load_latest("PETR4")
    assert latest.ref_date == date(2026, 9, 24)
    assert latest.payload["underlying"]["spot"] == 50.20

    assert store.load("PETR4", date(2026, 9, 22)).payload["underlying"]["spot"] == 49.10


def test_contract_registry_preserves_contract_after_it_leaves_latest(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)

    first = _payload("2026-09-23", 49.60)
    store.publish(first)

    next_day = _payload("2026-09-24", 50.10)
    next_day["expirations"][0]["rows"][0]["call"] = None
    store.publish(next_day)

    assert store.load_latest("PETR4").ref_date == date(2026, 9, 24)

    archived = store.find_contract("PETRJ510")
    assert archived["ref_date"] == "2026-09-23"
    assert archived["contract"]["ticker"] == "PETRJ510"
    assert archived["underlying"]["ticker"] == "PETR4"

    contracts = store.list_contracts(underlying="PETR4")
    call = next(item for item in contracts if item["ticker"] == "PETRJ510")
    assert call["first_seen"] == "2026-09-23"
    assert call["last_seen"] == "2026-09-23"


def test_registry_first_seen_moves_back_during_backfill_without_regressing_last_seen(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)

    store.publish(_payload("2026-09-24", 50.10))
    store.publish(_payload("2026-09-22", 49.10))

    contracts = store.list_contracts(underlying="PETR4")
    call = next(item for item in contracts if item["ticker"] == "PETRJ510")

    assert call["first_seen"] == "2026-09-22"
    assert call["last_seen"] == "2026-09-24"
    assert call["ref_date"] == "2026-09-24"
    assert call["last"] == 2.20



def _backfill_point(ref_date: str, last: float):
    return {
        "ref_date": ref_date,
        "source": "B3_COTAHIST_BACKFILL",
        "underlying_spot": 48.00,
        "last": last,
        "bid": last - 0.10,
        "ask": last + 0.10,
        "spread_pct": 10.0,
        "quote_state": "TWO_SIDED",
        "quality_flags": [],
        "trade_count": 10,
        "volume": 1000,
        "financial_volume": 2000.0,
        "open_interest": None,
        "price_for_model": None,
        "price_basis": None,
        "risk_free_rate": None,
        "iv": None,
        "delta": None,
        "gamma": None,
        "theta": None,
        "vega": None,
        "rho": None,
        "intrinsic": None,
        "extrinsic": None,
    }


def test_cotahist_backfill_merges_with_snapshot_and_snapshot_wins_same_date(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    store.publish(_history_payload(
        "2026-09-24",
        spot=50.10,
        last=2.40,
        iv=0.45,
        open_interest=1400,
        volume=200,
    ))

    store.publish_cotahist_backfill(
        underlying="PETR4",
        contract="PETRJ510",
        year=2026,
        points=[
            _backfill_point("2026-09-22", 2.00),
            _backfill_point("2026-09-24", 9.99),
        ],
    )

    history = store.contract_history("PETRJ510")

    assert [point["ref_date"] for point in history["points"]] == [
        "2026-09-22",
        "2026-09-24",
    ]

    backfill = history["points"][0]
    assert backfill["source"] == "B3_COTAHIST_BACKFILL"
    assert backfill["last"] == 2.00
    assert backfill["iv"] is None
    assert backfill["open_interest"] is None

    current = history["points"][1]
    assert current["source"] == "BOLSABR_SNAPSHOT"
    assert current["last"] == 2.40
    assert current["iv"] == 0.45
    assert current["open_interest"] == 1400


def test_backfill_requires_registered_contract(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    with pytest.raises(SnapshotNotFound):
        store.publish_cotahist_backfill(
            underlying="PETR4",
            contract="PETRJ510",
            year=2026,
            points=[_backfill_point("2026-09-22", 2.00)],
        )
