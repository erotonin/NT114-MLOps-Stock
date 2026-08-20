from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYMBOL = "FPT"
MODELS = ROOT / "models"
DATA = ROOT / "data" / f"{SYMBOL}.csv"
MANIFEST_PATH = MODELS / f"{SYMBOL}_artifact_manifest.json"

manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
required_features = [
    "open", "high", "low", "close", "volume", "sma_10", "sma_20", "rsi",
    "macd", "macd_signal", "bb_upper", "bb_lower", "log_return",
]
assert manifest["symbol"] == SYMBOL
assert manifest["features"] == required_features
assert manifest["meta_input_space"] == "scaled_target"
assert DATA.exists() and DATA.stat().st_size > 0

hashes = {}
for filename in manifest["artifacts"]:
    path = MODELS / filename
    assert path.exists() and path.stat().st_size > 0, f"missing artifact: {path}"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    hashes[filename] = {"bytes": path.stat().st_size, "sha256": digest}

report = {
    "symbol": SYMBOL,
    "manifest": str(MANIFEST_PATH.relative_to(ROOT)),
    "data": {"path": str(DATA.relative_to(ROOT)), "bytes": DATA.stat().st_size},
    "model_artifacts": hashes,
    "feature_count": len(required_features),
    "status": "ok",
}
out = ROOT / "artifacts" / "reproducibility_verification.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
