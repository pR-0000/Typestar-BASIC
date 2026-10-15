""".80 text spacing; guarded retired UI/padding reclamation, no hardware flash."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re,random,sys
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/paper-alignment';out=ROOT/'build/paper-spacing';out.mkdir(exist_ok=True)
old=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
assert hashlib.sha256(old).hexdigest()=='6bc525947cdf3ec7aa5d9f3e5b11c7d8bed4f94c75d8055b16588b15b621aba0'
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text());cpu=bytearray(old);patches=[];allowed=[]
def patch(a,expected,new):
    assert len(expected)==len(new) and cpu[a-0x4000:a-0x4000+len(expected)]==expected,hex(a)
    cpu[a-0x4000:a-0x4000+len(new)]=new;allowed.append([a,a+len(new)])
    patches.append(dict(address=a,old=expected.hex(),new=new.hex()))
assert old[0x2829:0x2830]==bytes.fromhex('0f4f97377e5000')
# The old Canon foreground loop/event table follows an unconditional BASIC
# handoff; its dispatcher at 6875 was already retired in .75. Check no live
# direct edge or immediate operand still refers to these bytes below.
# Seven old padding NOPs can become a two-byte branch over five free bytes.
assert old[s['LVWIDTH']-7-0x4000:s['LVWIDTH']-0x4000]==bytes([1])*7
patch(s['LVWIDTH']-7,bytes([1])*2,bytes.fromhex('2005'))
retired=[[s['LVWIDTH']-5,s['LVWIDTH']],[0x6830,0x686D],[s['LCDDELAY'],s['LCDDELAY']+9],
         [s['PROMPT'],s['PROMPT']+2],
         [s['IOERROR'],s['IOERROR']+5],[0x58F2,0x58F5]]
assert old[s['LCDDELAY']-0x4000:s['LCDDELAY']-0x4000+9]==bytes.fromhex('3cce40000926fd3839')
assert old[s['PROMPT']-0x4000:s['PROMPT']-0x4000+2]==b'>\0'
io=s['IOERROR'];assert old[io-0x4000]==0xce and old[io-0x4000+3:io-0x4000+5]==bytes.fromhex('2003')
obsolete=int.from_bytes(old[io-0x4000+1:io-0x4000+3],'big')
msg=next(r for r in m['console_paper_allocations'] if r['origin']==obsolete and r['name'].startswith('error-'))
assert old[obsolete-0x4000:obsolete-0x4000+msg['bytes']]==b'?SERIAL ERROR\0'
retired.append([obsolete,obsolete+msg['bytes']])
for a,n in [(0x7BB4,5),(0x7D76,8),(0xA52D,7),(0xA769,7)]:
    assert old[a-0x4000:a-0x4000+n]==bytes([1])*n
    patch(a,bytes([1])*2,bytes([0x20,n-2]))
    retired.append([a+2,a+n])
# Same root inventory as the native reclamation audit, plus all .79 commands.
sys.path.insert(0,str(ROOT.parents[1]/'ROMReader/tools'))
from disassemble_hd6301 import make_disassembler,absolute_target,CONDITIONAL_BRANCHES
mem=bytes(0x4000)+bytes(cpu)+(ROOT.parents[1]/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin').read_bytes()
roots=[0xffe0,0x5000,0x4400,0x6829,0x6a9e,0x6f83,0x704d,0x716f,0x7154,0x728b,0x77ef,0xaeb2,0xc824,0xc896,0xcc5a,0xcdea,0xf4e0]
roots += [int.from_bytes(mem[a:a+2],'big') for a in range(0x7800,0x7822,2)]
roots += [r['handler'] for r in m['command_dispatch']]
roots += [s[k] for k in ['TRDISPATCH','FXDISPATCH','NFAPPLY','ARADDRESS','HFDECODE','KBDPOLL','KBDFAST','ERRORRESET']]
md=make_disassembler();todo=roots[:];seen=set();unresolved=[]
def inside(a):return any(lo<=a<hi for lo,hi in retired)
while todo:
    pc=todo.pop()
    if pc in seen or not 0x4000<=pc<65536:continue
    ins=next(md.disasm(mem[pc:pc+4],pc,1),None)
    if not ins or ins.mnemonic in ('fcb','illegal'):continue
    seen.add(pc);op,arg=ins.mnemonic,ins.op_str
    assert not any(inside(a) for a in range(pc,pc+ins.size)),hex(pc)
    vals=[int(x,16) for x in re.findall(r'\$([0-9a-fA-F]+)',arg)]
    if arg.startswith('#') and '$' not in arg:
        try:vals.append(int(arg[1:])&65535)
        except ValueError:pass
    assert not any(inside(v) for v in vals),(hex(pc),op,arg)
    if op in ('jsr','jmp','bsr','bra') or op in CONDITIONAL_BRANCHES:
        q=absolute_target(ins)
        if q is not None:todo.append(q)
        else:unresolved.append([pc,op,arg])
    if op=='swi':todo.append(0x704d)
    if op not in ('rts','rti','jmp','bra','swi','wai','slp'):todo.append(pc+ins.size)
print('Reclaim audit PASS',sum(b-a for a,b in retired),flush=True)
items=[dict(r) for r in m['font_allocations'] if re.fullmatch('font-glyph-[0-9a-f]{2}',r['name'])]
items += [dict(r) for r in m['console_paper_allocations'] if r['name'].startswith('error-') and r['origin']!=obsolete]
streams={r['name']:old[r['origin']-0x4000:r['origin']-0x4000+r['bytes']] for r in items}
free=[]
for a,b in sorted(m['explicit_free_regions']+retired+[[r['origin'],r['origin']+r['bytes']] for r in items if r['bytes']]):
    if free and a<=free[-1][1]:free[-1][1]=max(b,free[-1][1])
    else:free.append([a,b])
allowed+=free
for a,b in free:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
alloc=[]
def reserve(name,n):
    _,i=min((b-a,i) for i,(a,b) in enumerate(free) if b-a>=n)
    if name=='spacing-0':i=next(i for i,(a,b) in enumerate(free) if a==0x6830 and b-a>=n)
    a,b=free[i];free[i]=[a+n,b];alloc.append(dict(name=name,origin=a,bytes=n));return a
bodies=[(f'spacing-{i}',body) for i,body in enumerate(re.split(r'; @island \w+\n',(ROOT/'src/paper-spacing.asm').read_text()))]
local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b','\n'.join(b for _,b in bodies),re.M));ls=dict.fromkeys(local,0x4000)
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items() if k not in local)
parts=[]
for name,body in bodies:
    names=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    d=defs+''.join(f'{k} EQU ${v:04X}\n' for k,v in ls.items() if k not in names)
    raw,_=assemble(name,' OPT H01\n'+d+' ORG $1000\n'+body);a=reserve(name,len(raw))
    raw,l=assemble(name,' OPT H01\n'+d+f' ORG ${a:04X}\n'+body)
    ls.update({k:l[k] for k in names});parts.append((a,name,body))
for a,name,body in parts:
    names=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    d=defs+''.join(f'{k} EQU ${v:04X}\n' for k,v in ls.items() if k not in names)
    raw,_=assemble(name,' OPT H01\n'+d+f' ORG ${a:04X}\n'+body);cpu[a-0x4000:a-0x4000+len(raw)]=raw
key=reserve('LSPACING-key',9);cpu[key-0x4000:key-0x4000+9]=b'LSPACING\0'
table=reserve('LSPACING-table',8);cpu[table-0x4000:table-0x4000+8]=key.to_bytes(2,'big')+ls['SPENTRY'].to_bytes(2,'big')+bytes(4)
p=s['CMDTABLE'];visited=set()
while True:
    assert p not in visited;visited.add(p)
    k=int.from_bytes(old[p-0x4000:p-0x4000+2],'big');v=int.from_bytes(old[p-0x4000+2:p-0x4000+4],'big')
    if k:p+=4
    elif v:p=v
    else:break
patch(p+2,bytes(2),table.to_bytes(2,'big'))
patch(s['GPINIT'],b'\x7e'+s['MOTORBOOT'].to_bytes(2,'big'),b'\x7e'+ls['SPBOOT'].to_bytes(2,'big'))
for start,end in [(s['LLENTRY'],s['LLBAD']),(s['LLMOVE'],s['LLFAIL'])]:
    p=old.index(bytes.fromhex('86383d'),start-0x4000,end-0x4000)+0x4000
    patch(p,bytes.fromhex('86383d'),b'\xbd'+ls['SPMUL'].to_bytes(2,'big'))
p=old.index(bytes.fromhex('cc0038'),s['GPROW']-0x4000,s['GPENABLE']-0x4000)+0x4000
assert old[p-0x4000-3:p-0x4000]==bytes.fromhex('b7013e')
patch(p,bytes.fromhex('cc0038'),b'\xbd'+ls['SPFEED'].to_bytes(2,'big'))
p=old.index(bytes.fromhex('cc4000'),s['GPCALL']-0x4000,s['GPCALL']-0x4000+35)+0x4000
patch(p,bytes.fromhex('cc4000'),bytes.fromhex('cc8000'))
packing=[r[:] for r in free]
for seed in range(100):
    pending=[r for r in items if r['bytes']];random.Random(seed).shuffle(pending)
    free=[r[:] for r in packing];placed=[]
    for i in sorted(range(len(free)),key=lambda i:free[i][1]-free[i][0]):
        a,b=free[i];choices={0:[]}
        for j,r in enumerate(pending):
            for n,selected in sorted(list(choices.items()),reverse=True):
                nn=n+r['bytes']
                if nn<=b-a and nn not in choices:choices[nn]=selected+[j]
        selected=choices[max(choices)]
        for j in selected:
            r=pending[j];placed.append(dict(name=r['name'],origin=a,bytes=r['bytes']));a+=r['bytes']
        pending=[r for j,r in enumerate(pending) if j not in selected];free[i]=[a,b]
    if not pending:break
assert not pending, [(r['name'],r['bytes']) for r in pending]
placed += [r for r in items if not r['bytes']]
for r in placed:
    a=r['origin'];data=streams[r['name']]
    assert cpu[a-0x4000:a-0x4000+len(data)]==b'\xff'*len(data)
    cpu[a-0x4000:a-0x4000+len(data)]=data
    if r['name'].startswith('font-glyph-'):
        at=s['HFGLYPHS']+3*(int(r['name'][-2:],16)-32)
        patch(at,old[at-0x4000:at-0x4000+2],a.to_bytes(2,'big'))
    else:
        prev=next(x['origin'] for x in items if x['name']==r['name'])
        needle=b'\xce'+prev.to_bytes(2,'big')
        refs=[i+0x4000 for i in range(len(old)-2) if old[i:i+3]==needle]
        assert refs,r
        for at in refs:patch(at,needle,b'\xce'+a.to_bytes(2,'big'))

reloc={next(x['origin'] for x in items if x['name']==r['name']):r['origin'] for r in placed if r['name'].startswith('error-')}
s={k:reloc.get(v,v) for k,v in s.items()};s.update(ls)
p=old.index(b'Typestar BASIC 0.4.79-dev')+0x4000
patch(p,b'Typestar BASIC 0.4.79-dev',b'Typestar BASIC 0.4.80-dev')
assert all(x==y or any(a<=i+0x4000<b for a,b in allowed) for i,(x,y) in enumerate(zip(old,cpu)))
free=[r for r in free if r[0]<r[1]]
m.update(version='0.4.80-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='Awaiting tests',
 explicit_free_regions=free,explicit_free_bytes=sum(b-a for a,b in free),
 known_free_fragmented_bytes=m['known_free_fragmented_bytes']+sum(b-a for a,b in retired)-sum(r['bytes'] for r in alloc),
 spacing_allocations=alloc,spacing_reclaimed=retired,spacing_patches=patches,native_stage_tick_limit=32768,
 text_spacing=dict(default=1.5,values=[1,1.5,2],pitches=[56,84,112],ram=ls['LSPITCH']))
m['font_allocations']=[r for r in m['font_allocations'] if not r['name'].startswith('font-glyph-')]+[r for r in placed if r['name'].startswith('font-glyph-')]
m['console_paper_allocations']=[r for r in m['console_paper_allocations'] if not r['name'].startswith('error-')]+[r for r in placed if r['name'].startswith('error-')]
m['statement_modules']+=alloc;m['command_dispatch'].append(dict(name='LSPACING',key=key,handler=ls['SPENTRY']))
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s,indent=2));(out/'manifest.json').write_text(json.dumps(m,indent=2))
(out/'font-expected.json').write_bytes((base/'font-expected.json').read_bytes())
(out/'spacing-reclaim-audit.json').write_text(json.dumps(dict(result='PASS',base_sha256=hashlib.sha256(old).hexdigest(),regions=retired,roots=roots,unresolved=unresolved),indent=2))
print('Added',sum(r['bytes'] for r in alloc),'free',m['explicit_free_bytes'],m['sha256'])
