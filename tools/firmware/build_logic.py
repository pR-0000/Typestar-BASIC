"""Link logical operators, remainder and ELSE in the .74 image."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re,random
from decimal import Decimal
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/extensions';out=ROOT/'build/logic';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();cpu=bytearray(original)
assert hashlib.sha256(original).hexdigest()=='9a604e225e3018a556cb95be1c2eca2011611c012d63264166d5e404f2ff5652'
retired=[[s['DEXPR']+3,s['DATOM']],[s['DCONDITION']+3,s['CCMPVALUE']],
         [s['STCONDITION'],s['STCMP']],[s['SCSCAN']+3,s['STSEGTWOEND']],
         [0x847d,0x8494],[0x9526,0x9542],[0x95da,0x95f7],[0xad2c,0xad4b],[0x6875,0x69ab],[0x6ca0,0x6cbd]]
glyphs=[r for r in m['font_allocations'] if re.fullmatch(r'font-glyph-[0-9a-f]{2}',r['name'])]
assert len(glyphs)==95
saved={r['name']:original[r['origin']-0x4000:r['origin']-0x4000+r['bytes']] for r in glyphs}
glyphspans=[[r['origin'],r['origin']+r['bytes']] for r in glyphs]
free=[]
for a,b in sorted(m['explicit_free_regions']+retired+glyphspans):
 if free and a<=free[-1][1]:free[-1][1]=max(b,free[-1][1])
 else:free.append([a,b])
for a,b in free:cpu[a-0x4000:b-0x4000]=bytes([255])*(b-a)
extra={'LERECORDEND':0x1CD5};dataalloc=[]
def reserve(name,n):
 options=[(b-a,i) for i,(a,b) in enumerate(free) if b-a>=n];assert options,(name,n)
 _,i=min(options);a,b=free[i];free[i]=[a+n,b];dataalloc.append(dict(name=name,origin=a,bytes=n));return a
names=['logic-expression','logic-condition','logic-operators','logic-operator-table','logic-apply','logic-else','logic-else-match','logic-segments']
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
    _,i=min(options,key=lambda v: ((v[0]-size) if 0<v[0]-size<17 else 0,v[0]));a,b=free[i];free[i]=[a+size,b]
    raw,ls=link(name,a);linked.update({k:v for k,v in ls.items() if k in labels[name]})
    alloc.append(dict(name=name,origin=a,bytes=size))
for r in alloc:
    raw,_=link(r['name'],r['origin']);assert len(raw)==r['bytes']
    a=r['origin']-0x4000;assert cpu[a:a+len(raw)]==bytes([255])*len(raw);cpu[a:a+len(raw)]=raw
patches=[]
def patch(a,old,new):
 i=a-0x4000;assert cpu[i:i+len(old)]==old,(hex(a),old.hex());assert len(old)==len(new)
 cpu[i:i+len(new)]=new;patches.append(dict(address=a,old=old.hex(),new=new.hex()))
def jump(a,target,op=0x7e):
 patch(a,original[a-0x4000:a-0x4000+3],bytes([op])+target.to_bytes(2,'big'))
jump(s['DEXPR'],linked['LXENTRY'])
jump(s['DCONDITION'],linked['LXCONDITION'])
jump(s['SCSCAN'],linked['LESCSCAN'])
jump(s['SCEXP'],linked['LESTART'],0xbd)
jump(s['DECIF'],linked['LECOND'],0xbd)
jump(s['STCMPREADY']+3,linked['LXSTRRIGHT'],0xbd)
# False branch formerly loaded SCEND; preserve the true branch dispatch.
lo=s['CIFMODE'];part=original[lo-0x4000:s['CIFDISPATCH']-0x4000]
a=lo+part.index(b'\xfe'+extra['LERECORDEND'].to_bytes(2,'big'))
jump(a,linked['LEFALSE'])
a=reserve('else-keyword',5);cpu[a-0x4000:a-0x4000+5]=b'ELSE\0';key=a
a=reserve('else-command-table',8);cpu[a-0x4000:a-0x4000+8]=key.to_bytes(2,'big')+linked['LEEND'].to_bytes(2,'big')+bytes(4)
last=next(r for r in m['extension_allocations'] if r['name']=='glyph-command-table')
patch(last['origin']+6,bytes(2),a.to_bytes(2,'big'))
m['command_dispatch'].append(dict(name='ELSE',key=key,handler=linked['LEEND']))
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
old=b'Typestar BASIC 0.4.74-dev';a=original.index(old)+0x4000;patch(a,old,b'Typestar BASIC 0.4.75-dev')
used=sum(r['bytes'] for r in alloc+dataalloc);recovered=sum(b-a for a,b in retired)
allowed=retired+glyphspans+m['explicit_free_regions']+[[r['address'],r['address']+len(bytes.fromhex(r['new']))] for r in patches]
assert all(x==y or any(a<=i+0x4000<b for a,b in allowed) for i,(x,y) in enumerate(zip(original,cpu)))
m.update(version='0.4.75-dev',status='Logical expressions and inline ELSE; hardware validation pending',sha256=hashlib.sha256(cpu).hexdigest(),logic_allocations=alloc+dataalloc,logic_bytes=used,logic_reclaimed=retired,logic_patches=patches,known_free_fragmented_bytes=m['known_free_fragmented_bytes']+recovered-used,explicit_free_regions=[r for r in free if r[0]<r[1]],explicit_free_bytes=sum(b-a for a,b in free))
# Native keyboard lookup data: reachable through an indexed table address.
assert cpu[0x6d1d-0x4000:0x6d44-0x4000]==original[0x6d1d-0x4000:0x6d44-0x4000]
m['statement_modules']+=alloc+dataalloc
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|extra|linked,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('Logical expressions',used,'reclaimed',recovered,'free',m['known_free_fragmented_bytes'])
