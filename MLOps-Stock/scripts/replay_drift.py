from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.mlops_control.drift import dataframe_drift_summary, feature_drift_report
from src.mlops_control.policy import DriftPolicyConfig, evaluate_policy

FEATURES = [
    "open", "high", "low", "close", "volume", "sma_10", "sma_20", "rsi", "macd", "macd_signal", "bb_upper", "bb_lower", "log_return",
]


def replay(symbol: str, reference_size: int = 120, current_size: int = 30, step: int = 30) -> dict:
    path = Path("data") / f"{symbol.upper()}.csv"
    df = pd.read_csv(path, index_col=0, parse_dates=True).dropna(subset=FEATURES)
    checks = []
    critical_checks = 0
    start = reference_size
    while start + current_size <= len(df):
        reference = df.iloc[start - reference_size:start][FEATURES]
        current = df.iloc[start:start + current_size][FEATURES]
        summary = dataframe_drift_summary(feature_drift_report(reference, current, FEATURES, min_samples=20))
        if summary["critical_features"]:
            critical_checks += 1
        else:
            critical_checks = 0
        decision = evaluate_policy(summary, consecutive_critical_checks=critical_checks, config=DriftPolicyConfig())
        checks.append({"reference_end": str(df.index[start - 1]), "current_end": str(df.index[start + current_size - 1]), "summary": summary, "decision": decision.as_dict()})
        start += step
    return {"symbol": symbol.upper(), "reference_size": reference_size, "current_size": current_size, "checks": checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="FPT")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    report = replay(args.symbol)
    output = Path(args.output or f"artifacts/evaluation/{args.symbol.upper()}_drift_replay.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    critical = sum(1 for item in report["checks"] if item["decision"]["action"] == "retrain")
    print(f"saved={output} checks={len(report['checks'])} retrain_decisions={critical}")
