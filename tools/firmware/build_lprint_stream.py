"""Place Huffman font and continuous, semicolon-aware LPRINT in audited holes."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/rom-reclaimed';out=ROOT/'build/lprint-stream';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();cpu=bytearray(original)
assert original[s['GPROW']-0x4000+24:s['GPROW']-0x4000+31]==b'\xbd'+s['GPENABLE'].to_bytes(2,'big')+bytes.fromhex('4F5FDDAB')
assert hashlib.sha256(original).hexdigest()=='e34e693b571ef3415ecc3c2b3346af940cda3879ed834fb7eac78e715d3511eb'
blob=(ROOT/'build/paper-font/delta-plain-huffman-b1.bin').read_bytes()
assert len(blob)==3007
maxbits=blob[0];tablelen=145;table=blob[:tablelen]
offsets=[int.from_bytes(blob[tablelen+2*i:tablelen+2*i+2],'big') for i in range(96)]
streams=[blob[tablelen+192+a:tablelen+192+b] for a,b in zip(offsets,offsets[1:])]
free=[r[:] for r in m['explicit_free_regions']];alloc=[]
def reserve(name,n):
    options=[(b-a,i) for i,(a,b) in enumerate(free) if b-a>=n]
    assert options,('no ROM span',name,n)
    _,i=min(options);a,b=free[i];free[i]=[a+n,b]
    alloc.append(dict(name=name,origin=a,bytes=n));return a
body=(ROOT/'src/paper-font-huffman.asm').read_text()+(ROOT/'src/paper-lprint-stream.asm').read_text()
local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
def link(origin,extra):
    defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|extra|dict(HFSTATE=0x1d80)).items() if k not in local)
    return assemble('lprint-stream','        OPT H01\n'+defs+f'        ORG ${origin:04X}\n'+body)
code,_=link(0x1000,dict(HFGLYPHS=0,HFCOUNTS=0,HFSYMBOLS=0,HFMAXBITS=maxbits))
origin=reserve('font-decoder-lprint',len(code))
tableaddr=reserve('font-huffman-table',len(table));indexaddr=reserve('font-glyph-index',285)
places={i:reserve(f'font-glyph-{i+32:02x}',len(streams[i])) for i in sorted(range(95),key=lambda i:-len(streams[i]))}
extra=dict(HFGLYPHS=indexaddr,HFCOUNTS=tableaddr+1,HFSYMBOLS=tableaddr+1+2*maxbits,HFMAXBITS=maxbits)
code,l=link(origin,extra)
def put(a,data):
    i=a-0x4000;assert cpu[i:i+len(data)]==b'\xff'*len(data),(hex(a),len(data))
    cpu[i:i+len(data)]=data
put(origin,code);put(tableaddr,table)
put(indexaddr,b''.join(places[i].to_bytes(2,'big')+bytes([len(streams[i])]) for i in range(95)))
for i in range(95):put(places[i],streams[i])
patches=[]
def patch(a,old,new):
    i=a-0x4000;assert bytes(cpu[i:i+len(old)])==old,(hex(a),old.hex(),cpu[i:i+len(old)].hex())
    assert len(old)==len(new);cpu[i:i+len(new)]=new
    patches.append(dict(address=a,old=old.hex(),new=new.hex()))
def findpatch(label,span,needle,target):
    a=s[label];part=original[a-0x4000:a-0x4000+span];assert part.count(needle)==1,(label,needle.hex())
    patch(a+part.index(needle),needle,b'\xbd'+l[target].to_bytes(2,'big'))
patch(s['LCDDISPATCH'],b'\x7e'+s['PTDISPATCH'].to_bytes(2,'big'),b'\x7e'+l['LPDISPATCH'].to_bytes(2,'big'))
findpatch('RBJOB',90,bytes.fromhex('86403D'),'LPSIZE')
findpatch('RBPRINT',40,bytes.fromhex('C30040'),'LPNEXT')
findpatch('RBRENDERED',25,b'\x7f'+(s['GPDESC']+1).to_bytes(2,'big'),'LPFORMAT')
findpatch('RBRENDERBAND',25,b'\xbd'+s['LNSELECT'].to_bytes(2,'big'),'LPSELECT')
findpatch('RBPRINT',5,b'\xbd'+s['GPPRINT'].to_bytes(2,'big'),'LPPRINT')
findpatch('RBROW',5,b'\xbd'+s['GPROW'].to_bytes(2,'big'),'LPROW')
# A 72-column carriage return takes 4608 phase ticks plus stage overhead.
# The old eight-tile bridge's 4096-tick guard stopped it 8 columns early.
# Keep a finite guard, large enough for the new maximum (not a fixed delay).
a=s['GPCALL'];part=original[a-0x4000:a-0x4000+35]
needle=bytes.fromhex('CC1000');assert part.count(needle)==1
patch(a+part.index(needle),needle,bytes.fromhex('CC2000'))
old=b'Typestar BASIC 0.4.65-dev';new=b'Typestar BASIC 0.4.68-dev'
assert cpu.count(old)==1;patch(cpu.index(old)+0x4000,old,new)
assert all(x==y or any(r['origin']<=i+0x4000<r['origin']+r['bytes'] for r in alloc) or any(p['address']<=i+0x4000<p['address']+len(bytes.fromhex(p['new'])) for p in patches) for i,(x,y) in enumerate(zip(original,cpu)))
used=sum(r['bytes'] for r in alloc)
m.update(version='0.4.68-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='Font and literal LPRINT CPU candidate',font_allocations=alloc,font_patches=patches,font_data_bytes=used-len(code),font_code_bytes=len(code),known_free_fragmented_bytes=m['known_free_fragmented_bytes']-used,explicit_free_regions=[r for r in free if r[0]<r[1]],explicit_free_bytes=sum(b-a for a,b in free),font_scratch=[0x1d80,0x1d99],lprint_scratch=[0x1da5,0x1dc2])
m['statement_modules']+=alloc
m['lprint_columns']=72
m['lprint_column_state']={'valid_address':s['PMVALID'],'valid_value':3,'column_address':s['PMX']+1,
    'ownership':'Aliases manual motor position; valid only while PMVALID=3'}
m['native_stage_tick_limit']=8192
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|extra|l,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('code',len(code),'font',used-len(code),'free',m['known_free_fragmented_bytes'])
