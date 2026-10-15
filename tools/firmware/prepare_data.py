"""Package .72 only after matching-image BASIC, font and native-driver checks."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT
base=ROOT/'build/data';cpu=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
m=json.loads((base/'manifest.json').read_text());digest=hashlib.sha256(cpu).hexdigest()
assert len(cpu)==32768 and digest==m['sha256'] and m['version']=='0.4.72-dev'
names=['data-validation.json','data-math-validation.json','data-paper-validation.json',
       'font-validation.json','draw-validation.json','motor-validation.json','native-rom-audit.json',
       'statements-validation.json','graphics-packed-validation.json','retention-validation.json',
       'decimal-for-validation.json','serial-validation.json','lcd-validation.json','framing-validation.json']
for name in names:
    r=json.loads((base/name).read_text());assert r['sha256']==digest,name
    if 'result' in r:assert r['result']=='PASS',name
audit=json.loads((base/'native-rom-audit.json').read_text())
for group in ['decimal_add','decimal_subtract','decimal_multiply','decimal_divide',
              'keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder']:
    assert not audit['groups'][group]['first_code_collisions'],group
raw=cpu[16384:]+cpu[:16384];target=ROOT/'release/s70-basic-0.4.72-dev-canon-start-nh7.bin'
assert not target.exists() or target.read_bytes()==raw
report=dict(version=m['version'],cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),
    status='CPU validated; .72 hardware validation pending; .71 hardware confirmed',
    candidate_manifest=m,validation_reports=[str((base/n).relative_to(ROOT)) for n in names],
    limits=['DATA: numeric literals only; READ: numeric scalars and 1D/2D array cells',
            'RESTORE without line number; DATA/READ/RESTORE stored as ASCII in existing token format',
            'Read cursor resets at boot, NEW, RUN, accepted edit and LOAD; earlier successful READ stores remain after a later error',
            'No change to trigonometric routines or physical printing timing; hardware validation required'],
    source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for d in ('src','tools') for p in sorted((ROOT/d).glob('*')) if p.is_file()})
target.write_bytes(raw);target.with_name(target.stem+'-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(target.name,report['nh7_sha256'])
