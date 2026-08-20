#!/usr/bin/env bash
set -u
for file in /tmp/mlops-*.pid; do
  [[ -f "$file" ]] || continue
  pid=$(cat "$file" 2>/dev/null || true)
  if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi
  rm -f "$file"
done
echo "Local MLOps services stopped where owned by this script."
