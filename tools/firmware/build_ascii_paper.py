""".76: correct regional punctuation and add ORIGIN [known head coordinate].

Rebuild the fixed-ABI Huffman table; preserve all 85 unchanged decoded glyphs.
Elide zero suffix bytes and supply bounded virtual zero bits after HFSTOP.
Only audited font slots/free spans and explicit decoder/dispatch/version hooks may change.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,random,re
from validate_array_tokens import ROOT,assemble
from paper_ascii_font import corrected
base=ROOT/'build/logic';out=ROOT/'build/ascii-paper';out.mkdir(exist_ok=True)
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
assert hashlib.sha256(original).hexdigest()=='87c468bbdee79da1cf5ccd84eda693b38a74a262f5a8d8c4df2fabceb9dbeda6'
cpu=bytearray(original);s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
trace=json.loads((ROOT/'build/paper-font/native-trace.json').read_text())
expected,fixes=corrected(trace)
# Rebuild the canonical code for the corrected alphabet, retaining its
# 12-level fixed ABI. Reuse the original 145-byte table allocation.
from collections import Counter
import heapq
blocks={ch:bytes(v^(r[i-3] if i>=3 else 0) for i,v in enumerate(r)) for ch,r in expected.items()}
freq=Counter(v for r in blocks.values() for v in r)
heap=[(n,v,{v:0}) for v,n in freq.items()];heapq.heapify(heap);serial=256
while len(heap)>1:
    n,_,left=heapq.heappop(heap);k,_,right=heapq.heappop(heap)
    heapq.heappush(heap,(n+k,serial,{v:d+1 for v,d in (left|right).items()}));serial+=1
lengths=heap[0][2];assert max(lengths.values())<=s['HFMAXBITS']
order=sorted(lengths,key=lambda v:(lengths[v],v));codes={};code=0;prev=0
for v in order:
    bits=lengths[v];code<<=bits-prev;codes[v]=(code,bits);code+=1;prev=bits
counts=b''.join(sum(d==n for d in lengths.values()).to_bytes(2,'big') for n in range(1,s['HFMAXBITS']+1))
table=bytes([s['HFMAXBITS']])+counts+bytes(order)
old_table=next(r for r in m['font_allocations'] if r['name']=='font-huffman-table')
assert len(table)<=old_table['bytes']
ta=old_table['origin']-0x4000;cpu[ta:ta+old_table['bytes']]=table.ljust(old_table['bytes'],b'\xff')
def encode(raw):
    delta=bytes(v^(raw[i-3] if i>=3 else 0) for i,v in enumerate(raw))
    bits=''.join(format(codes[v][0],f'0{codes[v][1]}b') for v in delta)
    bits+='0'*(-len(bits)%8)
    return bytes(int(bits[i:i+8],2) for i in range(0,len(bits),8)).rstrip(b'\0')
glyphs=[r for r in m['font_allocations'] if re.fullmatch(r'font-glyph-[0-9a-f]{2}',r['name'])]
streams={f'font-glyph-{ord(ch):02x}':encode(raw) for ch,raw in expected.items()}
free=[]
for a,b in sorted(m['explicit_free_regions']+[[r['origin'],r['origin']+r['bytes']] for r in glyphs]):
    if free and a<=free[-1][1]:free[-1][1]=max(b,free[-1][1])
    else:free.append([a,b])
spans=[r[:] for r in free]
for a,b in free:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
# Each glyph always produces exactly 93 bytes. Missing suffix bits are zero;
# the canonical zero-delta code is all zeros. Never read beyond HFSTOP.
assert codes[0][0]==0
branch=s['HFGETBIT']+11
_,i=min((b-a,i) for i,(a,b) in enumerate(free) if b-a>=3 and -128<=a-(branch+2)<=127)
za,zb=free[i];cpu[za-0x4000:za-0x4000+3]=bytes.fromhex('5f0c39');free[i]=[za+3,zb]
zero_alloc=dict(name='font-zero-suffix',origin=za,bytes=3)
assert cpu[branch-0x4000]==0x24
cpu[branch-0x4000+1]=(za-branch-2)&255

source=(ROOT/'src/paper-origin-coordinate.asm').read_text()
parts=re.split(r'; @island \w+\n',source)
local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',source,re.M));ls=dict.fromkeys(local,0x4000)
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items() if k not in local)
origin_allocs=[]
for j,body in enumerate(parts):
    names=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    d=defs+''.join(f'{k} EQU ${v:04X}\n' for k,v in ls.items() if k not in names)
    rr,_=assemble('origin-part',' OPT H01\n'+d+' ORG $1000\n'+body)
    _,i=min((b-a,i) for i,(a,b) in enumerate(free) if b-a>=len(rr));a,b=free[i]
    rr,ll=assemble('origin-part',' OPT H01\n'+d+f' ORG ${a:04X}\n'+body)
    ls.update({k:ll[k] for k in names});origin_allocs.append(dict(name=f'origin-{j}',origin=a,bytes=len(rr)))
    free[i]=[a+len(rr),b]
for body,r in zip(parts,origin_allocs):
    names=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    d=defs+''.join(f'{k} EQU ${v:04X}\n' for k,v in ls.items() if k not in names)
    rr,_=assemble(r['name'],' OPT H01\n'+d+f" ORG ${r['origin']:04X}\n"+body)
    a=r['origin']-0x4000;cpu[a:a+len(rr)]=rr
# Fit CLEAR into audited 6..8-byte fragments that cannot hold font streams.
clear_sections=re.split(r'; @island (clear-[a-z]+)\n',(ROOT/'src/basic-clear.asm').read_text())
clear_parts=dict(zip(clear_sections[1::2],clear_sections[2::2]))
cl={label:0x4000 for label in ('CLENTRY','CLCHECK','CLRESET','CLAPPLY')};clear_allocs=[]
for name,body in clear_parts.items():
    label=body.split()[0];n=6 if name in ('clear-entry','clear-check') else 7
    _,i=min((b-a,i) for i,(a,b) in enumerate(free) if b-a>=n);a,b=free[i]
    cl[label]=a;clear_allocs.append(dict(name=name,origin=a,bytes=n));free[i]=[a+n,b]
for r in clear_allocs:
    body=clear_parts[r['name']];label=body.split()[0]
    cd=defs+''.join(f'{k} EQU ${v:04X}\n' for k,v in cl.items() if k!=label)
    cr,_=assemble(r['name'],' OPT H01\n'+cd+f" ORG ${r['origin']:04X}\n"+body)
    assert len(cr)==r['bytes'];a=r['origin']-0x4000;cpu[a:a+len(cr)]=cr
_,i=min((b-a,i) for i,(a,b) in enumerate(free) if b-a>=6);ka,kb=free[i]
cpu[ka-0x4000:ka-0x4000+6]=b'CLEAR\0';free[i]=[ka+6,kb]
_,i=min((b-a,i) for i,(a,b) in enumerate(free) if b-a>=8);kt,kb=free[i]
cpu[kt-0x4000:kt-0x4000+8]=ka.to_bytes(2,'big')+cl['CLENTRY'].to_bytes(2,'big')+bytes(4)
free[i]=[kt+8,kb];key_allocs=[dict(name='clear-keyword',origin=ka,bytes=6),dict(name='clear-command-table',origin=kt,bytes=8)]
packing=[r[:] for r in free]
# Deterministic best-fill search over the audited bins; suffix elision makes
# short streams useful in small holes. No external solver is needed.
empty=[k for k,v in streams.items() if not v]
for seed in range(1000):
    pending=[k for k,v in streams.items() if v];random.Random(seed).shuffle(pending)
    free=[r[:] for r in packing];placed=[]
    for i in sorted(range(len(free)),key=lambda i:free[i][1]-free[i][0]):
        a,b=free[i];choices={0:[]}
        for j,name in enumerate(pending):
            for n,selected in sorted(list(choices.items()),reverse=True):
                nn=n+len(streams[name])
                if nn<=b-a and nn not in choices:choices[nn]=selected+[j]
        selected=choices[max(choices)]
        for j in selected:
            name=pending[j];placed.append(dict(name=name,origin=a,bytes=len(streams[name])));a+=len(streams[name])
        pending=[name for j,name in enumerate(pending) if j not in selected];free[i]=[a,b]
    if not pending:break
assert not pending,pending
placed += [dict(name=k,origin=za,bytes=0) for k in empty]
print('Font bytes',sum(map(len,streams.values())),'packing seed',seed,flush=True)
allowed=spans[:]+[[branch,branch+2]]+[[old_table["origin"],old_table["origin"]+old_table["bytes"]]]
for r in placed:
    a=r['origin']-0x4000;cpu[a:a+r['bytes']]=streams[r['name']]
    p=s['HFGLYPHS']+3*(int(r['name'][-2:],16)-32);allowed.append([p,p+3])
    cpu[p-0x4000:p-0x4000+3]=r['origin'].to_bytes(2,'big')+bytes([r['bytes']])
last=next(r for r in m['logic_allocations'] if r['name']=='else-command-table')
p=last['origin']+6;assert cpu[p-0x4000:p-0x4000+2]==bytes(2)
cpu[p-0x4000:p-0x4000+2]=kt.to_bytes(2,'big');allowed.append([p,p+2])
m['command_dispatch'].append(dict(name='CLEAR',key=ka,handler=cl['CLENTRY']))
a=s['MCORIGIN'];cpu[a-0x4000:a-0x4000+3]=b'\x7e'+ls['OCENTRY'].to_bytes(2,'big');allowed.append([a,a+3])
old=b'Typestar BASIC 0.4.75-dev';a=original.index(old);cpu[a:a+len(old)]=b'Typestar BASIC 0.4.76-dev';allowed.append([a+0x4000,a+0x4000+len(old)])
assert all(x==y or any(a<=i+0x4000<b for a,b in allowed) for i,(x,y) in enumerate(zip(original,cpu)))
free=[r for r in free if r[0]<r[1]];delta=sum(len(streams[r['name']])-r['bytes'] for r in glyphs)+sum(r['bytes'] for r in origin_allocs)+sum(r["bytes"] for r in clear_allocs+key_allocs)+3
m.update(version='0.4.76-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='ASCII punctuation and ORIGIN coordinate; hardware validation pending',
         font_data_bytes=m['font_data_bytes']+sum(len(streams[r['name']])-r['bytes'] for r in glyphs),
         font_allocations=[r for r in m['font_allocations'] if r not in glyphs]+placed,
         ascii_allocations=origin_allocs+clear_allocs+key_allocs+[zero_alloc],ascii_changed_characters=list(fixes),font_zero_suffix=True,
         explicit_free_regions=free,explicit_free_bytes=sum(b-a for a,b in free),
         known_free_fragmented_bytes=m['known_free_fragmented_bytes']-delta)
m['statement_modules'] += origin_allocs+clear_allocs+key_allocs+[zero_alloc]
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|{k:ls[k] for k in local}|cl,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
(out/'font-expected.json').write_text(json.dumps({k:v.hex() for k,v in expected.items()},indent=2))
print('Origin code',sum(r['bytes'] for r in origin_allocs),'net ROM change',delta,'free',m['known_free_fragmented_bytes'])
