"""Small auditable registry used by the local control plane.

MLflow remains the experiment/artifact system for cluster deployments. This
filesystem registry makes the complete workflow runnable without requiring a
Kubernetes cluster or an MLflow server during development and testing.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Registry:
    def __init__(self, path: str | os.PathLike[str] = "artifacts/registry/registry.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        if not self.path.exists():
            self._write({"models": {}, "audit": []})

    def _read(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {"models": {}, "audit": []}

    def _write(self, payload: dict[str, Any]) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _audit(self, payload: dict[str, Any], action: str, actor: str, details: dict[str, Any]) -> None:
        payload.setdefault("audit", []).append(
            {"event_id": str(uuid.uuid4()), "timestamp": self._now(), "action": action, "actor": actor, **details}
        )

    def register(
        self,
        model_name: str,
        metrics: dict[str, float],
        artifact_path: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "system",
    ) -> dict[str, Any]:
        with self._lock:
            payload = self._read()
            model = payload.setdefault("models", {}).setdefault(model_name, {"versions": [], "champion": None})
            version = str(len(model["versions"]) + 1)
            record = {
                "version": version,
                "model_name": model_name,
                "status": "candidate",
                "metrics": metrics,
                "artifact_path": artifact_path,
                "metadata": metadata or {},
                "created_at": self._now(),
            }
            model["versions"].append(record)
            self._audit(payload, "register_candidate", actor, {"model_name": model_name, "version": version})
            self._write(payload)
            return record

    def list_models(self) -> list[dict[str, Any]]:
        payload = self._read()
        result = []
        for name, model in payload.get("models", {}).items():
            result.append(
                {
                    "model_name": name,
                    "champion": model.get("champion"),
                    "latest_version": model.get("versions", [])[-1] if model.get("versions") else None,
                    "version_count": len(model.get("versions", [])),
                }
            )
        return result

    def get_model(self, model_name: str) -> dict[str, Any] | None:
        return self._read().get("models", {}).get(model_name)

    def get_version(self, model_name: str, version: str) -> dict[str, Any] | None:
        model = self.get_model(model_name)
        if not model:
            return None
        return next((item for item in model.get("versions", []) if item["version"] == str(version)), None)

    def get_champion(self, model_name: str) -> dict[str, Any] | None:
        model = self.get_model(model_name)
        if not model or not model.get("champion"):
            return None
        return self.get_version(model_name, model["champion"])

    def promote(self, model_name: str, version: str, actor: str = "system", reason: str = "evaluation_gate_passed") -> dict[str, Any]:
        with self._lock:
            payload = self._read()
            model = payload.get("models", {}).get(model_name)
            if not model:
                raise KeyError(f"Unknown model: {model_name}")
            candidate = next((item for item in model["versions"] if item["version"] == str(version)), None)
            if not candidate:
                raise KeyError(f"Unknown version: {model_name}:{version}")
            previous = model.get("champion")
            for item in model["versions"]:
                if item["status"] == "champion":
                    item["status"] = "previous_champion"
            candidate["status"] = "champion"
            candidate["promoted_at"] = self._now()
            candidate["promotion_reason"] = reason
            model["champion"] = str(version)
            self._audit(payload, "promote", actor, {"model_name": model_name, "version": str(version), "previous": previous, "reason": reason})
            self._write(payload)
            return candidate

    def reject(self, model_name: str, version: str, actor: str = "system", reason: str = "evaluation_gate_failed") -> dict[str, Any]:
        with self._lock:
            payload = self._read()
            model = payload.get("models", {}).get(model_name)
            if not model:
                raise KeyError(f"Unknown model: {model_name}")
            candidate = next((item for item in model["versions"] if item["version"] == str(version)), None)
            if not candidate:
                raise KeyError(f"Unknown version: {model_name}:{version}")
            candidate["status"] = "rejected"
            candidate["rejection_reason"] = reason
            candidate["rejected_at"] = self._now()
            self._audit(payload, "reject", actor, {"model_name": model_name, "version": str(version), "reason": reason})
            self._write(payload)
            return candidate

    def rollback(self, model_name: str, version: str, actor: str = "admin", reason: str = "manual_rollback") -> dict[str, Any]:
        return self.promote(model_name, version, actor=actor, reason=reason)

    def audit(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._read().get("audit", [])[-limit:][::-1]
