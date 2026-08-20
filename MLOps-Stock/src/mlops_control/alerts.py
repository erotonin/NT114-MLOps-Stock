"""Optional alert sink for drift and retraining decisions.

The default local mode is deterministic and offline: events are appended to a
JSONL file. A webhook is used only when ALERT_WEBHOOK_URL is explicitly set.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def emit_alert(event: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    log_path = Path(os.getenv("ALERT_LOG_PATH", "artifacts/alerts.jsonl"))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    webhook = os.getenv("ALERT_WEBHOOK_URL")
    if webhook:
        try:
            import requests

            response = requests.post(webhook, json=payload, timeout=5)
            payload["webhook_status"] = response.status_code
        except Exception as exc:  # notification must never break monitoring
            payload["webhook_error"] = str(exc)
    return payload
