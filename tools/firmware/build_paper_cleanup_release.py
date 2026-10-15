"""Remove audited unreachable printing paths; preserve every live address."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT
base=ROOT/'build/paper-point';out=ROOT/'build/paper-cleanup';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
cpu=bytearray((base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes());original=bytes(cpu)
audit=json.loads((base/'paper-dead-audit.json').read_text())
assert audit['result']=='PASS' and audit['sha256']==hashlib.sha256(cpu).hexdigest()
assert m['version']=='0.4.63-dev'
for a,b in audit['regions']:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
old=b'Typestar BASIC 0.4.63-dev';new=b'Typestar BASIC 0.4.64-dev'
assert cpu.count(old)==1;banner=cpu.index(old);cpu[banner:banner+len(old)]=new
assert all(x==y or banner<=i<banner+len(old) or any(a<=i+0x4000<b for a,b in audit['regions']) for i,(x,y) in enumerate(zip(original,cpu)))
m.update(version='0.4.64-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='Dead paper paths removed; regression required',reclaimed_paper_regions=audit['regions'],reclaimed_paper_bytes=audit['bytes'],known_free_fragmented_bytes=m['known_free_fragmented_bytes']+audit['bytes'],paper_code_bytes=m['paper_code_bytes']-audit['bytes'])
# Historical module spans are retained for provenance, not an allocation map.
m['allocation_note']='Use reclaimed_paper_regions as free holes inside historical statement_modules spans.'
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('Recovered',audit['bytes'],'free',m['known_free_fragmented_bytes'])
