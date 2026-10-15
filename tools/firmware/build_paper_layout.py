"""Offline ROM placement experiment: replaces old Canon descriptor table.
RAM bindings remain test-only. No NH7 output and no hardware release.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import json,hashlib,os
from validate_array_tokens import ROOT,assemble
out=ROOT/'build/paper-layout';out.mkdir(exist_ok=True)
base=ROOT/'build/randomize';image=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
assert hashlib.sha256(image).hexdigest()=='86a40efdedbde9b92c964dce34e84d879790043272d21bdad2db9c12f36be0ea'
s=json.loads((base/'symbols.json').read_text())
real=bool(os.environ.get('PAPER_RAM_LAYOUT'))
pb,po,pr,px=(0x1CE8,0x1BC0,0x1D77,0x1D70) if real else (0x1120,0x1180,0x1140,0x1150)
code,labels=assemble('paper-rom-layout',f'        OPT H01\nPBSTATE EQU ${pb:04X}\nPBOUT EQU ${po:04X}\nPRSTATE EQU ${pr:04X}\n        ORG $4000\n'+(ROOT/'src/paper-rectangle.asm').read_text()+(ROOT/'src/paper-rectangle-band.asm').read_text())
assert len(code)==342 and labels['PREND']<=0x4200
# PBOX's keyword uses five already-reclaimed parser bytes. The executable
# parser then fits directly after the rasterizer, without splitting branches.
name=s['NFAPPLYEND'];assert name==0x4BC3
body=(ROOT/'src/paper-box-command.asm').read_text().replace('PXNAME FCC "PBOX"\n        FCB 0\n','')
if real:body=body.replace('        BCS PXRANGE\n        RTS','        BCC PXOK\n        JMP RBPAPERERROR\nPXOK RTS')
parser,ps=assemble('paper-rom-parser','        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|labels).items())+f'PXSTATE EQU ${px:04X}\nPXNAME EQU ${name:04X}\nRBPAPERERROR EQU $5879\nRBJOB EQU $1202\n        ORG ${labels["PREND"]:04X}\n'+body)
assert len(parser)==(170 if real else 167) and ps['PXEND']<=0x4200
cpu=bytearray(image);used=len(code)+len(parser)
cpu[:512]=code+parser+bytes([255])*(512-used)
assert cpu[name-0x4000:name-0x4000+5]==b'\xff'*5
cpu[name-0x4000:name-0x4000+5]=b'PBOX\0'
assert len(cpu)==32768
assert all(a==b or i<512 or name-0x4000<=i<name-0x4000+5 for i,(a,b) in enumerate(zip(image,cpu)))
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|labels|ps,indent=2))
(out/'manifest.json').write_text(json.dumps(dict(status='OFFLINE; test RAM bindings; old Canon font descriptors removed',sha256=hashlib.sha256(cpu).hexdigest(),base_sha256=hashlib.sha256(image).hexdigest(),range=[16384,16896],code_bytes=used+5,parser_bytes=len(parser)+5,free_bytes=512-used,free_start=ps['PXEND'],keyword_range=[name,name+5],ram_bindings='1120/1140/1150/1180 and RBJOB=1202 are CPU-test-only',limits=['Not an NH7 release','Native text font descriptor path unavailable','No inference about all indirect/native calls']),indent=2))
print('Paper ROM experiment:',used+5,'bytes;',512-used,'bytes remaining in main block')
