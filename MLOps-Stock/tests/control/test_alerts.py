from __future__ import annotations

import json

from src.mlops_control.alerts import emit_alert


def test_emit_alert_writes_local_jsonl(tmp_path, monkeypatch):
    path = tmp_path / "alerts.jsonl"
    monkeypatch.setenv("ALERT_LOG_PATH", str(path))
    monkeypatch.delenv("ALERT_WEBHOOK_URL", raising=False)

    payload = emit_alert({"ticker": "FPT", "severity": "critical", "action": "retrain"})

    assert payload["ticker"] == "FPT"
    assert payload["action"] == "retrain"
    record = json.loads(path.read_text(encoding="utf-8").strip())
    assert record["severity"] == "critical"
    assert "timestamp" in record


def test_emit_alert_reports_webhook_status(tmp_path, monkeypatch):
    import requests

    monkeypatch.setenv("ALERT_LOG_PATH", str(tmp_path / "alerts.jsonl"))
    monkeypatch.setenv("ALERT_WEBHOOK_URL", "https://example.invalid/hook")

    class Response:
        status_code = 204

    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: Response())
    payload = emit_alert({"ticker": "FPT", "severity": "warning", "action": "alert"})

    assert payload["webhook_status"] == 204


def test_emit_alert_webhook_failure_is_non_blocking(tmp_path, monkeypatch):
    import requests

    monkeypatch.setenv("ALERT_LOG_PATH", str(tmp_path / "alerts.jsonl"))
    monkeypatch.setenv("ALERT_WEBHOOK_URL", "https://example.invalid/hook")

    def fail(*args, **kwargs):
        raise requests.RequestException("test webhook outage")

    monkeypatch.setattr(requests, "post", fail)
    payload = emit_alert({"ticker": "FPT", "severity": "critical", "action": "retrain"})

    assert "webhook_error" in payload
    assert "test webhook outage" in payload["webhook_error"]
    assert (tmp_path / "alerts.jsonl").exists()
