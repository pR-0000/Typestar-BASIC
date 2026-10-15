"""Place an INTERNAL scene engine in real IC8 space; no public parser/release.

SCAPPEND requires validated records. The strict offline SCADD remains in its
original source/test. Future BASIC callers must validate before SCAPPEND.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re
from validate_array_tokens import ROOT,assemble

base=ROOT/'build/keyboard-delta';out=ROOT/'build/paper-scene-linked';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();cpu=bytearray(original)
assert hashlib.sha256(original).hexdigest()=='dc24fdbe4c96c932d890733c0e68ae92998078890a0d4542b03db4ceea8c1de5'
# Ten nodes have no differences. Point their aliases at the parent rather
# than storing a three-byte link. The decoder and all characters are unchanged.
keyboard=(ROOT/'build/array-heap/keyboard-delta.asm').read_text()
keyboard,n=re.subn(r'KDN(\d+) FCB 254\n        FDB KDN(\d+)\n',r'KDN\1 EQU KDN\2\n',keyboard)
assert n==10,n
kcode,ks=assemble('scene-keyboard-aliases',keyboard)
start=s['KDENTRY'];limit=s['KICON']
assert len(kcode)==698
extra=dict(SCJOB=0x1cde,SCSTATE=0x1d70,PCSTATE=0x1d70,PCBASE=0x1d77,
           SBLIST=0x1d7c,SBLEFT=0x1d7e,ARRAY_NAMED_FIND=0x44ba,ANRESERVE=0x451a)
line=(ROOT/'src/paper-line.asm').read_text().replace('PLROW EQU PLSTATE+32\n','').replace('PLMASK EQU PLSTATE+33','PLMASK EQU PLSTATE+32').replace('PLTARGET EQU PLSTATE+35\n','').replace('PLENDX EQU PLSTATE+37','PLENDX EQU PLSTATE+34').replace('PLENDY EQU PLSTATE+38','PLENDY EQU PLSTATE+35')
line+=(ROOT/'src/paper-line-command.inc').read_text().replace('FCC "PLINE"','FCC "LINE"')
storage=(ROOT/'src/paper-scene-storage.asm').read_text()
a=storage.index('SCADD STX');b=storage.index('SCFIND JSR')
storage=storage[:a]+'''SCAPPEND STX SCSOURCE
; Internal ABI: kind/coordinates/width/fill/reserved already validated.
; Missing, corrupt, closed and full lists are still rejected by the code below.
'''+storage[b:]
scene=(ROOT/'src/paper-scene.asm').read_text().replace('LDX #PCOUT','LDX PCBASE')
body=line+storage+scene+(ROOT/'src/paper-scene-band.asm').read_text()
local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|extra).items() if k not in local)
origin=start+len(kcode)
code,l=assemble('paper-scene-linked','        OPT H01\n'+defs+f'        ORG ${origin:04X}\n'+body)
assert origin+len(code)<=limit,(len(code),limit-origin)
cpu[start-0x4000:limit-0x4000]=kcode+code+b'\xff'*(limit-origin-len(code))
# These are the only published ingress points of the relocated LINE module.
patches=[]
for entry,old,new in [(s['LCDDISPATCH'],s['LNDISPATCH'],l['LNDISPATCH'])]:
    i=entry-0x4000;assert cpu[i:i+3]==b'\x7e'+old.to_bytes(2,'big')
    cpu[i:i+3]=b'\x7e'+new.to_bytes(2,'big');patches.append((entry,3))
a=s['RBRENDERBAND'];i=a-0x4000
needle=b'\xbd'+s['LNSELECT'].to_bytes(2,'big');piece=cpu[i:i+25]
assert piece.count(needle)==1
j=i+piece.index(needle);cpu[j:j+3]=b'\xbd'+l['LNSELECT'].to_bytes(2,'big');patches.append((j+0x4000,3))
assert all(x==y or start<=i+0x4000<limit or any(a<=i+0x4000<a+n for a,n in patches)
           for i,(x,y) in enumerate(zip(original,cpu)))
engine=l['SBEND']-l['SCBEGIN'];gain=n*3+1
for module in m['statement_modules']:
    if module['name']=='keyboard-delta':module.update(bytes=len(kcode))
    if module['name']=='paper-line':module.update(origin=origin,bytes=l['LNEND']-origin)
m['statement_modules'].append(dict(name='internal-paper-scene',origin=l['SCBEGIN'],bytes=engine))
m['keyboard_delta'].update(bytes=len(kcode),recovered_bytes=356,
                          free_start=origin+len(code),free_end=limit,
                          free_note='Only final tail is free; relocated LINE and scene engine follow keyboard data')
m.update(status='INTERNAL CPU CANDIDATE ONLY: composition has no BASIC parser',
         sha256=hashlib.sha256(cpu).hexdigest(),scene_engine_bytes=engine,
         known_free_fragmented_bytes=m['known_free_fragmented_bytes']+gain-engine,
         scene_free_tail=dict(start=origin+len(code),end=limit,bytes=limit-origin-len(code)),
         scene_ram=extra,scene_validation_required='SCAPPEND only accepts prevalidated 8-byte records',
         keyboard_alias_bytes_saved=n*3,external_line_patches=patches)
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|ks|extra|l,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print(json.dumps({k:m[k] for k in ('scene_engine_bytes','known_free_fragmented_bytes','scene_free_tail')},indent=2))
