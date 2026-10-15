"""Package .88 only after actual-ROM paper, font and SAVE regressions pass."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'build/paper-list'
data=(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
m=json.loads((out/'manifest.json').read_text())
assert len(data)==32768 and hashlib.sha256(data).hexdigest()==m['sha256']
for name in ['font-validation.json','llist-validation.json']:
    report=json.loads((out/name).read_text())
    assert report['result']=='PASS' and report['sha256']==m['sha256'],name
raw=data[16384:]+data[:16384]
path=ROOT/'release/s70-basic-0.4.88-dev-canon-start-nh7.bin'
assert not path.exists() or path.read_bytes()==raw
path.write_bytes(raw)
digest=hashlib.sha256(raw).hexdigest()
path.with_suffix('.sha256').write_text(digest+'  '+path.name+'\n')
m.update(nh7_sha256=digest,status='LLIST, font and SAVE CPU validation passed; physical validation pending')
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
path.with_name(path.stem+'-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print(path.name,digest)
