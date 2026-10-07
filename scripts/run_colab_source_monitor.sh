#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
MODE="${2:-check}"
cd "$ROOT"

echo "KEP_SOURCE_MONITOR_START sha=$(git rev-parse HEAD) mode=$MODE"
if [[ "$MODE" == "accept-current" ]]; then
  python3 scripts/check_official_sources.py --accept-current
else
  python3 scripts/check_official_sources.py
fi
python3 scripts/write_source_review_status.py
echo "KEP_SOURCE_MONITOR_DONE sha=$(git rev-parse HEAD) mode=$MODE"
