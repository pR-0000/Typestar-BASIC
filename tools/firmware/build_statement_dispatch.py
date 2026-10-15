"""Replace repeated keyword tests; share existing token spellings where safe."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re,sys
from validate_array_tokens import ROOT,assemble
sys.path.insert(0,str(ROOT.parents[1]/'ROMReader/tools'))
from disassemble_hd6301 import make_disassembler,absolute_target,CONDITIONAL_BRANCHES
base=ROOT/'build/trig';out=ROOT/'build/statement-dispatch';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());manifest=json.loads((base/'manifest.json').read_text())
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
assert hashlib.sha256(original).hexdigest()=='63a18332f7a73a1692ef91a6fe72efeb214d112563f23368812e573e5d0ea680'
memory=bytearray(65536);memory[0x4000:0xc000]=original
memory[0xc000:]=(ROOT.parents[1]/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin').read_bytes()
rows=json.loads((ROOT/'src/statement-dispatch.json').read_text())
assert len(rows)==46 and len({r['name'] for r in rows})==46
retired=[r['retire'] for r in rows]
for r in rows:
    a,b=r['retire'];ret=r['match_return']
    if a==ret-6:assert memory[a:a+3]==b'\xce'+r['key'].to_bytes(2,'big')
    assert memory[ret-3:ret]==b'\xbd'+s['MATCH'].to_bytes(2,'big')
    assert memory[r['key']:r['key']+len(r['name'])+1]==r['name'].encode()+b'\0'
def inside(a,regions):return any(lo<=a<hi for lo,hi in regions)
# Walk both branch outcomes, plus the native motion phase table. Only decoded
# immediate LDX references may be rewritten to a shared keyword. Any other
# occurrence of the address keeps the original string conservatively.
stages=[int.from_bytes(memory[a:a+2],'big') for a in range(0x7800,0x7822,2)]
roots=[0xffe0,0x5000,0x4400,0x6829,0x6a9e,0x6f83,0x704d,0x716f,0x7154,0x728b,0x77ef,0xaeb2,0xc824,0xc896,0xcc5a,0xcdea,0xf4e0,*stages,*[r['handler'] for r in rows]]
md=make_disassembler();todo=roots[:];instructions={}
while todo:
    pc=todo.pop()
    if pc in instructions or not 0x4000<=pc<65536:continue
    ins=next(md.disasm(bytes(memory[pc:pc+4]),pc,1),None)
    if ins is None or ins.mnemonic in ('fcb','illegal'):continue
    instructions[pc]=ins
    op=ins.mnemonic
    if op in ('jsr','bsr','jmp','bra') or op in CONDITIONAL_BRANCHES:
        dest=absolute_target(ins)
        if dest is not None:todo.append(dest)
    if op=='swi':todo.append(0x704d)
    if op not in ('rts','rti','jmp','bra','swi','wai','slp'):todo.append(pc+ins.size)
cpu=bytearray(original);patches=[];aliases={}
def patch(a,old,new):
    i=a-0x4000;assert cpu[i:i+len(old)]==old,(hex(a),old.hex());assert len(old)==len(new)
    cpu[i:i+len(new)]=new;patches.append(dict(address=a,old=old.hex(),new=new.hex()))
for r in rows:
    old=r['key'];word=r['name'].encode()+b'\0'
    off=original.find(word,0x6800,0x6be0)
    if off<0:continue
    new=off+0x4000;needle=old.to_bytes(2,'big')
    positions=[a for a in range(0x4000,0xffff) if memory[a:a+2]==needle]
    rewrites=[a-1 for a in positions if not inside(a,retired)]
    if not all(a in instructions and memory[a]==0xce and a<0xc000 for a in rewrites):continue
    for a in rewrites:patch(a,b'\xce'+needle,b'\xce'+new.to_bytes(2,'big'))
    aliases[old]=new;r['key']=new;retired.append([old,old+len(word)])
free=sorted([r[:] for r in manifest['explicit_free_regions']]+retired)
merged=[]
for a,b in free:
    if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
    else:merged.append([a,b])
free=merged;alloc=[]
for a,b in retired:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
def reserve(name,n):
    options=[(b-a,i) for i,(a,b) in enumerate(free) if b-a>=n];assert options,(name,n,free)
    _,i=min(options);a,b=free[i];free[i]=[a+n,b];alloc.append(dict(name=name,origin=a,bytes=n));return a
body=(ROOT/'src/statement-dispatch.asm').read_text();local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
def link(a,table):
    defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|dict(CMDTABLE=table)).items() if k not in local)
    return assemble('statement-dispatch','        OPT H01\n'+defs+f'        ORG ${a:04X}\n'+body)
code,_=link(0x1000,0);origin=reserve('statement-lookup',len(code))
tables=[];remaining=rows[:]
while remaining:
    capacity=max((b-a-4)//4 for a,b in free)
    count=min(capacity,len(remaining));assert count>0
    a=reserve('statement-table',4*(count+1));tables.append((a,remaining[:count]));remaining=remaining[count:]
code,l=link(origin,tables[0][0])
def put(a,data):
    i=a-0x4000;assert cpu[i:i+len(data)]==b'\xff'*len(data);cpu[i:i+len(data)]=data
put(origin,code)
for i,(a,entries) in enumerate(tables):
    nxt=tables[i+1][0] if i+1<len(tables) else 0
    put(a,b''.join(r['key'].to_bytes(2,'big')+r['handler'].to_bytes(2,'big') for r in entries)+b'\0\0'+nxt.to_bytes(2,'big'))
patch(s['EXECUTE'],original[s['EXECUTE']-0x4000:s['EXECUTE']-0x4000+3],b'\x7e'+l['CMDENTRY'].to_bytes(2,'big'))
# No new handler may land in a removed lookup prefix or spelling.
assert all(not inside(r['handler'],retired) for r in rows)
assert all(x==y or inside(i+0x4000,retired) or any(r['origin']<=i+0x4000<r['origin']+r['bytes'] for r in alloc) or any(p['address']<=i+0x4000<p['address']+len(bytes.fromhex(p['new'])) for p in patches) for i,(x,y) in enumerate(zip(original,cpu)))
removed=sum(b-a for a,b in retired);added=sum(r['bytes'] for r in alloc)
manifest.update(sha256=hashlib.sha256(cpu).hexdigest(),status='Shared command dispatcher candidate',command_dispatch=rows,
    dispatch_retired_regions=retired,dispatch_new_allocations=alloc,dispatch_patches=patches,dispatch_keyword_aliases=aliases,
    dispatch_net_reclaimed=removed-added,known_free_fragmented_bytes=manifest['known_free_fragmented_bytes']+removed-added,
    explicit_free_regions=[r for r in free if r[0]<r[1]],explicit_free_bytes=sum(b-a for a,b in free))
manifest['statement_modules']+=alloc
live={k:aliases.get(v,v) for k,v in s.items() if v in aliases or not inside(v,retired)}
live['CMDTABLE']=tables[0][0]
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(live|l,indent=2))
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('Removed',removed,'added',added,'shared names',len(aliases),'free',manifest['known_free_fragmented_bytes'])
