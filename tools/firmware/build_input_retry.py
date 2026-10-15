"""Build .86 INPUT retries in the existing 18-byte numeric reply slot."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble

base=ROOT/'build/square-glyph';out=ROOT/'build/input-retry'
out.mkdir(exist_ok=True)
old=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
assert hashlib.sha256(old).hexdigest()=='294c03f31beca5ed7691c6c7014d5e7a66b652d58df7a34f004f080d32f8d9f7'
s=json.loads((base/'symbols.json').read_text())
m=json.loads((base/'manifest.json').read_text())
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())
code,ls=assemble('input-retry',' OPT H01\n'+defs+(ROOT/'src/input-retry.inc').read_text())
assert len(code)==18 and ls['INPUTREPLYEND']==0xA760
cpu=bytearray(old);patches=[]
def patch(at,expected,replacement):
    assert len(expected)==len(replacement)
    assert old[at-0x4000:at-0x4000+len(expected)]==expected
    cpu[at-0x4000:at-0x4000+len(expected)]=replacement
    patches.append(dict(address=at,old=expected.hex(),new=replacement.hex()))
patch(0xA74E,bytes.fromhex('ce1900ff1980bda000ff19804d2620bd5335'),code)
banner=b'Typestar BASIC 0.4.85-dev'
patch(old.index(banner)+0x4000,banner,b'Typestar BASIC 0.4.86-dev')
assert all(a==b or any(p['address']<=i+0x4000<p['address']+len(bytes.fromhex(p['new'])) for p in patches)
           for i,(a,b) in enumerate(zip(old,cpu)))
s.update(INPUTREPLY=ls['INPUTREPLY'],INPUTREPLYEND=ls['INPUTREPLYEND'])
m.update(version='0.4.86-dev',sha256=hashlib.sha256(cpu).hexdigest(),
         input_retry_patches=patches,status='Awaiting INPUT CPU validation')
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
(ROOT/'studio/internal/profiles/basic-0.4.86-symbols.json').write_text(json.dumps(s,indent=2))
print(m['sha256'])
