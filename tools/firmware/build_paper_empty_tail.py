"""Build .87: trim blank BASIC bands using space reclaimed from rectangle code."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/input-retry';out=ROOT/'build/paper-empty-tail';out.mkdir(exist_ok=True)
old=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
assert hashlib.sha256(old).hexdigest()=='776a563501b8c5ad8e248c67ff113b3996be576e1d7545ee778f604ce6cd9e58'
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
raster=(ROOT/'src/paper-rectangle.asm').read_text().replace('BSR PBNEAR','JSR PGVNEAR',2)
raster=raster.replace('LDD PBPY\n        ADDD #1\n        STD PBPY','LDX PBPY\n        INX\n        STX PBPY')
def link(body,origin,name,extra=None):
    local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|(extra or {})).items() if k not in local)
    return assemble(name,' OPT H01\n'+defs+f' ORG ${origin:04X}\n'+body)
reference,_=link(raster,0x4000,'rectangle-reference')
assert old[:len(reference)]==reference
raster=raster[:raster.index('; Canon\'s experimentally')]
raster=raster.replace('        CLR PBCOL\n','').replace('PBCOLUMN LDD #0','PBCOLUMN CLRA\n        CLRB')
raster=raster.replace('        LDAA ,X\n        ORAA PBWORD\n        STAA PBWORD\n        LDAA 1,X\n        ORAA PBWORD+1\n        STAA PBWORD+1','        LDD ,X\n        ORAA PBWORD\n        ORAB PBWORD+1\n        STD PBWORD')
raster=raster.replace('        INC PBCOL\n        LDAA PBCOL\n        CMPA #31','        CPX #PBOUT+62')
raster+='PBEND EQU *\n'
assert old[s['PBMASKS']-0x4000:s['PBMASKS']-0x4000+32]==old[s['PLMASKS']-0x4000:s['PLMASKS']-0x4000+32]
code,labels=link(raster,0x4000,'rectangle-compact',dict(PBMASKS=s['PLMASKS']))
helper,h=link((ROOT/'src/paper-empty-tail.inc').read_text(),labels['PBEND'],'paper-empty-tail')
assert len(code)+len(helper)<=0x118,(len(code),len(helper))
cpu=bytearray(old);cpu[:0x118]=code+helper+b'\xff'*(0x118-len(code)-len(helper))
at=s['LPFORMAT']-0x4000
assert old[at:at+7]==b'\xb6'+s['LPMODE'].to_bytes(2,'big')+b'\xb7'+(s['GPDESC']+1).to_bytes(2,'big')+b'\x39'
cpu[at+3:at+7]=b'\x7e'+h['PETAIL'].to_bytes(2,'big')+b'\x01'
cpu=cpu.replace(b'Typestar BASIC 0.4.86-dev',b'Typestar BASIC 0.4.87-dev')
assert len(cpu)==32768
newfree=0x4118-h['PEEND']
m.update(version='0.4.87-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='CPU candidate; hardware pending',
    empty_tail_bytes=len(helper),rectangle_bytes=len(code),explicit_free_bytes=m['explicit_free_bytes']+newfree,
    known_free_fragmented_bytes=m['known_free_fragmented_bytes']+newfree)
if newfree:m['explicit_free_regions'].append([h['PEEND'],0x4118])
s.update(h);s.update(labels);s.update({k:h[k] for k in ('PETAIL','PENEXT','PEBYTE','PEDONE','PEEND')});s['PBMASKS']=s['PLMASKS']
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('rectangle/helper/free:',len(code),len(helper),newfree,m['sha256'])
