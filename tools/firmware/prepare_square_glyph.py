"""Package .85 only after actual CPU glyph and game validations."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'build/square-glyph'
b=(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();m=json.loads((out/'manifest.json').read_text())
assert len(b)==32768 and hashlib.sha256(b).hexdigest()==m['sha256']
assert json.loads((out/'glyph-validation.json').read_text())['result']=='PASS'
assert 'OK' in (out/'studio-validation.txt').read_text(encoding='utf-8-sig')
r=json.loads((ROOT/'build/naval-duel/paper-validation.json').read_text())
assert r['sha256']==hashlib.sha256((ROOT/'examples/games/duel-orbital-fr.bas').read_bytes()).hexdigest()
assert r['games'][0]['result']=='ABANDON 1-1'
raw=b[16384:]+b[:16384];name='s70-basic-0.4.85-dev-canon-start-nh7.bin';p=ROOT/'release'/name
assert not p.exists() or p.read_bytes()==raw
p.write_bytes(raw);sha=hashlib.sha256(raw).hexdigest();p.with_suffix('.sha256').write_text(sha+'  '+name+'\n')
m.update(nh7_sha256=sha,status='Offline CPU/Studio/glyph/game tests passed; physical validation pending')
(out/'manifest.json').write_text(json.dumps(m,indent=2));p.with_name(p.stem+'-manifest.json').write_text(json.dumps(m,indent=2))
print(name,sha)
