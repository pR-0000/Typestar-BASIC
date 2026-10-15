"""Link numeric DATA commands, packing unchanged compressed glyph streams anew."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re,random
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/statement-dispatch';out=ROOT/'build/data';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();cpu=bytearray(original)
assert hashlib.sha256(original).hexdigest()=='a4b97575dac39eb720294c886045283d78ce84b9df4a436fefad5389836201fb'
glyphs=[r for r in m['font_allocations'] if re.fullmatch(r'font-glyph-[0-9a-f]{2}',r['name'])]
assert len(glyphs)==95
# Chain-only fallbacks, with no other absolute references or reachable entries.
retired=[[a,a+3] for a in (0x53e1,0x483a,0x4ac7,0x90ae,0x5426)]
assert all(original[a-0x4000]==0x7e for a,b in retired)
helpold=original[s['HELPMSG']-0x4000:].split(b'\0')[0]+b'\0'
assert b'signed 16 bit' in helpold and b'lines 1..32' in helpold
helpnew=b'LIST RUN NEW LOAD SAVE MEM\0'
retired.append([s['HELPMSG']+len(helpnew),s['HELPMSG']+len(helpold)])
tracked=[[0x4c21,0x4c28],[0x924c,0x924d],[0x916c,0x9175],[0x636b,0x637f],
         [0x46f3,0x4704],[0x588d,0x589e]]
assert all(original[a-0x4000:b-0x4000]==bytes([255])*(b-a) for a,b in tracked)
assert all(not (a<y and x<b) for a,b in tracked for x,y in m['explicit_free_regions'])
free=[r[:] for r in m['explicit_free_regions']]+tracked+retired+[[r['origin'],r['origin']+r['bytes']] for r in glyphs]
saved={r['name']:original[r['origin']-0x4000:r['origin']-0x4000+r['bytes']] for r in glyphs}
merged=[]
for a,b in sorted(free):
    if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
    else:merged.append([a,b])
free=merged;alloc=[];patches=[]
for a,b in free:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
def reserve(name,n):
    options=[(b-a,i) for i,(a,b) in enumerate(free) if b-a>=n]
    assert options,(name,n,free)
    _,i=min(options);a,b=free[i];free[i]=[a+n,b];alloc.append(dict(name=name,origin=a,bytes=n));return a
def put(a,data):
    i=a-0x4000;assert cpu[i:i+len(data)]==b'\xff'*len(data);cpu[i:i+len(data)]=data
def patch(a,old,new):
    i=a-0x4000;assert cpu[i:i+len(old)]==old,(hex(a),old.hex());assert len(old)==len(new)
    cpu[i:i+len(new)]=new;patches.append(dict(address=a,old=old.hex(),new=new.hex()))
patch(s['HELPMSG'],helpold[:len(helpnew)],helpnew)
assert original[0x6009]==0x7e
extra=dict(DAOLDINIT=int.from_bytes(original[0x600a:0x600c],'big'),ARADDRESS=0x9a8b,ARWRITE=0x9b9d)
for name,data in [('DANAME',b'DATA\0'),('DAREADNAME',b'READ\0'),('DARESTORENAME',b'RESTORE\0'),('DAOUTMSG',b'?OUT OF DATA\0')]:
    a=reserve(name,len(data));put(a,data);extra[name]=a
helpers=[]
for name,body in [('DAHEAP','DAHEAP JSR DARESET\n JMP DAOLDINIT\nDARESTORE JSR EOS\nDARESET CLR $1948\n CLR $1949\n CLR $194C\n RTS\n'),
                  ('DAWHITE','DAWHITE CPX $194A\n BHS DAWHITERET\n LDAA ,X\n CMPA #32\n BNE DAWHITERET\n INX\n BRA DAWHITE\nDAWHITERET RTS\n')]:
    loc=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|extra).items() if k not in loc)
    def helper(a):return assemble('data-'+name,' OPT H01\n'+defs+f' ORG ${a:04X}\n'+body)
    raw,_=helper(0x1000);a=reserve(name,len(raw));raw,hs=helper(a);put(a,raw);extra.update({k:v for k,v in hs.items() if k in loc})
# These existing array entry points are pinned by their current opcodes.
assert original[0x5a8b:0x5a8e]==b'\xbd\xa0\x1f'
assert original[0x5b9d:0x5ba0]==b'\xa6\x00\x3c'
body=(ROOT/'src/basic-data.asm').read_text();local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|extra).items() if k not in local)
def link(a):return assemble('data','        OPT H01\n'+defs+f'        ORG ${a:04X}\n'+body)
code,_=link(0x1000);origin=reserve('data-commands',len(code));code,l=link(origin);put(origin,code)
table=reserve('data-command-table',16)
put(table,b''.join(extra[k].to_bytes(2,'big')+v.to_bytes(2,'big') for k,v in
    [('DANAME',s['EXECRET']),('DAREADNAME',l['DAREAD']),('DARESTORENAME',extra['DARESTORE'])])+bytes(4))
last=[r for r in m['dispatch_new_allocations'] if r['name']=='statement-table'][-1]
patch(last['origin']+last['bytes']-2,bytes(2),table.to_bytes(2,'big'))
patch(0xa009,original[0x6009:0x600c],b'\x7e'+extra['DAHEAP'].to_bytes(2,'big'))
data_count=len(alloc)
# Fill small holes first with an exact subset-sum, rather than stranding the
# shortest streams at the end of a descending greedy placement.
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
    alloc.append(dict(name=r['name'],origin=a,bytes=r['bytes']))
    put(a,saved[r['name']])
    char=int(r['name'].rsplit('-',1)[1],16);p=s['HFGLYPHS']+(char-32)*3
    assert original[p-0x4000:p-0x4000+3]==r['origin'].to_bytes(2,'big')+bytes([r['bytes']])
    patch(p,r['origin'].to_bytes(2,'big'),a.to_bytes(2,'big'))
old=b'Typestar BASIC 0.4.71-dev';assert cpu.count(old)==1
patch(cpu.index(old)+0x4000,old,b'Typestar BASIC 0.4.72-dev')
allowed=m['explicit_free_regions']+tracked+retired+[[r['origin'],r['origin']+r['bytes']] for r in glyphs]
allowed += [[p['address'],p['address']+len(bytes.fromhex(p['new']))] for p in patches]
assert all(x==y or any(a<=i+0x4000<b for a,b in allowed) for i,(x,y) in enumerate(zip(original,cpu)))
used=sum(r['bytes'] for r in alloc[:data_count]);recovered=sum(b-a for a,b in retired)
m.update(version='0.4.72-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='Numeric DATA/READ/RESTORE CPU candidate',
    data_allocations=alloc[:data_count],data_patches=patches,data_code_bytes=len(code),data_reclaimed=retired,
    known_free_fragmented_bytes=m['known_free_fragmented_bytes']+recovered-used,
    explicit_free_regions=sorted(r for r in free if r[0]<r[1]),explicit_free_bytes=sum(b-a for a,b in free))
m['font_allocations']=[r for r in m['font_allocations'] if r not in glyphs]+alloc[data_count:]
m['statement_modules']+=alloc[:data_count]
m['other_tracked_fragment_bytes']-=sum(b-a for a,b in tracked)
m['command_dispatch'] += [dict(name=name,key=extra[key],handler=handler) for name,key,handler in
    [('DATA','DANAME',s['EXECRET']),('READ','DAREADNAME',l['DAREAD']),('RESTORE','DARESTORENAME',extra['DARESTORE'])]]
m['data_total_bytes']=used
m['data_glyph_packing_seed']=seed
m['data_promoted_tracked_regions']=tracked
assert m['known_free_fragmented_bytes']==m['explicit_free_bytes']+m['other_tracked_fragment_bytes']
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|extra|l,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('DATA code',len(code),'free',m['known_free_fragmented_bytes'],'explicit',m['explicit_free_bytes'])
