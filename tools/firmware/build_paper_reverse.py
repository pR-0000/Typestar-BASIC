"""Build .77 from the hardware-validated .76, changing only audited hooks."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/ascii-paper';out=ROOT/'build/paper-reverse';out.mkdir(exist_ok=True)
old=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
assert hashlib.sha256(old).hexdigest()=='bf7c15744b40248226fbe87186d8aa8c84be277e0efc48801d8ba94fe66d581b'
cpu=bytearray(old);s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
free=m['explicit_free_regions'];allowed=[]
def patch(a,expected,value):
    assert cpu[a-0x4000:a-0x4000+len(expected)]==expected,hex(a)
    assert len(expected)==len(value)
    cpu[a-0x4000:a-0x4000+len(value)]=value;allowed.append([a,a+len(value)])
assert cpu[0x3158]==0xbd
s['PRSHORT']=int.from_bytes(cpu[0x3159:0x315b],'big')
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())
source=(ROOT/'src/paper-reverse.asm').read_text()
r,_=assemble('paper-reverse-size',' OPT H01\n'+defs+' ORG $1000\n'+source)
_,i=min((b-a,i) for i,(a,b) in enumerate(free) if b-a>=len(r));a,b=free[i]
r,labels=assemble('paper-reverse',' OPT H01\n'+defs+f' ORG ${a:04X}\n'+source)
patch(a,b'\xff'*len(r),r);free[i]=[a+len(r),b]
# The normal printer must retain its private -32/+32 compensation. Only
# the positioning transaction enters the signed preparer.
p=old.index(bytes.fromhex('ce7154bd')+s['GPCALL'].to_bytes(2,'big'),s['PMFEED']-0x4000)+0x4000
assert s['PMFEED']<=p and p+6<=s['PMCOMMIT']
patch(p,b'\xce\x71\x54',b'\xce'+labels['PRPREP'].to_bytes(2,'big'))
patch(0x724a,bytes.fromhex('8680b7'),b'\x7e'+labels['PRCOMPLETE'].to_bytes(2,'big'))
p=s['PMMOVE']+16
patch(p,b'\xbc'+s['PMY'].to_bytes(2,'big')+b'\x25\x53',b'\x01'*5)
p=s['MCFEED']
patch(p,b'\xbd'+s['MCUNSIGNED'].to_bytes(2,'big')+bytes.fromhex('8301c02229c301c0'),
      b'\xbd'+labels['PRFEED'].to_bytes(2,'big')+b'\x01'*8)
p=old.index(b'Typestar BASIC 0.4.76-dev')+0x4000
patch(p,b'Typestar BASIC 0.4.76-dev',b'Typestar BASIC 0.4.77-dev')
assert all(x==y or any(a<=j+0x4000<b for a,b in allowed) for j,(x,y) in enumerate(zip(old,cpu)))
alloc=dict(name='paper-reverse',origin=a,bytes=len(r))
m.update(version='0.4.77-dev',sha256=hashlib.sha256(cpu).hexdigest(),
 status='Signed paper travel; hardware validation pending',reverse_hooks=allowed,
 explicit_free_regions=free,explicit_free_bytes=sum(b-a for a,b in free),
 known_free_fragmented_bytes=m['known_free_fragmented_bytes']-len(r))
m['statement_modules'].append(alloc)
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|{k:labels[k] for k in ('PRPREP','PRFEED','PRREVEND')},indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
(out/'font-expected.json').write_bytes((base/'font-expected.json').read_bytes())
print('Added',len(r),'bytes; free',m['explicit_free_bytes'],m['sha256'])
