"""Package the tested .84 image; never touch hardware."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'build/paper-origin-y'
cpu=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();m=json.loads((base/'manifest.json').read_text())
assert len(cpu)==32768 and hashlib.sha256(cpu).hexdigest()==m['sha256']
assert json.loads((base/'motion-validation.json').read_text())['result']=='PASS'
for name in ('logic-validation.json','paper-validation.json'):
 r=json.loads((ROOT/'build/naval-duel'/name).read_text())
 assert r['sha256']==hashlib.sha256((ROOT/'examples/games/duel-orbital-fr.bas').read_bytes()).hexdigest()
assert 'OK' in (base/'studio-validation.txt').read_text()
raw=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.84-dev-canon-start-nh7.bin';dest=ROOT/'release'/name
assert not dest.exists() or dest.read_bytes()==raw
dest.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest()
dest.with_suffix('.sha256').write_text(digest+'  '+name+'\n')
m.update(status='Offline origin, motor phase, Studio and orbital game tests passed; physical test pending',nh7_sha256=digest)
(base/'manifest.json').write_text(json.dumps(m,indent=2));dest.with_name(dest.stem+'-manifest.json').write_text(json.dumps(m,indent=2))
print(name,digest)
