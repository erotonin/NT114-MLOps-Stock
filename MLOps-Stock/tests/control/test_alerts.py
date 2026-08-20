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
