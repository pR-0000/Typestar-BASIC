"""Link DRAW and manual motion into audited retired Canon editor space."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re
from validate_array_tokens import ROOT,assemble

base=ROOT/'build/paper-scene-linked';out=ROOT/'build/paper-draw';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();cpu=bytearray(original)
audit=json.loads((base/'editor-reclaim-audit.json').read_text())
assert audit['result']=='PASS' and audit['sha256']==hashlib.sha256(original).hexdigest()
draw=(ROOT/'src/paper-draw-command.asm').read_text()
# Re-arm only completed BASIC jobs. Serial and fault paths retain their guard.
draw=draw.replace('SHRETURN RTS','SHRETURN CLR GPRAN\n        RTS')
position=(ROOT/'src/paper-position.asm').read_text()
# Five persistent bytes in the verified LCD metadata gap. Remaining state is
# exclusive transient LIST/SAVE scratch; no statement executes during motion.
position=position.replace('PMVALID EQU PMSTATE','PMVALID EQU $1B5B').replace('PMX EQU PMSTATE+1','PMX EQU $1B5C').replace('PMY EQU PMSTATE+3','PMY EQU $1B5E')
position=position.replace('        TST GPRAN\n        BNE PMREJECT','        LDAA GPRAN\n        CMPA #2\n        BEQ PMREJECT')
short=(ROOT/'src/paper-short-feed.asm').read_text().replace('        OPT H01\n','').replace('        ORG $6230\n','')
body=draw+position+short+(ROOT/'src/paper-motor-command.asm').read_text()
local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|dict(PMSTATE=0x1da5)).items() if k not in local)
code,l=assemble('paper-draw-release','        OPT H01\n'+defs+'        ORG $7A00\n'+body)
assert len(code)<=2048,len(code)
cpu[0x3a00:0x4200]=code+b'\xff'*(2048-len(code))
patches=[]
def patch(a,old,new):
    i=a-0x4000;assert bytes(cpu[i:i+len(old)])==old,(hex(a),cpu[i:i+len(old)].hex(),old.hex())
    assert len(old)==len(new)
    cpu[i:i+len(new)]=new;patches.append(dict(address=a,old=old.hex(),new=new.hex()))
def jump(a,old,target):patch(a,b'\x7e'+old.to_bytes(2,'big'),b'\x7e'+target.to_bytes(2,'big'))
jump(s['LCDDISPATCH'],s['LNDISPATCH'],l['MCDISPATCH'])
# Keep old validator entry points, replace only the successful commit tails.
for label,needle,target in [('PXCHECK',b'\x4f\xf6'+s['PXSTATE'].to_bytes(2,'big'),l['SHBOX']),
                            ('LNCHECK',b'\xfc'+s['PXSTATE'].to_bytes(2,'big')+b'\xfd'+s['PLSTATE'].to_bytes(2,'big'),l['SHLINE'])]:
    a=s[label];part=cpu[a-0x4000:a-0x4000+100];assert part.count(needle)==1
    at=a+part.index(needle);patch(at,bytes(cpu[at-0x4000:at-0x4000+3]),b'\x7e'+target.to_bytes(2,'big'))
patch(s['LNSELECT'],bytes(cpu[s['LNSELECT']-0x4000:s['LNSELECT']-0x4000+3]),b'\x7e'+s['SBBAND'].to_bytes(2,'big'))
patch(s['GPINIT'],b'\x7f'+s['GPRAN'].to_bytes(2,'big'),b'\x7e'+l['MOTORBOOT'].to_bytes(2,'big'))
patch(s['GPPRINT'],bytes.fromhex('DE4E8C6EE9'),b'\x7e'+l['MOTORPRINT'].to_bytes(2,'big')+b'\x01\x01')
jump(s['GPABORT']+3,s['RBERROUTE'],l['MOTORABORT'])
patch(0x7158,bytes.fromhex('BD74B9'),b'\xbd'+l['PAPER_SHORT_PREPARE'].to_bytes(2,'big'))
old=b'Typestar BASIC 0.4.60-dev';new=b'Typestar BASIC 0.4.61-dev'
assert cpu.count(old)==1;i=cpu.index(old);patch(i+0x4000,old,new)
assert len(cpu)==32768
assert all(x==y or 0x7a00<=i+0x4000<0x8200 or any(p['address']<=i+0x4000<p['address']+len(bytes.fromhex(p['new'])) for p in patches) for i,(x,y) in enumerate(zip(original,cpu)))
m.update(version='0.4.61-dev',sha256=hashlib.sha256(cpu).hexdigest(),
         status='DRAW and motor commands integrated, CPU validation required before packaging',
         draw_motor_bytes=len(code),known_free_fragmented_bytes=m['known_free_fragmented_bytes']+2048-len(code),
         paper_code_bytes=m['paper_code_bytes']-1+m['scene_engine_bytes']+len(code),
         draw_patches=patches,motor_ram=dict(persistent_start=l['PMVALID'],persistent_bytes=5,
         transient_start=0x1da5,transient_bytes=21),native_editor_reclaimed=[0x7a00,0x8200],
         motor_limits=dict(head=[0,128],paper=[0,448],unit='two native phase steps',paper_reverse=False))
m['statement_modules'].append(dict(name='paper-draw-and-motors',origin=0x7a00,bytes=len(code)))
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|l,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('Built .61:',len(code),'bytes; free',m['known_free_fragmented_bytes'])
