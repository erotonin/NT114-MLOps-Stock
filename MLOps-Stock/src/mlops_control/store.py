"""SQLite persistence for local MLOps control-plane events."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EventStore:
    def __init__(self, path: str = "artifacts/control_plane.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS prediction_logs (
                    id TEXT PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    horizon INTEGER NOT NULL,
                    current_price REAL,
                    prediction REAL,
                    model_version TEXT,
                    feature_version TEXT,
                    generated_at TEXT NOT NULL,
                    ground_truth REAL,
                    absolute_error REAL,
                    directional_correct INTEGER,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS drift_events (
                    id TEXT PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    action TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS retrain_jobs (
                    id TEXT PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    horizon INTEGER NOT NULL,
                    trigger_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_prediction_ticker_time ON prediction_logs(ticker, generated_at);
                CREATE INDEX IF NOT EXISTS idx_drift_ticker_time ON drift_events(ticker, created_at);
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_prediction(self, payload: dict[str, Any]) -> dict[str, Any]:
        record = {
            "id": payload.get("id", str(uuid.uuid4())),
            "ticker": payload["ticker"].upper(),
            "horizon": int(payload.get("horizon", 3)),
            "current_price": payload.get("current_price"),
            "prediction": payload.get("prediction", payload.get("predicted_t3")),
            "model_version": payload.get("model_version", "unknown"),
            "feature_version": payload.get("feature_version", "unknown"),
            "generated_at": payload.get("generated_at", self._now()),
            "ground_truth": payload.get("ground_truth"),
            "absolute_error": payload.get("absolute_error"),
            "directional_correct": payload.get("directional_correct"),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO prediction_logs
                (id, ticker, horizon, current_price, prediction, model_version, feature_version,
                 generated_at, ground_truth, absolute_error, directional_correct, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (*[record[key] for key in record], json.dumps(payload, ensure_ascii=False)),
            )
        return record

    def list_predictions(self, ticker: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = "SELECT * FROM prediction_logs"
        args: list[Any] = []
        if ticker:
            query += " WHERE ticker = ?"
            args.append(ticker.upper())
        query += " ORDER BY generated_at DESC LIMIT ?"
        args.append(int(limit))
        with self._connect() as conn:
            return [dict(row) for row in conn.execute(query, args).fetchall()]

    def update_ground_truth(self, prediction_id: str, ground_truth: float) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM prediction_logs WHERE id = ?", (prediction_id,)).fetchone()
            if row is None:
                return None
            error = abs(float(row["prediction"]) - float(ground_truth)) if row["prediction"] is not None else None
            direction = None
            if row["current_price"] is not None and row["prediction"] is not None:
                direction = int((float(row["prediction"]) >= float(row["current_price"])) == (float(ground_truth) >= float(row["current_price"])))
            conn.execute(
                "UPDATE prediction_logs SET ground_truth=?, absolute_error=?, directional_correct=? WHERE id=?",
                (ground_truth, error, direction, prediction_id),
            )
            updated = dict(conn.execute("SELECT * FROM prediction_logs WHERE id = ?", (prediction_id,)).fetchone())
        return updated

    def add_drift_event(self, ticker: str, severity: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = {"id": str(uuid.uuid4()), "ticker": ticker.upper(), "severity": severity, "action": action, "created_at": self._now(), "payload": payload}
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO drift_events(id, ticker, severity, action, created_at, payload) VALUES (?, ?, ?, ?, ?, ?)",
                (record["id"], record["ticker"], severity, action, record["created_at"], json.dumps(payload, ensure_ascii=False)),
            )
        return record

    def list_drift_events(self, ticker: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = "SELECT * FROM drift_events"
        args: list[Any] = []
        if ticker:
            query += " WHERE ticker = ?"
            args.append(ticker.upper())
        query += " ORDER BY created_at DESC LIMIT ?"
        args.append(int(limit))
        with self._connect() as conn:
            rows = []
            for row in conn.execute(query, args).fetchall():
                item = dict(row)
                item["payload"] = json.loads(item["payload"])
                rows.append(item)
            return rows

    def create_job(self, ticker: str, horizon: int, trigger_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        now = self._now()
        record = {"id": str(uuid.uuid4()), "ticker": ticker.upper(), "horizon": horizon, "trigger_type": trigger_type, "status": "queued", "created_at": now, "updated_at": now, "payload": payload or {}}
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO retrain_jobs(id, ticker, horizon, trigger_type, status, created_at, updated_at, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (record["id"], record["ticker"], horizon, trigger_type, "queued", now, now, json.dumps(record["payload"], ensure_ascii=False)),
            )
        return record

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM retrain_jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["payload"] = json.loads(result["payload"])
            return result

    def update_job(self, job_id: str, status: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
        now = self._now()
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM retrain_jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                return None
            merged = json.loads(row["payload"])
            merged.update(payload or {})
            conn.execute("UPDATE retrain_jobs SET status=?, updated_at=?, payload=? WHERE id=?", (status, now, json.dumps(merged, ensure_ascii=False), job_id))
            result = dict(conn.execute("SELECT * FROM retrain_jobs WHERE id = ?", (job_id,)).fetchone())
            result["payload"] = json.loads(result["payload"])
            return result

    def list_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = []
            for row in conn.execute("SELECT * FROM retrain_jobs ORDER BY created_at DESC LIMIT ?", (int(limit),)).fetchall():
                item = dict(row)
                item["payload"] = json.loads(item["payload"])
                rows.append(item)
            return rows

    def performance_summary(self, ticker: str | None = None, limit: int = 100) -> dict[str, Any]:
        rows = self.list_predictions(ticker=ticker, limit=limit)
        labelled = [row for row in rows if row["absolute_error"] is not None]
        errors = [float(row["absolute_error"]) for row in labelled]
        directions = [int(row["directional_correct"]) for row in labelled if row["directional_correct"] is not None]
        return {
            "ticker": ticker.upper() if ticker else "ALL",
            "sample_size": len(labelled),
            "mae": sum(errors) / len(errors) if errors else None,
            "directional_accuracy": 100.0 * sum(directions) / len(directions) if directions else None,
            "latest_label_time": labelled[0]["generated_at"] if labelled else None,
        }
