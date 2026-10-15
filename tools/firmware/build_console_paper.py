""".78: line errors, safe Backspace, no HELP, POINT and text-grid LLOCATE.

Pin the validated input image. Repack unchanged font streams only in their
documented allocations and verified reclaimed BASIC bodies. No native boot,
SCI or motor phase tables are removed. No hardware is flashed by this tool.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re,random
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/paper-reverse';out=ROOT/'build/console-paper';out.mkdir(exist_ok=True)
old=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
assert hashlib.sha256(old).hexdigest()==m['sha256'] and m['version']=='0.4.77-dev'
cpu=bytearray(old);allowed=[];patches=[]
def patch(a,expected,new):
    assert len(expected)==len(new)
    assert cpu[a-0x4000:a-0x4000+len(expected)]==expected,(hex(a),expected.hex())
    cpu[a-0x4000:a-0x4000+len(new)]=new
    allowed.append([a,a+len(new)]);patches.append(dict(address=a,old=expected.hex(),new=new.hex()))
help_row=next(r for r in m['command_dispatch'] if r['name']=='HELP')
assert old[help_row['handler']-0x4000:help_row['handler']-0x4000+9]==b'\xbd'+s['EOS'].to_bytes(2,'big')+b'\xce'+s['HELPMSG'].to_bytes(2,'big')+b'\x7e'+s['PUTS'].to_bytes(2,'big')
help_text=old[s['HELPMSG']-0x4000:].split(b'\0')[0]+b'\0'
assert help_text==b'LIST RUN NEW LOAD SAVE MEM\0'
# Both known OUTNUM callers emit nonnegative RAM sizes. The new line reporter
# also needs unsigned output. Keep the ABI address and replace the whole body.
refs=[i+0x4000-1 for i in range(len(old)-1) if old[i:i+2]==s['OUTNUM'].to_bytes(2,'big')]
assert refs==[0x5022,0xa56f],refs
assert old[s['OUTNUM']-0x4000+76]==0x39
# Backspace must not infer physical Shift from the shared uppercase wire.
# Restore the original four-byte editor branch. Retire only the private .38
# modifier helper; no other call targets it.
assert old[0x9dcb-0x4000:0x9dcf-0x4000]==bytes.fromhex('81082625')
patch(s['EDNOTRIGHT'],bytes.fromhex('7e9dcb01'),bytes([0x81,8,0x26,(s['EDPRINTABLE']-(s['EDNOTRIGHT']+4))&255]))
retired=[[help_row['handler'],help_row['handler']+9],[s['KHELP'],s['KHELP']+5],
         [s['HELPMSG'],s['HELPMSG']+len(help_text)],
         [s['OUTNUM']+3,s['OUTNUM']+77],[0x9dcb,0x9dfa]]
# Error displays now stop before CR/LF. Pool those strings without their
# obsolete line endings and share identical messages; patch verified LDX # refs.
error_strings={}
for name,a in s.items():
    if not 0x4000<=a<0xc000 or old[a-0x4000:a-0x4000+1]!=b'?':continue
    value=old[a-0x4000:].split(b'\0')[0]
    if value.endswith(b'\r\n') and all(32<=v<127 for v in value[:-2]):
        error_strings[a]=value
for a,value in error_strings.items():retired.append([a,a+len(value)+1])
retired.append([s['GRAPHICS_SCAN'],s['GRAPHICS_KEY_END']])
oldpoint=next(r for r in m['command_dispatch'] if r['name']=='PSET')['key']
retired.append([oldpoint,oldpoint+5])
# The old flat keyboard decoder is bypassed by the validated delta decoder.
# Its only apparent interior address occurrence is native opcodes B96A-B96C,
# not a pointer (F6 1EAB / 5C / 3A). No executable entry targets this tail.
a=s['KBDCHAR']+7;b=s['KBDNONE']
assert old[a-0x4000:b-0x4000]==bytes.fromhex('58ce5c8b3aee00f6199a3a963285802703c62c3a7d199f2703c6583aa6002001')
retired.append([a,b])
glyphs=[r for r in m['font_allocations'] if re.fullmatch(r'font-glyph-[0-9a-f]{2}',r['name'])]
streams={r['name']:old[r['origin']-0x4000:r['origin']-0x4000+r['bytes']] for r in glyphs}
free=[]
for a,b in sorted(m['explicit_free_regions']+retired+[[r['origin'],r['origin']+r['bytes']] for r in glyphs if r['bytes']]):
    if free and a<=free[-1][1]:free[-1][1]=max(b,free[-1][1])
    else:free.append([a,b])
allowed+=free
for a,b in free:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
alloc=[]
def reserve(name,n):
    options=[(b-a,i) for i,(a,b) in enumerate(free) if b-a>=n]
    assert options,(name,n)
    _,i=min(options);a,b=free[i];free[i]=[a+n,b]
    alloc.append(dict(name=name,origin=a,bytes=n));return a
def put(a,data):
    assert cpu[a-0x4000:a-0x4000+len(data)]==b'\xff'*len(data),(hex(a),len(data))
    cpu[a-0x4000:a-0x4000+len(data)]=data
# PMMOVE+21 starts its common validity/resource checks. We skip only its
# stored-target/manual-range prefix, after independently bounding the grid.
s['LLPMCHECK']=s['PMMOVE']+21
assert old[s['LLPMCHECK']-0x4000:s['LLPMCHECK']-0x4000+3]==b'\xb6'+s['PMVALID'].to_bytes(2,'big')
bodies=[]
for name in ['paper-text-locate','basic-error-line','console-chords','console-busy']:
    for i,body in enumerate(re.split(r'; @island \w+\n',(ROOT/f'src/{name}.asm').read_text())):
        bodies.append((f'{name}-{i}',body))
local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b','\n'.join(b for _,b in bodies),re.M));ls=dict.fromkeys(local,0x4000)
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items() if k not in local)
parts=[]
for name,body in bodies:
    names=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    d=defs+''.join(f'{k} EQU ${v:04X}\n' for k,v in ls.items() if k not in names)
    raw,_=assemble(name,' OPT H01\n'+d+' ORG $1000\n'+body)
    a=reserve(name,len(raw));raw,l=assemble(name,' OPT H01\n'+d+f' ORG ${a:04X}\n'+body)
    ls.update({k:l[k] for k in names});parts.append((a,name,body))
for a,name,body in parts:
    names=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    d=defs+''.join(f'{k} EQU ${v:04X}\n' for k,v in ls.items() if k not in names)
    raw,_=assemble(name,' OPT H01\n'+d+f' ORG ${a:04X}\n'+body);put(a,raw)
# Relink pooled error strings, whose executable references are LDX immediates.
error_locations={};error_refs={}
for a,value in error_strings.items():
    value=value[:-2]+b'\0'
    name='error-'+value.decode().strip('\0')
    if name not in streams:
        streams[name]=value;glyphs.append(dict(name=name,origin=0,bytes=len(value)))
    needle=b'\xce'+a.to_bytes(2,'big')
    refs=[i+0x4000 for i in range(len(old)-2) if old[i:i+3]==needle]
    assert refs,(hex(a),value)
    error_refs[a]=(name,refs)
patch(s['KBDREAD'],b'\xbd'+s['GRAPHICS_SCAN'].to_bytes(2,'big'),b'\xbd'+ls['CXSCAN'].to_bytes(2,'big'))
patch(s['KBDCHAR'],b'\x7e'+s['GRAPHICS_KEYCHAR'].to_bytes(2,'big'),b'\x7e'+ls['CXCHAR'].to_bytes(2,'big'))
patch(s['EDNOTRIGHT'],bytes([0x81,8,0x26,(s['EDPRINTABLE']-(s['EDNOTRIGHT']+4))&255]),b'\x7e'+ls['CXDELETE'].to_bytes(2,'big')+b'\x01')
# Swap the retained-document check and LCD attachment, preserving native boot.
patch(0x5004,bytes.fromhex('bd4403bd5a7d'),bytes.fromhex('bd5a7dbd')+ls['CXBOOT'].to_bytes(2,'big'))
patch(s['LOAD']+6,b'\xbd'+s['SERIALINIT'].to_bytes(2,'big'),b'\xbd'+ls['CXLOAD'].to_bytes(2,'big'))
# 64 text rows require up to 14112 native timer stages; retain a finite bound.
a=s['GPCALL'];needle=bytes.fromhex('cc2000');off=old.index(needle,a-0x4000,a-0x4000+35)+0x4000
patch(off,needle,bytes.fromhex('cc4000'))
keys={}
for name in ('LLOCATE','POINT'):
    keys[name]=reserve(name+'-keyword',len(name)+1);put(keys[name],name.encode()+b'\0')
# Reuse HELP's table entry; POINT replaces PSET without an alias or token change.
for name,newname in [('HELP','LLOCATE'),('PSET','POINT')]:
    row=next(r for r in m['command_dispatch'] if r['name']==name)
    needle=row['key'].to_bytes(2,'big')+row['handler'].to_bytes(2,'big')
    assert old.count(needle)==1
    a=old.index(needle)+0x4000
    handler=ls['LLENTRY'] if name=='HELP' else row['handler']
    patch(a,needle,keys[newname].to_bytes(2,'big')+handler.to_bytes(2,'big'))
    row.update(name=newname,key=keys[newname],handler=handler)
patch(s['OUTNUM'],old[s['OUTNUM']-0x4000:s['OUTNUM']-0x4000+3],b'\x7e'+ls['ERUNSIGNED'].to_bytes(2,'big'))
a=s['ERRORWAIT']+20
assert old[a-0x4000:a-0x4000+3]==b'\xbd'+s['PUTS'].to_bytes(2,'big')
patch(a,b'\xbd'+s['PUTS'].to_bytes(2,'big'),b'\xbd'+ls['ERLINE'].to_bytes(2,'big'))
# Retain RUNNING until unfinished FOR/GOSUB diagnostics have been emitted.
a=s['RRFINISH'];oldfinish=old[a-0x4000:a-0x4000+20]
assert oldfinish[:3]==b'\x7f'+s['RUNNING'].to_bytes(2,'big') and oldfinish[-1]==0x39
patch(a,oldfinish,oldfinish[3:-1]+oldfinish[:3]+b'\x39')
a=s['LVWIDTH']-10
assert old[a-0x4000:a-0x4000+10]==b'\xb6'+s['PMVALID'].to_bytes(2,'big')+bytes.fromhex('81032703')+b'\x7f'+s['LPCOLUMN'].to_bytes(2,'big')
patch(a,old[a-0x4000:a-0x4000+10],b'\xbd'+ls['LLINIT'].to_bytes(2,'big')+b'\x01'*7)
patch(s['LPCLEARED'],b'\x7f'+s['LPCOLUMN'].to_bytes(2,'big')+b'\x39',b'\x7e'+ls['LLNEWLINE'].to_bytes(2,'big')+b'\x01')
print("Packing capacity",sum(b-a for a,b in free),"glyphs",sum(r["bytes"] for r in glyphs),"alloc",sum(r["bytes"] for r in alloc),flush=True)
packing=[r[:] for r in free]
for seed in range(300):
    pending=[r for r in glyphs if r['bytes']];random.Random(seed).shuffle(pending)
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
assert not pending,[(r['name'],r['bytes']) for r in pending]
placed += [r for r in glyphs if not r['bytes']]
for r in placed:
    put(r['origin'],streams[r['name']])
    if r['name'].startswith('font-glyph-'):
        p=s['HFGLYPHS']+3*(int(r['name'][-2:],16)-32)
        patch(p,old[p-0x4000:p-0x4000+2],r['origin'].to_bytes(2,'big'))
    else:
        alloc.append(r)
        for oldaddr,(name,refs) in error_refs.items():
            if name!=r['name']:continue
            for ref in refs:patch(ref,b'\xce'+oldaddr.to_bytes(2,'big'),b'\xce'+r['origin'].to_bytes(2,'big'))
            for k,v in list(s.items()):
                if v==oldaddr:s[k]=r['origin']
p=old.index(b'Typestar BASIC 0.4.77-dev')+0x4000
patch(p,b'Typestar BASIC 0.4.77-dev',b'Typestar BASIC 0.4.78-dev')
assert all(x==y or any(a<=i+0x4000<b for a,b in allowed) for i,(x,y) in enumerate(zip(old,cpu)))
free=[r for r in free if r[0]<r[1]]
used=sum(r['bytes'] for r in alloc);recovered=sum(b-a for a,b in retired)
m.update(version='0.4.78-dev',sha256=hashlib.sha256(cpu).hexdigest(),
    status='Console fixes and LLOCATE candidate; awaiting tests',console_paper_allocations=alloc,
    console_paper_patches=patches,console_paper_reclaimed=retired,
    font_allocations=[r for r in m['font_allocations'] if r not in glyphs]+[r for r in placed if r['name'].startswith('font-glyph-')],
    explicit_free_regions=free,explicit_free_bytes=sum(b-a for a,b in free),
    known_free_fragmented_bytes=m['known_free_fragmented_bytes']+recovered-used,
    native_stage_tick_limit=16384,
    text_grid=dict(rows=64,columns=72,head_pitch=16,paper_pitch=56,row_state=ls['LLROW']),
    keyboard_clear_shortcut='CODE+Backspace; CODE+Left/Right insert </>')
m['statement_modules']+=alloc
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|ls,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
(out/'font-expected.json').write_bytes((base/'font-expected.json').read_bytes())
print('Code/data',used,'recovered',recovered,'free',m['explicit_free_bytes'],m['sha256'])
