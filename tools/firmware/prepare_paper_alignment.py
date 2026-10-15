"""Package .79 only after matching-image trajectory, LCD and motor tests."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'build/paper-alignment'
cpu=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
m=json.loads((base/'manifest.json').read_text());digest=hashlib.sha256(cpu).hexdigest()
assert len(cpu)==32768 and digest==m['sha256'] and m['version']=='0.4.79-dev'
names=['alignment-validation.json','motor-validation.json']
for name in names:
    r=json.loads((base/name).read_text())
    assert r.get('sha256',r.get('cpu_sha256'))==digest and r['result']=='PASS',name
raw=cpu[16384:]+cpu[:16384]
target=ROOT/'release/s70-basic-0.4.79-dev-canon-start-nh7.bin'
assert not target.exists() or target.read_bytes()==raw
m['status']='CPU validated; physical reverse-approach alignment confirmation pending'
(base/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
r=dict(version=m['version'],cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),
       status=m['status'],candidate_manifest=m,
       validation_reports=[str((base/n).relative_to(ROOT)) for n in names],
       limits=['Mechanical backlash is not modeled; paper test required',
               'Negative paper movement passes 32 motor units beyond target then returns forward',
               'BASIC program format and tokens unchanged'],
       source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                     for d in ('src','tools') for p in sorted((ROOT/d).glob('*')) if p.is_file()})
target.write_bytes(raw)
target.with_name(target.stem+'-manifest.json').write_text(json.dumps(r,indent=2)+'\n')
target.with_suffix('.sha256').write_text(r['nh7_sha256']+'  '+target.name+'\n')
print(target.name,r['nh7_sha256'])
