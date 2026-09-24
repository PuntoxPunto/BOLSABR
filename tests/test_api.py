from fastapi.testclient import TestClient

from bolsabr.api.app import create_app
from bolsabr.serving.snapshot_store import FilesystemSnapshotStore


def _payload():
    return {
        "schema_version": "0.1",
        "ref_date": "2026-09-23",
        "market_data_source": "B3_EOD",
        "rate_source": "B3_DI1",
        "underlying": {"ticker": "PETR4", "spot": 49.60},
        "fallback_risk_free_rate": 0.12,
        "dividend_yield": 0.0,
        "expirations": [
            {
                "date": "2026-10-16",
                "type": "MONTHLY",
                "dte_calendar": 23,
                "dte_business": 16,
                "risk_free_rate": 0.125,
                "rows": [{"strike": 49.61, "call": None, "put": None}],
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


def _client(tmp_path):
    FilesystemSnapshotStore(tmp_path).publish(_payload())
    return TestClient(create_app(tmp_path))


def test_healthz_does_not_need_market_data(tmp_path):
    client = TestClient(create_app(tmp_path))
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_latest_option_chain_is_served_with_eod_cache_headers(tmp_path):
    client = _client(tmp_path)
    response = client.get("/v1/assets/PETR4/options")

    assert response.status_code == 200
    assert response.json()["schema_version"] == "0.1"
    assert response.json()["underlying"]["ticker"] == "PETR4"
    assert "max-age=300" in response.headers["cache-control"]
    assert response.headers["etag"].startswith('"')


def test_expiration_filter_keeps_api_contract_and_one_expiry(tmp_path):
    client = _client(tmp_path)
    response = client.get(
        "/v1/assets/PETR4/options",
        params={"expiration": "2026-10-16"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["underlying"]["ticker"] == "PETR4"
    assert [item["date"] for item in payload["expirations"]] == ["2026-10-16"]


def test_filtered_and_full_responses_have_different_etags(tmp_path):
    client = _client(tmp_path)
    full = client.get("/v1/assets/PETR4/options")
    filtered = client.get(
        "/v1/assets/PETR4/options",
        params={"expiration": "2026-10-16"},
    )
    assert full.headers["etag"] != filtered.headers["etag"]


def test_if_none_match_returns_304(tmp_path):
    client = _client(tmp_path)
    first = client.get("/v1/assets/PETR4/options")
    second = client.get(
        "/v1/assets/PETR4/options",
        headers={"If-None-Match": first.headers["etag"]},
    )
    assert second.status_code == 304
    assert second.content == b""


def test_missing_ticker_returns_404(tmp_path):
    client = _client(tmp_path)
    response = client.get("/v1/assets/VALE3/options")
    assert response.status_code == 404


def test_missing_expiration_returns_404(tmp_path):
    client = _client(tmp_path)
    response = client.get(
        "/v1/assets/PETR4/options",
        params={"expiration": "2027-01-15"},
    )
    assert response.status_code == 404



def test_asset_catalog_lists_published_tickers_and_supports_query(tmp_path):
    store = FilesystemSnapshotStore(tmp_path)
    store.publish(_payload())

    vale = _payload()
    vale["underlying"]["ticker"] = "VALE3"
    vale["underlying"]["spot"] = 61.25
    store.publish(vale)

    client = TestClient(create_app(tmp_path))

    response = client.get("/v1/assets")
    assert response.status_code == 200
    assert [item["ticker"] for item in response.json()["assets"]] == ["PETR4", "VALE3"]

    filtered = client.get("/v1/assets", params={"q": "vale"})
    assert filtered.status_code == 200
    assert [item["ticker"] for item in filtered.json()["assets"]] == ["VALE3"]
    assert filtered.json()["assets"][0]["spot"] == 61.25
