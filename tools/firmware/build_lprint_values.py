"""Add numeric/mixed LPRINT without relocating the validated font/driver."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/lprint-cache';out=ROOT/'build/lprint-values';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();cpu=bytearray(original)
assert hashlib.sha256(original).hexdigest()=='7ed171de9caef6190ca22dfc63d9d23c419c8ace8ef4b6075b618eb26372f5ac'
body=(ROOT/'src/paper-lprint-values.asm').read_text()
local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items() if k not in local)
def link(origin):return assemble('lprint-values','        OPT H01\n'+defs+f'        ORG ${origin:04X}\n'+body)
code,_=link(0x1000)
free=[r[:] for r in m['explicit_free_regions']]
_,index=min((b-a,i) for i,(a,b) in enumerate(free) if b-a>=len(code))
origin=free[index][0];free[index][0]+=len(code)
code,l=link(origin)
assert cpu[origin-0x4000:origin-0x4000+len(code)]==b'\xff'*len(code)
cpu[origin-0x4000:origin-0x4000+len(code)]=code
patches=[]
def patch(a,old,new):
    i=a-0x4000;assert cpu[i:i+len(old)]==old,(hex(a),old.hex())
    assert len(old)==len(new);cpu[i:i+len(new)]=new
    patches.append(dict(address=a,old=old.hex(),new=new.hex()))
patch(s['LPPARSE'],b'\xbd'+s['SPACE'].to_bytes(2,'big'),b'\x7e'+l['LVPARSE'].to_bytes(2,'big'))
a=s['LPCOPY'];part=original[a-0x4000:s['LPFOUND']-0x4000]
old=b'\xbd'+s['LPLOOKUP'].to_bytes(2,'big');assert part.count(old)==1
patch(a+part.index(old),old,b'\xbd'+l['LVLOOKUP'].to_bytes(2,'big'))
a=s['LPLIMIT'];part=original[a-0x4000:s['LPGRAPHICLIMIT']-0x4000]
assert part.count(b'\xc1\x36')==1
patch(a+part.index(b'\xc1\x36'),b'\xc1\x36',b'\xc1\x48')
old=b'Typestar BASIC 0.4.69-dev';assert cpu.count(old)==1
patch(cpu.index(old)+0x4000,old,b'Typestar BASIC 0.4.70-dev')
assert all(x==y or origin<=i+0x4000<origin+len(code) or any(p['address']<=i+0x4000<p['address']+len(bytes.fromhex(p['new'])) for p in patches) for i,(x,y) in enumerate(zip(original,cpu)))
m.update(version='0.4.70-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='Mixed numeric LPRINT CPU candidate',
    known_free_fragmented_bytes=m['known_free_fragmented_bytes']-len(code),explicit_free_regions=[r for r in free if r[0]<r[1]],
    explicit_free_bytes=sum(b-a for a,b in free),lprint_values_bytes=len(code),lprint_values_patches=patches,
    lprint_output_buffer=[0x1900,0x1948])
m['statement_modules'].append(dict(name='lprint-values',origin=origin,bytes=len(code)))
m['lprint_cache']['max_keys']=64
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|l,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('numeric LPRINT',len(code),'bytes; free',m['known_free_fragmented_bytes'])
