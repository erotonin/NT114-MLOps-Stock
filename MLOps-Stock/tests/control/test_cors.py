from fastapi.testclient import TestClient

from services.control_api.main import app


def test_cors_allows_local_dashboard_origin_only():
    client = TestClient(app)
    allowed = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:8081",
            "Access-Control-Request-Method": "GET",
        },
    )
    denied = client.options(
        "/health",
        headers={
            "Origin": "https://example.invalid",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.status_code == 200
    assert allowed.headers.get("access-control-allow-origin") == "http://127.0.0.1:8081"
    assert "access-control-allow-origin" not in denied.headers
