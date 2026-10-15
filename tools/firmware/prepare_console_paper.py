"""Package the .78 candidate only after matching-image CPU checks; never flash."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'build/console-paper'
cpu=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
m=json.loads((base/'manifest.json').read_text());digest=hashlib.sha256(cpu).hexdigest()
assert len(cpu)==32768 and digest==m['sha256'] and m['version']=='0.4.78-dev'
names=['console-paper-validation.json','chords-validation.json','font-validation.json',
       'motor-validation.json','keyboard-validation.json','serial-validation.json','framing-validation.json']
for name in names:
    r=json.loads((base/name).read_text())
    assert r.get('sha256',r.get('cpu_sha256'))==digest,name
    if name=='serial-validation.json':
        assert r['roundtrip_lines']>=4 and r['empty_load'] and r['partial_failure_invalidates']
    elif name=='framing-validation.json':
        assert r.get('result')=='PASS',r
    else:assert r['result']=='PASS',name
raw=cpu[16384:]+cpu[:16384]
target=ROOT/'release/s70-basic-0.4.78-dev-canon-start-nh7.bin'
assert not target.exists() or target.read_bytes()==raw
m['status']='CPU validated; physical confirmation pending'
(base/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
report=dict(version=m['version'],cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),
            status=m['status'],candidate_manifest=m,
            validation_reports=[str((base/n).relative_to(ROOT)) for n in names],
            limits=['No hardware timing or mechanical accuracy claim from CPU tests',
                    'LLOCATE reference is current position, not sensed paper edge',
                    'Seven shared LCD custom slots; eighth reserved for cursor',
                    'PSET renamed POINT without alias; token record format unchanged'],
            source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for d in ('src','tools') for p in sorted((ROOT/d).glob('*')) if p.is_file()})
target.write_bytes(raw)
target.with_name(target.stem+'-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
target.with_suffix('.sha256').write_text(report['nh7_sha256']+'  '+target.name+'\n')
print(target.name,report['nh7_sha256'])
