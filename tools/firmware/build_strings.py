"""First string runtime: bounded views, lazy objects and existing decimal IO."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re,sys
from validate_array_tokens import ROOT,assemble
sys.path.insert(0,str(ROOT.parents[1]/'ROMReader/tools'))
from disassemble_hd6301 import make_disassembler,absolute_target,CONDITIONAL_BRANCHES
base=ROOT/'build/data';out=ROOT/'build/strings';out.mkdir(exist_ok=True)
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();cpu=bytearray(original)
assert hashlib.sha256(original).hexdigest()=='a5f783459d178fee5b36f450b9cae102a64b0458ac84b516ea59fd99ff596459'
# Retired Canon ONLINE text translation, RX queue/ISR, and editor operations.
# Keep B990..B99B (reset), BB4A..BB56 and BD4B..BD67 helper entry points.
# BASIC uses its own polled SCI with SEI; the native SCI ISR is never enabled.
retired=[[0xb99c,0xbb4a],[0xbb57,0xbd4b],[0xbd68,0xbedd],
         [0x9280,0x92f0],[0x9377,0x93ee],[0x955f,0x95c6],[0xada7,0xaeab]]
mem=bytes(0x4000)+original+(ROOT.parents[1]/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin').read_bytes()
roots=[0xffe0,0x5000,0x4400,0x6829,0x6a9e,0x6f83,0x704d,0x716f,0x7154,
       0x728b,0x77ef,0xaeb2,0xc824,0xc896,0xcc5a,0xcdea,0xf4e0]
roots += [int.from_bytes(mem[a:a+2],'big') for a in range(0x7800,0x7822,2)]
roots += [r['handler'] for r in m['command_dispatch']]
roots += [s[k] for k in ['TRDISPATCH','FXDISPATCH','NFAPPLY','ARADDRESS','HFDECODE','KBDPOLL','KBDFAST']]
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
free=[]
for a,b in sorted(m['explicit_free_regions']+retired):
    if free and a<=free[-1][1]:free[-1][1]=max(b,free[-1][1])
    else:free.append([a,b])
for a,b in retired:cpu[a-0x4000:b-0x4000]=bytes([255])*(b-a)
extra=dict(DIMJOB=0x1cde,STMODE=0x1957,STLEN=0x1958,STFIRST=0x1959,STLHS=0x195a,STDEST=0x195b,STCHAR=0x195d,
           STDEPTH=0x195e,STARG=0x195f,STCOUNT=0x1961,STRESULTPTR=0x1963,STRESULTLEN=0x1965,
           STRIGHTLEN=0x1966,STLEFTLEN=0x1967,STLEFTPTR=0x1968,STRIGHTPTR=0x196a,STDATA=0x196c,
           STOLDLET=int.from_bytes(original[0x6007:0x6009],'big'))
# Locate the live INPUT variable parser by its unique VARADDR/IVAR sequence.
needle=b'\xbd'+s['VARADDR'].to_bytes(2,'big')+b'\xf7'+s['IVAR'].to_bytes(2,'big')
assert original[0x6700:0x67c5].count(needle)==1
extra['STOLDINPUT']=0xa700+original[0x6700:0x67c5].index(needle)
names=['string-syntax','string-view','string-core','string-statements','string-numeric','string-input',
       'string-subkind','string-substring','string-scratch','string-value','string-condition',
       'string-control','string-data']
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
def jump(a,target):
    i=a-0x4000;old=cpu[i:i+3];new=b'\x7e'+target.to_bytes(2,'big')
    cpu[i:i+3]=new;patches.append(dict(address=a,old=old.hex(),new=new.hex()))
for a,k in [(0xa006,'STLET'),(s['PRINTITEM'],'STPRINT'),(s['LVITEM'],'STLPRINT'),
            (s['NFENTRY'],'STNUMENTRY'),(extra['STOLDINPUT'],'STINPUT'),(s['CMDENTRY'],'STCOMMAND'),
            (s['DCONDITION'],'STCONDITION'),(s['THENEQUAL'],'STTHEN'),
            (s['DAREAD'],'STREAD'),(s['DAVALUE'],'STDAVALUE')]:jump(a,linked[k])
old=b'Typestar BASIC 0.4.72-dev';assert cpu.count(old)==1
a=cpu.index(old);cpu[a:a+len(old)]=b'Typestar BASIC 0.4.73-dev'
allowed=retired+[[r['origin'],r['origin']+r['bytes']] for r in alloc]+[[p['address'],p['address']+3] for p in patches]+[[a+0x4000,a+0x4000+len(old)]]
assert all(x==y or any(lo<=i+0x4000<hi for lo,hi in allowed) for i,(x,y) in enumerate(zip(original,cpu)))
used=sum(r['bytes'] for r in alloc);recovered=sum(b-a for a,b in retired)
m.update(version='0.4.73-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='String runtime CPU candidate',
    string_allocations=alloc,string_reclaimed=retired,string_patches=patches,string_bytes=used,
    known_free_fragmented_bytes=m['known_free_fragmented_bytes']+recovered-used,
    explicit_free_regions=[r for r in free if r[0]<r[1]],explicit_free_bytes=sum(b-a for a,b in free))
m['statement_modules']+=alloc
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|extra|linked,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
(out/'reclaim-audit.json').write_text(json.dumps(dict(result='PASS',base_sha256=hashlib.sha256(original).hexdigest(),
    regions=retired,bytes=recovered,roots=roots,instructions=len(seen),unresolved=unresolved,
    limitation='Direct control/data references; native IRQ-driven ONLINE editor intentionally unsupported'),indent=2))
print('String code',used,'reclaimed',recovered,'free',m['known_free_fragmented_bytes'])
