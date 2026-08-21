from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def copy_file(source: Path, destination: Path, records: list[dict[str, object]]) -> None:
    if not source.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    records.append(
        {
            "source": str(source.relative_to(ROOT)),
            "backup": display_path(destination),
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
        }
    )


def copy_tree(source: Path, destination: Path, records: list[dict[str, object]]) -> None:
    if not source.exists():
        return
    for item in source.rglob("*"):
        if item.is_file():
            copy_file(item, destination / item.relative_to(source), records)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup demo-critical local artifacts.")
    parser.add_argument("--output", type=Path, help="Optional backup directory.")
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = args.output or (ROOT / "artifacts" / "backups" / f"demo_{stamp}")
    backup = backup.resolve()
    backup.mkdir(parents=True, exist_ok=False)

    records: list[dict[str, object]] = []
    copy_tree(ROOT / "models", backup / "models", records)
    copy_tree(ROOT / "data", backup / "data", records)
    copy_file(
        ROOT / "artifacts" / "control_plane.sqlite3",
        backup / "artifacts" / "control_plane.sqlite3",
        records,
    )

    if not records:
        shutil.rmtree(backup)
        raise RuntimeError("No demo-critical files were found to back up")

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(ROOT),
        "file_count": len(records),
        "files": records,
        "status": "ok",
    }
    manifest_path = backup / "backup_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"backup": str(backup), **{k: manifest[k] for k in ("file_count", "status")}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
