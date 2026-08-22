"""Offline structural validation for Helm-rendered Kubernetes YAML."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_rendered_yaml.py <rendered.yaml>")
        return 2
    path = Path(sys.argv[1])
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16")
    else:
        text = raw.decode("utf-8-sig")
    docs = [doc for doc in yaml.safe_load_all(text) if doc]
    if not docs:
        print("no Kubernetes documents found")
        return 1
    missing = []
    identities = []
    for idx, doc in enumerate(docs, 1):
        if not isinstance(doc, dict):
            missing.append(f"document {idx}: not a mapping")
            continue
        for key in ("apiVersion", "kind", "metadata"):
            if key not in doc:
                missing.append(f"document {idx}: missing {key}")
        metadata = doc.get("metadata") or {}
        if not metadata.get("name"):
            missing.append(f"document {idx}: missing metadata.name")
        identities.append(f"{doc.get('kind','?')}/{metadata.get('name','?')}")
    if missing:
        print("structural errors:")
        print("\n".join(missing))
        return 1
    print(f"offline-yaml-validation: ok ({len(docs)} documents)")
    print("\n".join(identities))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
