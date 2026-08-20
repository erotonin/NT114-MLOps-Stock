from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    base = {"ensemble": "http://127.0.0.1:8080", "control": "http://127.0.0.1:8085"}
    for service, url in [("ensemble", base["ensemble"] + "/docs"), ("control", base["control"] + "/health")]:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print(f"health {service}: ok")

    prediction = requests.get(base["ensemble"] + "/predict/FPT", timeout=120)
    prediction.raise_for_status()
    payload = prediction.json()
    assert payload["ticker"] == "FPT"
    assert payload["predicted_t3"] is not None
    assert payload["model_version"] != "unknown"
    print("prediction: ok", json.dumps(payload, ensure_ascii=False))

    df = pd.read_csv(ROOT / "data/FPT.csv", index_col=0, parse_dates=True).dropna(subset=["close", "volume"])
    reference = df.iloc[-90:-30][["close", "volume"]].to_dict(orient="records")
    current = df.iloc[-30:][["close", "volume"]].to_dict(orient="records")
    drift = requests.post(
        base["control"] + "/drift/evaluate",
        headers={"X-Role": "analyst"},
        json={"ticker": "FPT", "reference": reference, "current": current, "columns": ["close", "volume"], "consecutive_critical_checks": 2},
        timeout=30,
    )
    drift.raise_for_status()
    drift_payload = drift.json()
    assert "summary" in drift_payload and "decision" in drift_payload
    print("drift evaluation: ok", drift_payload["decision"])

    denied = requests.post(base["control"] + "/retrain", headers={"X-Role": "viewer"}, json={"ticker": "FPT"}, timeout=10)
    assert denied.status_code == 403
    print("RBAC viewer denial: ok")


if __name__ == "__main__":
    main()
