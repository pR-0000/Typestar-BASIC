"""Add bounded CIRCLE to the hardware-validated .61 image."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/paper-draw';out=ROOT/'build/paper-circle';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();cpu=bytearray(original)
assert hashlib.sha256(original).hexdigest()=='44be671df836547c1e8b4cafef932db0b743e8278039b4be269a97e634a5da17'

body=(ROOT/'src/paper-circle.asm').read_text()
local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items() if k not in local)
origin=0x7a00+m['draw_motor_bytes']
code,l=assemble('paper-circle-release','        OPT H01\n'+defs+f'        ORG ${origin:04X}\n'+body)
assert origin+len(code)<=0x8200
assert cpu[origin-0x4000:origin-0x4000+len(code)]==b'\xff'*len(code)
cpu[origin-0x4000:origin-0x4000+len(code)]=code
patches=[]
def patch(a,old,new):
    i=a-0x4000;assert bytes(cpu[i:i+len(old)])==old,(hex(a),old.hex())
    assert len(old)==len(new);cpu[i:i+len(new)]=new
    patches.append(dict(address=a,old=old.hex(),new=new.hex()))
patch(s['LCDDISPATCH'],b'\x7e'+s['MCDISPATCH'].to_bytes(2,'big'),b'\x7e'+l['CCDISPATCH'].to_bytes(2,'big'))
patch(s['PCNEXT'],b'\xfe'+s['PCPTR'].to_bytes(2,'big'),b'\x7e'+l['CCSELECT'].to_bytes(2,'big'))
patch(s['SHEXTENT'],bytes.fromhex('5F6D00'),b'\x7e'+l['CCEXTENT'].to_bytes(2,'big'))
old=b'Typestar BASIC 0.4.61-dev';new=b'Typestar BASIC 0.4.62-dev'
assert cpu.count(old)==1;patch(cpu.index(old)+0x4000,old,new)
assert all(x==y or origin<=i+0x4000<origin+len(code) or any(p['address']<=i+0x4000<p['address']+len(bytes.fromhex(p['new'])) for p in patches) for i,(x,y) in enumerate(zip(original,cpu)))
m.update(version='0.4.62-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='CIRCLE CPU candidate',circle_bytes=len(code),known_free_fragmented_bytes=m['known_free_fragmented_bytes']-len(code),paper_code_bytes=m['paper_code_bytes']+len(code),circle_patches=patches)
m['statement_modules'].append(dict(name='paper-circle',origin=origin,bytes=len(code)))
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|l,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('CIRCLE bytes',len(code),'free',m['known_free_fragmented_bytes'])
