"""Package .77 only after matching-image motor, font and game validation."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'build/paper-reverse'
cpu=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
m=json.loads((base/'manifest.json').read_text());digest=hashlib.sha256(cpu).hexdigest()
assert len(cpu)==32768 and digest==m['sha256'] and m['version']=='0.4.77-dev'
names=['font-validation.json','motor-validation.json','candy-map-validation.json',
       'candy-events-validation.json','candy-war-validation.json']
gh=hashlib.sha256((ROOT/'examples/games/candy-war-fr.bas').read_text().encode()).hexdigest()
for name in names:
    r=json.loads((base/name).read_text())
    assert r.get('sha256',r.get('cpu_sha256'))==digest,name
    assert r['result']=='PASS',name
    if 'source_sha256' in r:assert r['source_sha256']==gh,name
raw=cpu[16384:]+cpu[:16384]
target=ROOT/'release/s70-basic-0.4.77-dev-canon-start-nh7.bin'
assert not target.exists() or target.read_bytes()==raw
report=dict(version=m['version'],cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),
    status='CPU validated; physical paper reversal/visibility confirmation pending',
    candidate_manifest=m,game_sha256=gh,
    validation_reports=[str((base/n).relative_to(ROOT)) for n in names],
    limits=['FEED is relative and signed; absolute paper position must remain 0..448',
            'Native glyph -32/+32 compensation retained outside PMMOVE',
            'Paper presentation belongs to the game, not to every LPRINT',
            'Mechanical backlash and visible height require hardware confirmation'],
    source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for d in ('src','tools') for p in sorted((ROOT/d).glob('*')) if p.is_file()})
target.write_bytes(raw)
target.with_name(target.stem+'-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(target.name,report['nh7_sha256'])
