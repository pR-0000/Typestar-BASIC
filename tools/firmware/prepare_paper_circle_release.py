"""Package the .62 NH7 image only after matching-image regression reports."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT

base=ROOT/'build/paper-circle'
cpu=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
m=json.loads((base/'manifest.json').read_text());digest=hashlib.sha256(cpu).hexdigest()
assert len(cpu)==32768 and digest==m['sha256'] and m['version']=='0.4.62-dev'
names=['circle-validation.json','draw-validation.json','motor-validation.json','keyboard-validation.json',
       'native-rom-audit.json','retention-validation.json','decimal-for-validation.json',
       'statements-validation.json','serial-validation.json','graphics-packed-validation.json']
for name in names:
    report=json.loads((base/name).read_text())
    assert report['sha256']==digest,name
    if 'result' in report:assert report['result']=='PASS',name
audit=json.loads((base/'native-rom-audit.json').read_text())
for group in ['decimal_add','decimal_subtract','decimal_multiply','decimal_divide',
              'keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder']:
    assert not audit['groups'][group]['first_code_collisions'],group
raw=cpu[16384:]+cpu[:16384]
target=ROOT/'release/s70-basic-0.4.62-dev-canon-start-nh7.bin'
assert not target.exists() or target.read_bytes()==raw
report=dict(version=m['version'],cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),
            status='CPU validated; CIRCLE physical validation pending; DRAW and motors validated on .61',
            candidate_manifest=m,validation_reports=[str((base/name).relative_to(ROOT)) for name in names],
            limits=['Motor units are native units, not graphic coordinates or millimetres',
                    'ORIGIN declares current position; no automatic homing or page edge detection',
                    'Paper reverse rejected; head 0..128, paper 0..448 relative to declared origin',
                    'Printing invalidates manual origin; re-declare ORIGIN before manual motion',
                    'Each immediate drawing starts at current sheet position; common origin via DEFERRED'],
            source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                           for d in ('src','tools') for p in sorted((ROOT/d).glob('*')) if p.is_file()})
target.write_bytes(raw)
target.with_name(target.stem+'-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(target.name,report['nh7_sha256'])
