"""Reclaim the retired literal parser/table, then link shared SIN/COS."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/lprint-values';out=ROOT/'build/trig';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();cpu=bytearray(original)
assert hashlib.sha256(original).hexdigest()=='7217250a24d3508d8ab2cc76667a4eccf8700c27cd29799ccb66e5224b777adf'
assert original[s['LPPARSE']-0x4000:s['LPPARSE']-0x4000+3]==b'\x7e'+s['LVPARSE'].to_bytes(2,'big')
table=original[s['NFTABLE']-0x4000:s['NFTABLE']-0x4000+60]
assert table==b'\x03ABS  \x03SGN  \x03INT  \x04PEEK \x03RND  \x03SQR  \x03FRE  \x05SERIN\x05INKEY\x03FIX  '
retired=[[s['LPPARSE']+3,s['LPCHECKWIDTH']],[s['NFTABLE'],s['NFTABLE']+60]]
free=[r[:] for r in m['explicit_free_regions']]+[r[:] for r in retired]
for a,b in retired:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
alloc=[]
def reserve(name,n):
    _,i=min((b-a,i) for i,(a,b) in enumerate(free) if b-a>=n)
    a,b=free[i];free[i]=[a+n,b];alloc.append(dict(name=name,origin=a,bytes=n));return a
tableaddr=reserve('numeric-function-table',72)
# Horner coefficients for sin(pi*f/2), f in [0,1], through f**11.
# Nine-byte Canon format: eight unpacked digits, then sign|decimal scale.
coeff=bytes([0,0,0,0,0,0,3,6,0x87,
             0,0,0,0,1,6,0,4,7,
             0,0,0,4,6,8,1,8,0x87,
             0,0,7,9,6,9,2,6,7,
             0,6,4,5,9,6,4,1,0x87,
             1,5,7,0,7,9,6,3,7])
coeffaddr=reserve('trig-polynomial',len(coeff))
misc=bytes([1,0,0,0,0,0,0,1,4, 0,0,0,0,0,0,0,1,0])
miscaddr=reserve('trig-bound-one',len(misc))
extra=dict(TRTABLE=tableaddr,TRCOEFF=coeffaddr,TRCOEFFEND=coeffaddr+54,TRHALFPI=coeffaddr+45,TRBOUND=miscaddr,TRONE=miscaddr+9)
body=(ROOT/'src/basic-trig.asm').read_text();local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|extra).items() if k not in local)
def link(a):return assemble('trig','        OPT H01\n'+defs+f'        ORG ${a:04X}\n'+body)
code,_=link(0x1000);origin=reserve('trig-functions',len(code));code,l=link(origin)
def put(a,data):
    i=a-0x4000;assert cpu[i:i+len(data)]==b'\xff'*len(data);cpu[i:i+len(data)]=data
put(tableaddr,table+b'\x03SIN  \x03COS  ');put(coeffaddr,coeff);put(miscaddr,misc);put(origin,code)
patches=[]
def patch(a,old,new):
    i=a-0x4000;assert cpu[i:i+len(old)]==old,(hex(a),old.hex());assert len(old)==len(new)
    cpu[i:i+len(new)]=new;patches.append(dict(address=a,old=old.hex(),new=new.hex()))
def patchspan(start,end,old,new):
    a=s[start];part=original[a-0x4000:s[end]-0x4000];assert part.count(old)==1
    patch(a+part.index(old),old,new)
patch(s['NFENTRY'],b'\xce'+s['NFTABLE'].to_bytes(2,'big'),b'\xce'+tableaddr.to_bytes(2,'big'))
patchspan('FNMISS','FNFALLBACK',b'\xc3'+s['NFTABLE'].to_bytes(2,'big'),b'\xc3'+tableaddr.to_bytes(2,'big'))
patchspan('FNMISS','FNFALLBACK',b'\xc1\x0a',b'\xc1\x0c')
patchspan('FNENTRY','FNBADARG',b'\x7e'+s['FXDISPATCH'].to_bytes(2,'big'),b'\x7e'+l['TRDISPATCH'].to_bytes(2,'big'))
old=b'Typestar BASIC 0.4.70-dev';assert cpu.count(old)==1;patch(cpu.index(old)+0x4000,old,b'Typestar BASIC 0.4.71-dev')
assert all(x==y or any(a<=i+0x4000<b for a,b in retired) or any(r['origin']<=i+0x4000<r['origin']+r['bytes'] for r in alloc) or any(p['address']<=i+0x4000<p['address']+len(bytes.fromhex(p['new'])) for p in patches) for i,(x,y) in enumerate(zip(original,cpu)))
used=sum(r['bytes'] for r in alloc);recovered=sum(b-a for a,b in retired)
m.update(version='0.4.71-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='SIN/COS CPU candidate',
    trig_allocations=alloc,trig_reclaimed=retired,trig_patches=patches,trig_code_bytes=len(code),trig_data_bytes=144,
    known_free_fragmented_bytes=m['known_free_fragmented_bytes']+recovered-used,
    explicit_free_regions=sorted(r for r in free if r[0]<r[1]),explicit_free_bytes=sum(b-a for a,b in free))
m['lprint_active_code_bytes']=m['font_code_bytes']-245+m['lprint_values_bytes']-97
m['font_code_bytes']-=97 # Original decoder/cache allocation, excluding the separate values module.
m['statement_modules']+=alloc
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
# Do not retain labels that now point into reclaimed code/data. In particular
# future table extensions must follow the relocated table, not its old address.
live={k:v for k,v in s.items() if not any(a<=v<b for a,b in retired)}
(out/'symbols.json').write_text(json.dumps(live|extra|l|dict(NFTABLE=tableaddr,NFTABLEEND=tableaddr+72),indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('trig code',len(code),'recovered',recovered,'allocated',used,'free',m['known_free_fragmented_bytes'])
