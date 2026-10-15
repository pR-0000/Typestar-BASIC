"""Package .83 after offline firmware/Studio regression tests; never flash."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib,json,subprocess,os
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'build/native-strings'
cpu=(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
m=json.loads((out/'manifest.json').read_text());digest=hashlib.sha256(cpu).hexdigest()
assert len(cpu)==32768 and digest==m['sha256'] and m['version']=='0.4.83-dev'
env=os.environ.copy();env['TYPESTAR_TEST_FIRMWARE']=str(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin')
r=subprocess.run([str(ROOT/'studio/.venv/Scripts/python.exe'),'-m','unittest','discover','-s','studio','-p','test_*.py','-v'],cwd=ROOT,env=env,capture_output=True,text=True)
(out/'validation.txt').write_text(r.stdout+r.stderr,encoding='utf-8')
assert r.returncode==0,r.stdout+r.stderr
report=dict(result='PASS',sha256=digest,command='unittest discover -s studio -p test_*.py',physical_validation='pending')
(out/'validation.json').write_text(json.dumps(report,indent=2))
raw=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.83-dev-canon-start-nh7.bin';target=ROOT/'release'/name
assert not target.exists() or target.read_bytes()==raw
target.write_bytes(raw);h=hashlib.sha256(raw).hexdigest()
target.with_suffix('.sha256').write_text(h+'  '+name+'\n')
m.update(status='Offline tests passed; physical native accented strings pending',nh7_sha256=h)
(out/'manifest.json').write_text(json.dumps(m,indent=2))
target.with_name(target.stem+'-manifest.json').write_text(json.dumps(m,indent=2))
print('PASS',name,h)
