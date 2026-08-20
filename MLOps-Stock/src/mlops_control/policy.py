"""Decision policy for drift alerts and candidate retraining."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class DriftPolicyConfig:
    min_samples: int = 20
    critical_feature_count: int = 2
    consecutive_checks: int = 2
    performance_degradation_ratio: float = 1.20
    directional_accuracy_floor: float = 45.0
    cooldown_minutes: int = 360


@dataclass
class PolicyDecision:
    severity: str
    action: str
    reason: str
    policy_version: str = "v1"
    details: dict[str, Any] | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def evaluate_policy(
    drift_summary: dict[str, Any],
    performance: dict[str, Any] | None = None,
    consecutive_critical_checks: int = 0,
    last_retrain_at: datetime | None = None,
    now: datetime | None = None,
    config: DriftPolicyConfig | None = None,
) -> PolicyDecision:
    config = config or DriftPolicyConfig()
    now = now or datetime.now(timezone.utc)
    critical_features = len(drift_summary.get("critical_features", []))
    warning_features = len(drift_summary.get("warning_features", []))
    evaluated = int(drift_summary.get("evaluated_features", 0))

    if evaluated == 0:
        return PolicyDecision("insufficient_sample", "observe", "no feature has enough observations")

    performance_severity = (performance or {}).get("severity", "stable")
    page_hinkley_detected = bool((performance or {}).get("page_hinkley", {}).get("detected"))
    critical = critical_features >= config.critical_feature_count or performance_severity == "critical" or page_hinkley_detected
    warning = warning_features > 0 or performance_severity == "warning"

    if not critical:
        return PolicyDecision(
            "warning" if warning else "stable",
            "alert" if warning else "observe",
            "feature or performance distribution changed" if warning else "no actionable drift",
            details={"critical_features": critical_features, "warning_features": warning_features},
        )

    if consecutive_critical_checks < config.consecutive_checks:
        return PolicyDecision("critical_pending", "alert", "critical signal has not persisted for the required checks")

    if last_retrain_at is not None:
        if last_retrain_at.tzinfo is None:
            last_retrain_at = last_retrain_at.replace(tzinfo=timezone.utc)
        if now - last_retrain_at < timedelta(minutes=config.cooldown_minutes):
            return PolicyDecision("critical_cooldown", "alert", "retraining cooldown is active")

    return PolicyDecision(
        "critical",
        "retrain",
        "persistent drift or performance degradation passed retraining policy",
        details={"critical_features": critical_features, "performance": performance or {}},
    )


def evaluation_gate(candidate: dict[str, float], champion: dict[str, float] | None, max_mae_regression: float = 0.02) -> dict[str, Any]:
    """Compare candidate and champion metrics without assuming a fixed scale."""
    if not champion:
        return {"passed": True, "reason": "no champion exists", "checks": {"first_model": True}}
    candidate_mae = float(candidate.get("mae", float("inf")))
    champion_mae = float(champion.get("mae", float("inf")))
    candidate_rmse = float(candidate.get("rmse", float("inf")))
    champion_rmse = float(champion.get("rmse", float("inf")))
    candidate_da = float(candidate.get("directional_acc", 0.0))
    champion_da = float(champion.get("directional_acc", 0.0))
    mae_ok = candidate_mae <= champion_mae * (1.0 + max_mae_regression)
    rmse_ok = candidate_rmse <= champion_rmse * (1.0 + max_mae_regression)
    da_ok = candidate_da >= champion_da - 2.0
    return {
        "passed": bool(mae_ok and rmse_ok and da_ok),
        "reason": "candidate satisfies metric gate" if mae_ok and rmse_ok and da_ok else "candidate regression detected",
        "checks": {"mae_ok": mae_ok, "rmse_ok": rmse_ok, "directional_accuracy_ok": da_ok},
        "candidate": candidate,
        "champion": champion,
    }
