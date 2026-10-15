"""Package .76 only after matching-image font, motor and Candy War checks."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'build/ascii-paper'
cpu=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
m=json.loads((base/'manifest.json').read_text());digest=hashlib.sha256(cpu).hexdigest()
assert len(cpu)==32768 and digest==m['sha256'] and m['version']=='0.4.76-dev'
names=['ascii-controls-validation.json','font-validation.json','motor-validation.json',
       'native-rom-audit.json','candy-map-validation.json','candy-events-validation.json','candy-war-validation.json']
for name in names:
    r=json.loads((base/name).read_text())
    assert r.get('sha256',r.get('cpu_sha256'))==digest,name
    assert r.get('result','PASS')=='PASS',name
game=ROOT/'examples/games/candy-war-fr.bas'
gh=hashlib.sha256(game.read_text().encode()).hexdigest()
for name in ('candy-events-validation.json','candy-war-validation.json'):
    assert json.loads((base/name).read_text())['source_sha256']==gh,name
audit=json.loads((base/'native-rom-audit.json').read_text())
for group in ('decimal_add','decimal_subtract','decimal_multiply','decimal_divide',
              'keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder'):
    assert not audit['groups'][group]['first_code_collisions'],group
raw=cpu[16384:]+cpu[:16384]
target=ROOT/'release/s70-basic-0.4.76-dev-canon-start-nh7.bin'
assert not target.exists() or target.read_bytes()==raw
report=dict(version=m['version'],cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),
    status='CPU validated; hardware confirmation pending',candidate_manifest=m,
    validation_reports=[str((base/n).relative_to(ROOT)) for n in names],
    game_sha256=gh,limits=['Physical punctuation and map registration need a paper test',
    'ORIGIN x declares a known coordinate, not a homing operation',
    'CLEAR discards variables/arrays/FOR frames, not source or GOSUB continuations',
    'Fixed 93-byte glyph decode uses implicit zero suffix; ROM integrity relies on verified image hashes'],
    source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for d in ('src','tools') for p in sorted((ROOT/d).glob('*')) if p.is_file()})
target.write_bytes(raw)
target.with_name(target.stem+'-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(target.name,report['nh7_sha256'])
