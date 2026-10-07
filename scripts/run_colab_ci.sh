#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT"

echo "KEP_COLAB_CI_START sha=$(git rev-parse HEAD)"
python3 --version
node --version
npm --version

npm ci
npx playwright install --with-deps chromium

for f in docs/app.js docs/landing.js docs/app-runtime.js docs/beta.js docs/sw.js docs/country-pack.js docs/readiness.js; do
  node --check "$f"
done

python3 - <<'PY'
import json, pathlib, subprocess
files=subprocess.check_output(["git","ls-files","*.json","docs/manifest.webmanifest"],text=True).splitlines()
for name in files:
    with open(name,encoding="utf-8") as fh:
        json.load(fh)
print(f"JSON_VALIDATION_PASS files={len(files)}")
PY

python3 -m compileall -q scripts

checks=(
  "python3 scripts/test_source_normalization.py"
  "python3 scripts/test_source_review_status.py"
  "python3 scripts/check_webapp_contract.py"
  "python3 scripts/check_country_pack_contract.py"
  "python3 scripts/check_hrd_examnot_linkage.py"
  "python3 scripts/check_myanmar_manufacturing_gate.py"
  "python3 scripts/check_next_review_monitor_coverage.py"
  "python3 scripts/check_bqc_scopes.py"
  "python3 scripts/check_beta_tracker.py"
  "python3 scripts/check_beta_launch_readiness.py --allow-source-review-pending"
  "python3 scripts/report_beta_progress.py --self-test"
  "python3 scripts/report_beta_progress.py"
  "python3 scripts/parse_beta_interest.py --self-test"
  "python3 scripts/assign_beta_slot.py --self-test"
  "python3 scripts/record_beta_feedback.py --self-test"
  "python3 scripts/record_zero_broker_evidence.py --self-test"
  "python3 scripts/record_manufacturing_launch_check.py --self-test"
  "python3 scripts/set_beta_release.py --self-test"
  "python3 scripts/set_worker_panel_release.py --self-test"
  "python3 scripts/assign_worker_validator.py --self-test"
  "python3 scripts/parse_worker_interest.py --self-test"
  "python3 scripts/check_outreach_send_guard.py --self-test"
  "python3 scripts/check_outreach_send_guard.py --audit"
  "python3 scripts/record_worker_interview.py --self-test"
  "python3 scripts/publish_worker_evidence.py --self-test"
  "python3 scripts/check_workplace_worker_evidence.py"
)
for cmd in "${checks[@]}"; do
  echo "+ $cmd"
  bash -lc "$cmd"
done

nohup python3 -m http.server 4173 --directory docs >/tmp/kep-http.log 2>&1 &
HTTP_PID=$!
cleanup(){ kill "$HTTP_PID" >/dev/null 2>&1 || true; }
trap cleanup EXIT

for i in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:4173/app.html >/dev/null; then break; fi
  sleep 1
done
curl -fsS http://127.0.0.1:4173/app.html >/dev/null
npm run test:ui

python3 scripts/check_beta_launch_readiness.py

echo "KEP_COLAB_CI_PASS sha=$(git rev-parse HEAD)"
