"""Place the synchronous bridge in audited ROM gaps. RAM still test-only."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import json,hashlib,re,os
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/paper-reclaimed';out=ROOT/'build/paper-rom-bridge';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());cpu=bytearray((base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes())
real=bool(os.environ.get('PAPER_RAM_LAYOUT'))
source=(ROOT/'src/paper-band-call.asm').read_text()
header=source[:source.index('RBAND LDAA')]
entry=source[source.index('RBJOB TSTA'):source.index('RBSAVE STS')]
entry=entry.replace('RBJOB TSTA\n        BEQ RBREJECT\n        CMPA #16\n        BHI RBREJECT','RBJOB DECA\n        CMPA #15\n        BHI RBREJECT\n        INCA').replace('BRA RBSAVE','JMP RBSAVE')
save=source[source.index('RBSAVE STS'):source.index('        INC GPRAN')]+'        JMP RBINIT\n'
init='RBINIT'+source[source.index('        INC GPRAN')+7:source.index('RBNEXT LDAA')]+'        JMP RBNEXT\n'
nextpart=source[source.index('RBNEXT LDAA'):source.index('RBRENDERED CLR')].replace('BCC RBRENDERED','BCS RBRENDERFAIL\n        JMP RBRENDERED\nRBRENDERFAIL EQU *')
render=source[source.index('RBRENDERED CLR'):source.index('RBPRINT JSR')]+'        JMP RBPRINT\n'
printing=source[source.index('RBPRINT JSR'):source.index('RBROW JSR')].replace('BEQ RBROW','BNE RBMORE\n        JMP RBROW\nRBMORE EQU *')
row=source[source.index('RBROW JSR'):source.index('; Test linker')].replace('BNE RBNEXT\n        BRA RBCLEAN','BEQ RBFINISHED\n        JMP RBNEXT\nRBFINISHED JMP RBCLEAN')
abort=source[source.index('RBABORT LDAA'):source.index('RBCLEAN JSR')]+'        JMP RBCLEAN\n'
clean=source[source.index('RBCLEAN JSR'):source.index('RBEND EQU')]
parts=[(0x4EA2,0x4EB9,'render',render),(0x4EE8,0x4F1D,'clean',clean),(0x4F20,0x4F3E,'print',printing),(0x542C,0x544F,'save',save),(0x56D4,0x56F1,'row',row),(0x63E4,0x63F3,'abort',abort),(0x8EC7,0x8EE6,'init',init),(0x8F43,0x8F5E,'next',nextpart),(0xBEDD,0xBF2F,'entry',entry)]
if real:
 # Mark BASIC ownership only after reservation/snapshot; leave serial ownership 1.
 parts=[(a,b,n,body.replace('INC GPRAN','JSR RBMARK') if n=='init' else body) for a,b,n,body in parts]
 parts=[(a,b,n,body.replace('        LDAA RBRESULT','        LDAA #1\n        STAA GPRAN\n        LDAA RBRESULT')+'RBMARK LDAA #2\n        STAA GPRAN\n        RTS\n' if n=='clean' else body) for a,b,n,body in parts]
 # A separate selector preserves CODE+P's existing editor/SCI cleanup path.
 parts.append((0x5728,0x5737,'route','RBERROUTE LDAA GPRAN\n        CMPA #2\n        BNE RBSERIALFAIL\n        JMP RBABORT\nRBSERIALFAIL JMP GXFAIL\n'))
 # Poll BREAK before each band; never interrupt a native tile in mid-phase.
 parts=[(a,b,n,body.replace('RBNEXT LDAA','RBRENDERBAND LDAA') if n=='next' else body) for a,b,n,body in parts]
 parts.append((0x5801,0x5813,'break','RBNEXT JSR RFASTBREAK\n        BNE RBNOBREAK\n        LDAA #8\n        STAA GPERROR\n        JMP RBABORT\nRBNOBREAK JMP RBRENDERBAND\n'))
 parts.append((0x5879,0x589E,'error','RBPAPERERROR CMPA #8\n        BNE RBHWERROR\n        JMP BREAK\nRBHWERROR LDX #RBPAPERMSG\n        JMP ERROR\nRBPAPERMSG FCC "?PAPER"\n        FCB 0\n'))
 parts.sort()
local=set(re.findall(r'^([A-Z][A-Z0-9]*)\b',header+''.join(x[3] for x in parts),re.M))|{'RBSTATE','RBRENDER'}
asm=f'        OPT H01\nRBSTATE EQU ${0x1CDE if real else 0x1100:04X}\nRBRENDER EQU $4118\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items() if k not in local)+header
for a,b,name,body in parts:asm+=f'        ORG ${a:04X}\n'+body+f'RBEND{name.upper()} EQU *\n'
code,l=assemble('paper-rom-bridge',asm);spans=[]
for a,b,name,_ in parts:
 end=l['RBEND'+name.upper()];assert end<=b,(name,hex(end),hex(b))
 assert cpu[a-0x4000:end-0x4000]==b'\xff'*(end-a),(name,'not empty')
 cpu[a-0x4000:end-0x4000]=code[a-parts[0][0]:end-parts[0][0]];spans.append(dict(name=name,start=a,end=end,bytes=end-a))
# The experimental parser used a RAM bridge address. Only change that JSR.
a=s['PXDISPATCH']-0x4000;b=s['PXEND']-0x4000;region=bytes(cpu[a:b]);assert region.count(bytes.fromhex('BD1202'))==1
cpu[a:b]=region.replace(bytes.fromhex('BD1202'),b'\xbd'+l['RBJOB'].to_bytes(2,'big'))
if real:
 at=s['GPABORT']-0x4000+3;assert cpu[at:at+3]==b'\x7e'+s['GXFAIL'].to_bytes(2,'big');cpu[at:at+3]=b'\x7e'+l['RBERROUTE'].to_bytes(2,'big')
 at=s['LCDDISPATCH']-0x4000;cpu[at:at+3]=b'\x7e'+s['PXDISPATCH'].to_bytes(2,'big')
if real:cpu=cpu.replace(b'Typestar BASIC 0.4.55-dev',b'Typestar BASIC 0.4.56-dev')
assert len(cpu)==32768
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu);(out/'symbols.json').write_text(json.dumps(s|l,indent=2))
m=json.loads((base/'manifest.json').read_text());m.update(sha256=hashlib.sha256(cpu).hexdigest(),bridge_spans=spans,bridge_bytes=sum(x['bytes'] for x in spans),paper_real_ram=real,version='0.4.56-dev' if real else m['version'],status='CPU candidate with shared working RAM; hardware validation pending' if real else 'All paper code in ROM; test RAM bindings; not for flash')
if real:m['paper_ram_map']=json.loads((ROOT/'tools/firmware/paper_ram_map.json').read_text())
m['statement_modules'] += [dict(name='paper-low-ROM',origin=0x4000,bytes=512),dict(name='paper-keyword',origin=0x4BC3,bytes=5)]+[dict(name='paper-'+r['name'],origin=r['start'],bytes=r['bytes']) for r in spans]
(out/'manifest.json').write_text(json.dumps(m,indent=2));print('PASS ROM placement',m['bridge_bytes'],'bytes in',len(spans),'segments')
