from fastapi.testclient import TestClient

from services.control_api.main import app


client = TestClient(app)


def test_feature_catalog_is_readable_by_viewer():
    response = client.get("/features", headers={"X-Role": "viewer"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["feature_store_version"] == "v1"
    assert {item["symbol"] for item in payload["symbols"]} >= {"FPT", "VCB", "VNM", "HPG"}


def test_feature_detail_contains_schema_and_hash():
    response = client.get("/features/FPT", headers={"X-Role": "viewer"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "FPT"
    assert payload["row_count"] > 0
    assert payload["null_count"] == 0
    assert len(payload["sha256"]) == 64


def test_feature_detail_rejects_invalid_ticker():
    response = client.get("/features/FPT-", headers={"X-Role": "viewer"})
    assert response.status_code == 422


def test_control_query_limit_rejects_invalid_boundaries():
    for path in ("/predictions", "/performance", "/drift/events", "/retrain/jobs", "/audit"):
        response = client.get(path + "?limit=0", headers={"X-Role": "viewer"})
        assert response.status_code == 422, path
        response = client.get(path + "?limit=1001", headers={"X-Role": "viewer"})
        assert response.status_code == 422, path
