"""Package the .68 image after matching-image font and shared-driver tests."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT

base=ROOT/'build/lprint-stream'
cpu=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
m=json.loads((base/'manifest.json').read_text());digest=hashlib.sha256(cpu).hexdigest()
assert len(cpu)==32768 and digest==m['sha256'] and m['version']=='0.4.68-dev'
names=['font-validation.json','draw-validation.json','motor-validation.json',
       'native-rom-audit.json','statements-validation.json','graphics-packed-validation.json',
       'retention-validation.json','decimal-for-validation.json','serial-validation.json']
for name in names:
    report=json.loads((base/name).read_text())
    assert report['sha256']==digest,name
    if 'result' in report:assert report['result']=='PASS',name
audit=json.loads((base/'native-rom-audit.json').read_text())
for group in ['decimal_add','decimal_subtract','decimal_multiply','decimal_divide',
              'keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder']:
    assert not audit['groups'][group]['first_code_collisions'],group
raw=cpu[16384:]+cpu[:16384]
target=ROOT/'release/s70-basic-0.4.68-dev-canon-start-nh7.bin'
assert not target.exists() or target.read_bytes()==raw
report=dict(version=m['version'],cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),
            status='CPU validated; LPRINT physical validation pending; .66 hardware validated',
            candidate_manifest=m,validation_reports=[str((base/n).relative_to(ROOT)) for n in names],
            limits=['LPRINT accepts one ASCII 32..126 quoted literal, 72 columns; trailing semicolon continues; bare LPRINT ends line',
                    'Bare LPRINT or an empty literal advances one line; trailing semicolon suppresses it',
                    'No numeric/string expressions or comma separators yet',
                    'Native timing, heating and physical appearance still require hardware validation'],
            source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                           for d in ('src','tools') for p in sorted((ROOT/d).glob('*')) if p.is_file()})
target.write_bytes(raw)
target.with_name(target.stem+'-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(target.name,report['nh7_sha256'])
