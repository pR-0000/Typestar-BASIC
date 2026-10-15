"""Place PLINE in ROM reclaimed by lossless keyboard block sharing."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/keyboard-packed';out=ROOT/'build/paper-line-linked';out.mkdir(exist_ok=True)
m=json.loads((base/'manifest.json').read_text());s=json.loads((base/'symbols.json').read_text())
cpu=bytearray((base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes())
origin=m['keyboard_packed']['free_start'];limit=m['keyboard_packed']['free_end']
# Compact scratch to 36 bytes in the transient LIST/SAVE buffer, stopping
# strictly before the native printer flag $1DA4. No LIST/SAVE during a job.
line=(ROOT/'src/paper-line.asm').read_text().replace('PLROW EQU PLSTATE+32\n','').replace('PLMASK EQU PLSTATE+33','PLMASK EQU PLSTATE+32').replace('PLTARGET EQU PLSTATE+35\n','').replace('PLENDX EQU PLSTATE+37','PLENDX EQU PLSTATE+34').replace('PLENDY EQU PLSTATE+38','PLENDY EQU PLSTATE+35')
body=line+(ROOT/'src/paper-line-command.inc').read_text()
local=set(re.findall(r'^([A-Z][A-Z0-9]*)\b',body,re.M))
extra=dict(PLSTATE=0x1D80,PLOUT=s['PBOUT'],LNMODE=0x1D7B,LNEXTRA=0x1D7C)
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|extra).items() if k not in local)
code,l=assemble('paper-line-linked','        OPT H01\n'+defs+f'        ORG ${origin:04X}\n'+body)
assert origin+len(code)<=limit,(len(code),limit-origin)
assert cpu[origin-0x4000:origin-0x4000+len(code)]==b'\xff'*len(code)
cpu[origin-0x4000:origin-0x4000+len(code)]=code
def replace_at(a,old,new):
 assert cpu[a-0x4000:a-0x4000+len(old)]==old,hex(a)
 cpu[a-0x4000:a-0x4000+len(old)]=new
replace_at(s['LCDDISPATCH'],b'\x7e'+s['PXDISPATCH'].to_bytes(2,'big'),b'\x7e'+l['LNDISPATCH'].to_bytes(2,'big'))
a=s['RBRENDERBAND'];piece=bytes(cpu[a-0x4000:a-0x4000+25]);needle=b'\xbd'+s['PRBAND'].to_bytes(2,'big');assert piece.count(needle)==1
replace_at(a+piece.index(needle),needle,b'\xbd'+l['LNSELECT'].to_bytes(2,'big'))
# PGSTART has exactly three spare bytes before the next live block.
pg=(ROOT/'src/paper-geometry.inc').read_text().replace('PGSTART LSR','PGSTART CLR LNMODE\n        LSR')
locals=set(re.findall(r'^([A-Z][A-Z0-9]*)\b',pg,re.M))
p,ps=assemble('paper-line-geometry','        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|extra).items() if k not in locals)+pg)
assert ps['PGSTARTEND']==0x4BE4
cpu[0xBC8:0xBE4]=p[:28]
m.update(sha256=hashlib.sha256(cpu).hexdigest(),status='PLINE linked; hardware validation pending',
         paper_line_bytes=len(code)+3,known_free_fragmented_bytes=m['known_free_fragmented_bytes']-len(code)-3,
         paper_code_bytes=m['paper_code_bytes']+len(code)+3)
m['statement_modules'].append(dict(name='paper-line',origin=origin,bytes=len(code)))
for module in m['statement_modules']:
 if module['name']=='paper-geometry-start':module['bytes']=28
m['paper_ram_map']['blocks'] += [dict(name='PLSTATE',start='1D80',bytes=36,alias='LIST/SAVE buffer, exclusive synchronous print; native 1DA4 untouched'),dict(name='LNMODE/EXTRA',start='1D7B',bytes=2,alias=None)]
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|extra|l|ps,indent=2));(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('PLINE bytes',len(code)+3,'remaining',m['known_free_fragmented_bytes'])
