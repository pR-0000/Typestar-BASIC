"""Package .60 only after keyboard and paper checks on this exact image."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT

base=ROOT/'build/keyboard-delta'
cpu=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
m=json.loads((base/'manifest.json').read_text())
digest=hashlib.sha256(cpu).hexdigest()
assert len(cpu)==32768 and digest==m['sha256'] and m['version']=='0.4.60-dev'
reports=[]
for name in ('keyboard-validation.json','line-validation.json'):
    path=base/name;report=json.loads(path.read_text())
    assert report['sha256']==digest and report['result']=='PASS',name
    reports.append(str(path.relative_to(ROOT)))
oldraw=release_input('s70-basic-0.4.59-dev-canon-start-nh7.bin').read_bytes()
assert hashlib.sha256(oldraw).hexdigest()=='aedcb86390fec11353153be19c9c91a1c4437ddc8588411eced617b74ce6695e'
old=oldraw[16384:]+oldraw[:16384]
s=json.loads((base/'symbols.json').read_text())
start=s['KPACK'];end=m['keyboard_delta']['free_end']
banner=old.index(b'Typestar BASIC 0.4.59-dev')
assert all(a==b or start<=i+0x4000<end or banner<=i<banner+23
           for i,(a,b) in enumerate(zip(old,cpu)))
raw=cpu[16384:]+cpu[:16384]
target=ROOT/'release/s70-basic-0.4.60-dev-canon-start-nh7.bin'
assert not target.exists() or target.read_bytes()==raw
target.write_bytes(raw)
report=dict(version=m['version'],cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),
            candidate_manifest=m,validation_reports=reports,
            unchanged_outside_keyboard_and_banner=True,
            hardware_status='Pending keyboard check; paper bytes identical to .59',
            limits=['One BOX, LINE or CODE+P print job per boot',
                    'Composition and motor commands remain offline prototypes'])
target.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
print(target.name,report['nh7_sha256'])
