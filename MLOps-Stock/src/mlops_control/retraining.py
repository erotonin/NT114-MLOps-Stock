"""Background retraining worker for the local and Kubernetes control plane."""

from __future__ import annotations

import json
import os
import shutil
import threading
from pathlib import Path
from typing import Any

from src.mlops_control.policy import evaluation_gate
from src.mlops_control.registry import Registry
from src.mlops_control.store import EventStore


class RetrainingService:
    def __init__(self, store: EventStore | None = None, registry: Registry | None = None) -> None:
        self.store = store or EventStore()
        self.registry = registry or Registry()

    def start(self, ticker: str, horizon: int = 3, trigger_type: str = "manual", epochs: int | None = None) -> dict[str, Any]:
        symbol = ticker.upper()
        job = self.store.create_job(symbol, horizon, trigger_type, {"epochs": epochs or int(os.getenv("RETRAIN_EPOCHS", "5"))})
        thread = threading.Thread(target=self._run, args=(job["id"], symbol, horizon), daemon=True)
        thread.start()
        return job

    def _run(self, job_id: str, symbol: str, horizon: int) -> None:
        self.store.update_job(job_id, "running")
        try:
            # Training dependencies are intentionally lazy: the control API can
            # serve health, drift, registry and audit endpoints without loading
            # PyTorch/LightGBM. They are imported only when a retraining job runs.
            from src.data_pipeline.download_latest import download_all
            from src.training.ensemble_trainer import train_ensemble

            project_root = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[2]))
            data_dir = project_root / "data"
            models_dir = project_root / "models"
            artifact_root = project_root / "artifacts" / "mlflow"
            artifact_root.mkdir(parents=True, exist_ok=True)
            if not os.getenv("MLFLOW_TRACKING_URI") or os.getenv("MLFLOW_TRACKING_URI", "").startswith("file:"):
                os.environ["MLFLOW_TRACKING_URI"] = f"sqlite:///{project_root / 'mlflow.db'}"
            os.environ.setdefault("MLFLOW_ARTIFACT_ROOT", str(artifact_root))
            job = self.store.get_job(job_id)
            if job is None:
                raise RuntimeError(f"Retrain job {job_id} disappeared")
            epochs = int(job["payload"].get("epochs", 5))
            model_name = f"stock-ensemble-{symbol}-t{horizon}"
            manifest_path = models_dir / f"{symbol}_artifact_manifest.json"
            backup_dir = project_root / "artifacts" / "retraining_backups" / job_id
            baseline_manifest = None
            baseline_metrics = None
            if manifest_path.exists():
                try:
                    baseline_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    baseline_metrics = {
                        "mae": float(baseline_manifest["mae"]),
                        "rmse": float(baseline_manifest["rmse"]),
                        "directional_acc": float(baseline_manifest["directional_acc"]),
                    }
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    for artifact_name in baseline_manifest.get("artifacts", []):
                        source = models_dir / artifact_name
                        if source.exists():
                            shutil.copy2(source, backup_dir / artifact_name)
                    shutil.copy2(manifest_path, backup_dir / manifest_path.name)
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    baseline_manifest = None
                    baseline_metrics = None
            download_all([symbol], data_dir=str(data_dir))
            train_ensemble(symbol=symbol, epochs=epochs, window_size=int(os.getenv("TFT_WINDOW_SIZE", "60")), data_dir=str(data_dir), models_dir=str(models_dir))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.setdefault("meta_input_space", "scaled_target")
            manifest.setdefault("model_version", f"retrain-{job_id[:8]}")
            manifest.setdefault("data_version", "retraining-snapshot")
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            metrics = {
                "mae": float(manifest.get("mae", 0.0)),
                "rmse": float(manifest.get("rmse", 0.0)),
                "directional_acc": float(manifest.get("directional_acc", 0.0)),
            }
            champion = self.registry.get_champion(model_name)
            if champion is None and baseline_metrics is not None and baseline_manifest is not None:
                baseline = self.registry.register(
                    model_name=model_name,
                    metrics=baseline_metrics,
                    artifact_path=str(manifest_path),
                    metadata={"ticker": symbol, "horizon": horizon, "trigger": "existing_local_artifact", "manifest": baseline_manifest},
                    actor="retraining-worker",
                )
                champion = self.registry.promote(model_name, baseline["version"], actor="retraining-worker", reason="seeded_from_existing_local_artifact")
            candidate = self.registry.register(
                model_name=model_name,
                metrics=metrics,
                artifact_path=str(manifest_path),
                metadata={"ticker": symbol, "horizon": horizon, "trigger": "retraining", "manifest": manifest},
                actor="retraining-worker",
            )
            gate = evaluation_gate(metrics, champion.get("metrics") if champion else None)
            if gate["passed"]:
                self.registry.promote(model_name, candidate["version"], actor="retraining-worker", reason=gate["reason"])
                status = "promoted"
            else:
                self.registry.reject(model_name, candidate["version"], actor="retraining-worker", reason=gate["reason"])
                if backup_dir.exists():
                    for backup_file in backup_dir.iterdir():
                        if backup_file.name != "":
                            shutil.copy2(backup_file, models_dir / backup_file.name)
                status = "rejected"
            self.store.update_job(job_id, status, {"candidate": candidate, "gate": gate, "baseline_metrics": baseline_metrics})
        except Exception as exc:  # worker boundary: persist failure for operators
            self.store.update_job(job_id, "failed", {"error": str(exc)})


_default_service: RetrainingService | None = None


def get_retraining_service() -> RetrainingService:
    global _default_service
    if _default_service is None:
        _default_service = RetrainingService()
    return _default_service
