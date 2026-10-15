""".85 square glyphs: fit the existing submitter slot; no font relocation."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/paper-origin-y';out=ROOT/'build/square-glyph';out.mkdir(exist_ok=True)
old=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
assert hashlib.sha256(old).hexdigest()=='b737bae8f0f2b20921758b1e2237c8fef86135d0f0145893fec86de2cd2d5a69'
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text());cpu=bytearray(old);patches=[]
a=s['SGSUBMIT'];end=s['SGSELECT']
body=(ROOT/'src/paper-square-submit.asm').read_text()
local={'SGSUBMIT','SQWIDTH','SQHEIGHT','SGDONE','SQEND','SGTILES'}
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items() if k not in local)
code,ls=assemble('square-submit',' OPT H01\n'+defs+f' ORG ${a:04X}\n'+body)
assert len(code)<=end-a,(len(code),end-a)
def patch(at,expected,new):
 assert len(expected)==len(new) and old[at-0x4000:at-0x4000+len(expected)]==expected,hex(at)
 cpu[at-0x4000:at-0x4000+len(new)]=new;patches.append(dict(address=at,old=expected.hex(),new=new.hex()))
patch(a,old[a-0x4000:end-0x4000],code+b'\x01'*(end-a-len(code)))
needle=bytes.fromhex('c10226');p=old.index(needle,s['SGRY']-0x4000,s['SGRX']-0x4000)+0x4000
patch(p,needle,bytes.fromhex('c10127'))
p=old.index(bytes.fromhex('c10222'),s['SGNOZOOM']-20-0x4000,s['SGNOZOOM']-0x4000)+0x4000
patch(p,bytes.fromhex('c10222'),bytes.fromhex('c10322'))
p=old.index(b'Typestar BASIC 0.4.84-dev')+0x4000;patch(p,b'Typestar BASIC 0.4.84-dev',b'Typestar BASIC 0.4.85-dev')
allowed=[[r['address'],r['address']+len(bytes.fromhex(r['new']))] for r in patches]
assert all(x==y or any(a<=i+0x4000<b for a,b in allowed) for i,(x,y) in enumerate(zip(old,cpu)))
s.update({k:ls[k] for k in local});m.update(version='0.4.85-dev',sha256=hashlib.sha256(cpu).hexdigest(),square_patches=patches,status='Awaiting offline tests')
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu);(out/'symbols.json').write_text(json.dumps(s,indent=2));(out/'manifest.json').write_text(json.dumps(m,indent=2))
(ROOT/'studio/internal/profiles/basic-0.4.85-symbols.json').write_text(json.dumps(s,indent=2))
print('Submitter',len(code),'/',end-a,'SHA',m['sha256'])
