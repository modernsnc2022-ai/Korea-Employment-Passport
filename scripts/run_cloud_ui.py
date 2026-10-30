#!/usr/bin/env python3
"""Serial Linux-cloud Playwright runs with owned server and immutable run artifacts."""
import argparse
import hashlib
import fcntl
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output', default='test-results/cloud', help='Parent directory; every attempt gets a distinct subdirectory.')
parser.add_argument('tests', nargs=argparse.REMAINDER)
args = parser.parse_args()
common = Path(subprocess.check_output(['git', 'rev-parse', '--git-common-dir'], cwd=ROOT, text=True).strip())
if not common.is_absolute():
    common = ROOT / common
with (common / 'kep-cloud-ui.lock').open('a+') as lock:
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('CLOUD_UI_BUSY: another serialized run is active in this repository; no tests started.', flush=True)
        raise SystemExit(2)
    preflight = subprocess.run(['node', '-e', "const {chromium}=require('@playwright/test'); (async()=>{const b=await chromium.launch();await b.close()})().catch(e=>{console.error(e.message);process.exit(1)})"], cwd=ROOT, text=True, capture_output=True)
    if preflight.returncode:
        print('CLOUD_UI_UNAVAILABLE: Chromium preflight failed; no test suite started.', flush=True)
        print(preflight.stderr, flush=True)
        raise SystemExit(3)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    parent = Path(args.output).resolve()
    run = parent / stamp
    run.mkdir(parents=True)
    command = ['npx', 'playwright', 'test', *args.tests, '--reporter=line,json', '--output', str(run / 'artifacts'), '--retries=0', '--workers=1']
    metadata = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'startedAt': stamp, 'command': command, 'runDirectory': str(run)}
    metadata['workingTreeStatus'] = subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True).splitlines()
    metadata['trackedDiffSha256'] = hashlib.sha256(subprocess.check_output(['git', 'diff', 'HEAD', '--binary'], cwd=ROOT)).hexdigest()
    (run / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    environment = {**os.environ, 'PLAYWRIGHT_JSON_OUTPUT_NAME': str(run / 'results.json')}
    print('CLOUD_UI_START ' + str(run), flush=True)
    with (run / 'run.log').open('w') as log:
        try:
            result = subprocess.run(command, cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT)
            exit_code = result.returncode
        except KeyboardInterrupt:
            exit_code = 130
            metadata['interrupted'] = True
    metadata['exitCode'] = exit_code
    if (run / 'results.json').exists():
        metadata['stats'] = json.loads((run / 'results.json').read_text())['stats']
    (run / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (parent / 'latest.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print('CLOUD_UI_END ' + json.dumps(metadata.get('stats', {})) + ' exit=' + str(exit_code), flush=True)
    raise SystemExit(exit_code)
