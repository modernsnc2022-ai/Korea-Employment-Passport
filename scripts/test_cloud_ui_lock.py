"""Check rejection before a second runner can start browsers or replace evidence."""
import fcntl
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
ROOT=Path(__file__).resolve().parents[1]
common=Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=ROOT,text=True).strip())
if not common.is_absolute():common=ROOT/common
with TemporaryDirectory() as output, (common/'kep-cloud-ui.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    result=subprocess.run([sys.executable,str(ROOT/'scripts/run_cloud_ui.py'),'--output',output],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==2, result.stdout+result.stderr
    assert 'CLOUD_UI_BUSY' in result.stdout
    assert not list(Path(output).iterdir()), 'busy run must not create or overwrite evidence'
print('CLOUD_UI_LOCK_PASS')
