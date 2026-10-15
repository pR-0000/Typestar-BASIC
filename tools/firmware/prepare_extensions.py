"""Export .74 NH7 only with matching-image regression and native-driver reports."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT
base=ROOT/'build/extensions';cpu=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
m=json.loads((base/'manifest.json').read_text());digest=hashlib.sha256(cpu).hexdigest()
assert len(cpu)==32768 and digest==m['sha256'] and m['version']=='0.4.74-dev'
names=['extra-math-validation.json','glyph-validation.json','strings-validation.json','strings-paper-validation.json','strings-io-validation.json',
       'data-validation.json','data-math-validation.json','data-paper-validation.json',
       'font-validation.json','draw-validation.json','motor-validation.json','native-rom-audit.json',
       'statements-validation.json','graphics-packed-validation.json','retention-validation.json',
       'decimal-for-validation.json','decimal-if-validation.json','inline-then-validation.json',
       'serial-validation.json','lcd-validation.json','framing-validation.json']
for name in names:
    r=json.loads((base/name).read_text());assert r['sha256']==digest,name
    if 'result' in r:assert r['result']=='PASS',name
audit=json.loads((base/'native-rom-audit.json').read_text())
for group in ['decimal_add','decimal_subtract','decimal_multiply','decimal_divide',
              'keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder']:
    assert not audit['groups'][group]['first_code_collisions'],group
reclaim=json.loads((base/'reclaim-audit.json').read_text())
assert reclaim['result']=='PASS' and reclaim['bytes']==1613
assert reclaim['base_sha256']==hashlib.sha256((ROOT/'build/strings/EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()).hexdigest()
raw=cpu[16384:]+cpu[:16384];target=ROOT/'release/s70-basic-0.4.74-dev-canon-start-nh7.bin'
assert not target.exists() or target.read_bytes()==raw
report=dict(version=m['version'],cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),
    status='CPU validated; .74 hardware validation pending; .73 hardware confirmed',
    candidate_manifest=m,validation_reports=[str((base/n).relative_to(ROOT)) for n in names],
    reclaim_audit=reclaim,
    limits=['TAN/ATN/LOG/EXP approximate; radians; EXP maximum argument 18',
            'Power: right associative; negative bases require integer exponent -32768..65535',
            'GLYPH: width 1..16 for row-word lists, 1..31 for pixel matrices; height 1..16; zoom 1 or 2',
            'GLYPH prints immediately and rejects open deferred scenes; no LPRINT font registration',
            'Physical pixel aspect differs from corrected geometry coordinates; paper test required',
            'RAM cartridges deferred; program retention and serial wire format unchanged'],
    source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for d in ('src','tools') for p in sorted((ROOT/d).glob('*')) if p.is_file()})
target.write_bytes(raw);target.with_name(target.stem+'-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(target.name,report['nh7_sha256'])
