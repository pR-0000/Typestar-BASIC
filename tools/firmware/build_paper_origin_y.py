""".84: declare both origin coordinates, using only an audited free fragment."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/native-strings';out=ROOT/'build/paper-origin-y';out.mkdir(exist_ok=True)
old=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
assert hashlib.sha256(old).hexdigest()=='feedfc9d73e1e07ce06c8e6c39a1dda28d82e3e889023ebff0629e2c2b034b1e'
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
a=0x98ce;end=0x9900
assert [a,end] in m['explicit_free_regions'] and old[a-0x4000:end-0x4000]==b'\xff'*(end-a)
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())
code,labels=assemble('paper-origin-y',' OPT H01\n'+defs+f' ORG ${a:04X}\n'+(ROOT/'src/paper-origin-y.asm').read_text())
assert len(code)<=end-a,len(code)
cpu=bytearray(old);cpu[a-0x4000:a-0x4000+len(code)]=code;patches=[]
def patch(at,expected,data):
 assert len(expected)==len(data) and old[at-0x4000:at-0x4000+len(expected)]==expected,hex(at)
 cpu[at-0x4000:at-0x4000+len(data)]=data
 patches.append(dict(address=at,old=expected.hex(),new=data.hex()))
patch(s['OCVALIDATE'],b'\xbd'+s['EOS'].to_bytes(2,'big'),b'\x7e'+labels['OYENTRY'].to_bytes(2,'big'))
patch(s['OCLOAD']+3,b'\x7e'+s['OCSTORE'].to_bytes(2,'big'),b'\x7e'+labels['OYSTORE'].to_bytes(2,'big'))
v=old.index(b'Typestar BASIC 0.4.83-dev')+0x4000
patch(v,b'Typestar BASIC 0.4.83-dev',b'Typestar BASIC 0.4.84-dev')
allowed=[[a,a+len(code)]]+[[p['address'],p['address']+len(bytes.fromhex(p['new']))] for p in patches]
assert all(x==y or any(lo<=i+0x4000<hi for lo,hi in allowed) for i,(x,y) in enumerate(zip(old,cpu)))
free=[r for r in m['explicit_free_regions'] if r!=[a,end]]
if a+len(code)<end:free.append([a+len(code),end])
s.update({k:labels[k] for k in ('OYENTRY','OYSTORE','OYEND')})
m.update(version='0.4.84-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='Offline validation pending',
 explicit_free_regions=sorted(free),explicit_free_bytes=sum(y-x for x,y in free),
 known_free_fragmented_bytes=m['known_free_fragmented_bytes']-len(code),origin_y_patches=patches)
m['statement_modules'].append(dict(name='origin-y',origin=a,bytes=len(code)))
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s,indent=2));(out/'manifest.json').write_text(json.dumps(m,indent=2))
(ROOT/'studio/internal/profiles/basic-0.4.84-symbols.json').write_text(json.dumps(s,indent=2))
print('ORIGIN Y:',len(code),'bytes, free:',m['explicit_free_bytes'],'SHA',m['sha256'])
