"""Link decimal math extensions in audited native editor regions."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re,random
from decimal import Decimal
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/strings';out=ROOT/'build/extensions';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();cpu=bytearray(original)
audit=json.loads((out/'reclaim-audit.json').read_text());assert audit['base_sha256']==hashlib.sha256(original).hexdigest()
retired=audit['regions']+[[s['NFTABLE'],s['NFTABLE']+72]]
glyphs=[r for r in m['font_allocations'] if re.fullmatch(r'font-glyph-[0-9a-f]{2}',r['name'])]
assert len(glyphs)==95
saved={r['name']:original[r['origin']-0x4000:r['origin']-0x4000+r['bytes']] for r in glyphs}
glyphspans=[[r['origin'],r['origin']+r['bytes']] for r in glyphs]
free=[]
for a,b in sorted(m['explicit_free_regions']+retired+glyphspans):
 if free and a<=free[-1][1]:free[-1][1]=max(b,free[-1][1])
 else:free.append([a,b])
for a,b in free:cpu[a-0x4000:b-0x4000]=bytes([255])*(b-a)
extra={};dataalloc=[]
def reserve(name,n):
 options=[(b-a,i) for i,(a,b) in enumerate(free) if b-a>=n];assert options,(name,n)
 _,i=min(options);a,b=free[i];free[i]=[a+n,b];dataalloc.append(dict(name=name,origin=a,bytes=n));return a
# Nine-byte constants use the same unpacked coefficient/scale as the maskROM.
for name,value in [('XMTWO','2'),('XMEPS','0.000001'),('XMTHRESH','0.4142136'),('XMQUARTERPI','0.7853982'),('XMLN2','0.6931472'),('XM18','18.000001'),('XMLOGLOW','0.75'),('XMLOGHIGH','1.5')]:
 d=Decimal(value);scale=max(0,-d.as_tuple().exponent);digits=f'{int(d*(10**scale)):08d}';assert len(digits)==8
 raw=bytes(map(int,digits))+bytes([scale]);a=reserve(name,9);extra[name]=a;cpu[a-0x4000:a-0x4000+9]=raw
table=original[s['NFTABLE']-0x4000:s['NFTABLE']-0x4000+72]+b'\x03TAN  \x03ATN  \x03LOG  \x03EXP  '
a=reserve('extended-function-table',len(table));cpu[a-0x4000:a-0x4000+len(table)]=table;extra['NFTABLE']=a;extra['NFTABLEEND']=a+len(table)
names=['math-extra-core','math-extra-tan','math-extra-series','math-extra-atn','math-extra-log','math-extra-exp','math-extra-power','paper-glyph-command','paper-glyph-stage','paper-glyph-render','paper-glyph-submit']
bodies={n:(ROOT/'src'/f'{n}.asm').read_text() for n in names}
labels={n:set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',b,re.M)) for n,b in bodies.items()}
alllabels=set.union(*labels.values());linked=dict.fromkeys(alllabels,0x4000)
def link(name,a):
    defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|extra|linked).items() if k not in labels[name])
    return assemble(name,' OPT H01\n'+defs+f' ORG ${a:04X}\n'+bodies[name])
alloc=[]
sizes={name:len(link(name,0x1000)[0]) for name in names}
for name in sorted(names,key=lambda n:-sizes[n]):
    size=sizes[name]
    options=[(b-a,i) for i,(a,b) in enumerate(free) if b-a>=size];assert options,(name,size)
    _,i=min(options);a,b=free[i];free[i]=[a+size,b]
    raw,ls=link(name,a);linked.update({k:v for k,v in ls.items() if k in labels[name]})
    alloc.append(dict(name=name,origin=a,bytes=size))
for r in alloc:
    raw,_=link(r['name'],r['origin']);assert len(raw)==r['bytes']
    a=r['origin']-0x4000;assert cpu[a:a+len(raw)]==bytes([255])*len(raw);cpu[a:a+len(raw)]=raw
patches=[]
def patch(a,old,new):
 i=a-0x4000;assert cpu[i:i+len(old)]==old,(hex(a),old.hex());assert len(old)==len(new)
 cpu[i:i+len(new)]=new;patches.append(dict(address=a,old=old.hex(),new=new.hex()))
def replace_span(a,b,old,new,count=1):
 part=original[a-0x4000:b-0x4000];assert part.count(old)==count,(hex(a),old.hex(),part.count(old))
 offset=0
 for _ in range(count):
  j=part.index(old,offset);patch(a+j,old,new);offset=j+len(old)
replace_span(s['STVALFALLBACK'],s['STVALOPEN'],b'\xce'+s['NFTABLE'].to_bytes(2,'big'),b'\xce'+extra['NFTABLE'].to_bytes(2,'big'))
replace_span(s['FNMISS'],s['FNFALLBACK'],b'\xc3'+s['NFTABLE'].to_bytes(2,'big'),b'\xc3'+extra['NFTABLE'].to_bytes(2,'big'))
replace_span(s['FNMISS'],s['FNFALLBACK'],b'\xc1\x0c',b'\xc1\x10')
replace_span(s['FNENTRY'],s['FNBADARG'],b'\x7e'+s['TRDISPATCH'].to_bytes(2,'big'),b'\x7e'+linked['XMDISPATCH'].to_bytes(2,'big'))
for lo,hi,count in [('DTERM','DT_RETURN',2),('DA_PLUS','DA_GROUP',2)]:
 replace_span(s[lo],s[hi],b'\xbd'+s['DATOM'].to_bytes(2,'big'),b'\xbd'+linked['XPATOM'].to_bytes(2,'big'),count)
# GLYPH uses raw format and a dedicated band callback; other jobs are unchanged.
patch(s['LNSELECT'],b'\x7e'+s['SBBAND'].to_bytes(2,'big'),b'\x7e'+linked['SGSELECT'].to_bytes(2,'big'))
patch(s['STCOMMAND'],b'\x7f'+s['STDEPTH'].to_bytes(2,'big'),b'\xbd'+linked['SGRESET'].to_bytes(2,'big'))
a=reserve('glyph-keyword',6);cpu[a-0x4000:a-0x4000+6]=b'GLYPH\0';key=a
a=reserve('glyph-command-table',8);cpu[a-0x4000:a-0x4000+8]=key.to_bytes(2,'big')+linked['SGPARSE'].to_bytes(2,'big')+bytes(4)
last=next(r for r in m['data_allocations'] if r['name']=='data-command-table')
patch(last['origin']+last['bytes']-2,bytes(2),a.to_bytes(2,'big'))
m['command_dispatch'].append(dict(name='GLYPH',key=key,handler=linked['SGPARSE']))
fontalloc=[]
packing_free=[r[:] for r in free]
for seed in range(200):
    pending=sorted(glyphs,key=lambda r:r['name']);random.Random(seed).shuffle(pending)
    placements=[];free=[r[:] for r in packing_free]
    for i in sorted(range(len(free)),key=lambda i:free[i][1]-free[i][0]):
        a,b=free[i];capacity=b-a;choices={0:[]}
        for j,r in enumerate(pending):
            for n,selection in sorted(list(choices.items()),reverse=True):
                nn=n+r['bytes']
                if nn<=capacity and nn not in choices:choices[nn]=selection+[j]
        selected=choices[max(choices)]
        for j in selected:
            r=pending[j];placements.append((a,r));a+=r['bytes']
        pending=[r for j,r in enumerate(pending) if j not in selected];free[i]=[a,b]
    if not pending:break
assert not pending,[(r['name'],r['bytes']) for r in pending]
for a,r in placements:
    fontalloc.append(dict(name=r['name'],origin=a,bytes=r['bytes']))
    cpu[a-0x4000:a-0x4000+r['bytes']]=saved[r['name']]
    char=int(r['name'].rsplit('-',1)[1],16);p=s['HFGLYPHS']+(char-32)*3
    assert original[p-0x4000:p-0x4000+3]==r['origin'].to_bytes(2,'big')+bytes([r['bytes']])
    patch(p,r['origin'].to_bytes(2,'big'),a.to_bytes(2,'big'))
m['font_allocations']=[r for r in m['font_allocations'] if r not in glyphs]+fontalloc
old=b'Typestar BASIC 0.4.73-dev';a=original.index(old)+0x4000;patch(a,old,b'Typestar BASIC 0.4.74-dev')
used=sum(r['bytes'] for r in alloc+dataalloc);recovered=sum(b-a for a,b in retired)
allowed=retired+glyphspans+m['explicit_free_regions']+[[r['address'],r['address']+len(bytes.fromhex(r['new']))] for r in patches]
assert all(x==y or any(a<=i+0x4000<b for a,b in allowed) for i,(x,y) in enumerate(zip(original,cpu)))
m.update(version='0.4.74-dev',status='Extended decimal math and custom paper glyphs; hardware validation pending',sha256=hashlib.sha256(cpu).hexdigest(),extension_allocations=alloc+dataalloc,extension_bytes=used,extension_reclaimed=retired,extension_patches=patches,known_free_fragmented_bytes=m['known_free_fragmented_bytes']+recovered-used,explicit_free_regions=[r for r in free if r[0]<r[1]],explicit_free_bytes=sum(b-a for a,b in free))
m['statement_modules']+=alloc+dataalloc
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|extra|linked,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('Extended math',used,'reclaimed',recovered,'free',m['known_free_fragmented_bytes'])
