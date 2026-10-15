"""Build .57 from the hardware-tested .56, with uniform paper geometry."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import json,hashlib,re
from validate_array_tokens import ROOT,assemble
out=ROOT/'build/paper-geometry';out.mkdir(exist_ok=True)
raw=release_input('s70-basic-0.4.56-dev-canon-start-nh7.bin').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='f31d4d1ee2a274776e7dfccf3748cd99b0e699973bfde093cf24a06290208abc'
cpu=bytearray(raw[16384:]+raw[:16384]);s=json.loads((ROOT/'build/paper-rom-bridge/symbols.json').read_text())
raster=(ROOT/'src/paper-rectangle.asm').read_text().replace('BSR PBNEAR','JSR PGVNEAR',2)
for name in ('PBPY',):
 raster=raster.replace(f'LDD {name}\n        ADDD #1\n        STD {name}',f'LDX {name}\n        INX\n        STX {name}')
parser=(ROOT/'src/paper-box-command.asm').read_text().replace('PXNAME FCC "PBOX"\n        FCB 0\n','').replace('        BCS PXRANGE\n        RTS','        BCC PXOK\n        JMP RBPAPERERROR\nPXOK RTS').replace('JSR RBJOB','JSR PGSTART')
body='        ORG $4000\n'+raster+(ROOT/'src/paper-rectangle-band.asm').read_text()+parser
local=set(re.findall(r'^([A-Z][A-Z0-9]*)\b',body,re.M))
extra={'PGSTART':0x4BC8,'PGVNEAR':0x56E8,'PGYWIDTH':0x1D7A}
code,l=assemble('paper-geometry-low','        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|extra).items() if k not in local)+body)
assert len(code)==512 and l['PXEND']==0x4200
cpu[:512]=code
helper=(ROOT/'src/paper-geometry.inc').read_text();defs=set(re.findall(r'^([A-Z][A-Z0-9]*)\b',helper,re.M))
h,hlabels=assemble('paper-geometry-helper','        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|extra|l).items() if k not in defs)+helper)
for a,b in [(0x4BC8,hlabels['PGSTARTEND']),(0x56E8,hlabels['PGVEND'])]:
 assert b<=(0x4BE4 if a==0x4BC8 else 0x56F1)
 assert cpu[a-0x4000:b-0x4000]==b'\xff'*(b-a)
 cpu[a-0x4000:b-0x4000]=h[a-0x4BC8:b-0x4BC8]
# Recompiled adapter and dispatcher may move after recompilation; rewrite only their calls.
at=s['LCDDISPATCH']-0x4000;assert cpu[at:at+3]==b'\x7e'+s['PXDISPATCH'].to_bytes(2,'big');cpu[at:at+3]=b'\x7e'+l['PXDISPATCH'].to_bytes(2,'big')
a=s['RBRENDERBAND']-0x4000;b=a+25;region=bytes(cpu[a:b]);old=b'\xbd'+s['PRBAND'].to_bytes(2,'big');assert region.count(old)==1;cpu[a:b]=region.replace(old,b'\xbd'+l['PRBAND'].to_bytes(2,'big'))
cpu=cpu.replace(b'Typestar BASIC 0.4.56-dev',b'Typestar BASIC 0.4.57-dev');assert len(cpu)==32768
m=json.loads((ROOT/'build/paper-rom-bridge/manifest.json').read_text());m.update(version='0.4.57-dev',sha256=hashlib.sha256(cpu).hexdigest(),paper_geometry='uniform 2:1; endpoints floor(y/2), vertical thickness ceil(t/2)',paper_code_bytes=903,known_free_fragmented_bytes=63,status='Uniform paper geometry; hardware validation pending')
m['paper_ram_map']['blocks'].append(dict(name='PGYWIDTH',start='1D7A',bytes=1,alias=None,reason='vertical stroke in native rows, recomputed per PBOX'))
m['statement_modules'] += [dict(name='paper-geometry-start',origin=0x4BC8,bytes=hlabels['PGSTARTEND']-0x4BC8),dict(name='paper-geometry-near',origin=0x56E8,bytes=hlabels['PGVEND']-0x56E8)]
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu);(out/'symbols.json').write_text(json.dumps(s|extra|l|hlabels,indent=2));(out/'manifest.json').write_text(json.dumps(m,indent=2));print('Built .57;',len(code),'low bytes; helpers',hlabels['PGSTARTEND']-0x4BC8+hlabels['PGVEND']-0x56E8)
