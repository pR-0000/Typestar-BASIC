""".79: finish reverse paper positioning forward; reset LCD on errors.

The motor-distance model is unchanged. The extra 32-unit reverse/forward
approach uses the magnitude of Canon's own reverse-paper preparation, but
its suitability for physical LLOCATE alignment still requires a machine test.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re,random
from validate_array_tokens import ROOT,assemble
base=ROOT/'build/console-paper';out=ROOT/'build/paper-alignment';out.mkdir(exist_ok=True)
old=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
assert hashlib.sha256(old).hexdigest()=='191f3f04e59f9193c75f385bd414ff4e2834dd121348222bb80a811b9dc79c71'
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
cpu=bytearray(old);allowed=[];patches=[]
def patch(a,expected,new):
    assert len(expected)==len(new) and cpu[a-0x4000:a-0x4000+len(expected)]==expected,hex(a)
    cpu[a-0x4000:a-0x4000+len(new)]=new;allowed.append([a,a+len(new)])
    patches.append(dict(address=a,old=expected.hex(),new=new.hex()))
# -(signed delta) + 32: reverse past the target, then approach forward.
patch(s['PRPREP']+10,bytes.fromhex('c30001'),bytes.fromhex('c30021'))
p=int.from_bytes(old[0x324b:0x324d],'big')
assert old[p-0x4000:p-0x4000+23]==bytes.fromhex('b61b5b8102270d8680b718f7cc0020ddb87e71547e7257')
# PMVALID=2 skips only Canon's glyph latch, not the 32-unit forward return.
patch(p+5,bytes.fromhex('270d'),bytes.fromhex('2705'))
retired=[[p+20,p+23]] # unreachable former PRDIRECT JMP $7257
# CLS duplicates UICLEAR's exact 32-cell shadow loop. Call the shared helper
# then keep its existing redraw/lower-bank cleanup, freeing 16 contiguous bytes.
a=s['CLS']+3
assert old[a-0x4000:a-0x4000+25]==bytes.fromhex('7f19ca7f1996ce19a08620a700088c19c026f8bd5b327e480c')
patch(a,old[a-0x4000:a-0x4000+9],b'\xbd'+s['UICLEAR'].to_bytes(2,'big')+b'\xbd'+s['LCDREDRAW'].to_bytes(2,'big')+bytes.fromhex('7e480c'))
retired.append([a+9,a+25])

items=[dict(r) for r in m['font_allocations'] if re.fullmatch('font-glyph-[0-9a-f]{2}',r['name'])]
items += [dict(r) for r in m['console_paper_allocations'] if r['name'].startswith('error-')]
streams={r['name']:old[r['origin']-0x4000:r['origin']-0x4000+r['bytes']] for r in items}
free=[]
for a,b in sorted(m['explicit_free_regions']+retired+[[r['origin'],r['origin']+r['bytes']] for r in items if r['bytes']]):
    if free and a<=free[-1][1]:free[-1][1]=max(b,free[-1][1])
    else:free.append([a,b])
allowed+=free
for a,b in free:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())
body=(ROOT/'src/console-error-reset.asm').read_text()
code,_=assemble('error-reset-size',' OPT H01\n'+defs+' ORG $1000\n'+body)
_,i=min((b-a,i) for i,(a,b) in enumerate(free) if b-a>=len(code));a,b=free[i]
code,labels=assemble('error-reset',' OPT H01\n'+defs+f' ORG ${a:04X}\n'+body)
cpu[a-0x4000:a-0x4000+len(code)]=code;free[i]=[a+len(code),b]
allocation=dict(name='error-reset',origin=a,bytes=len(code));s['ERRORRESET']=a
# Include the custom UART error screens, which bypass ERRORWAIT.
for start,end in [(s['ERRORWAIT'],s['ERRORKEY']),(s['SRXTIMEOUT'],s['SRXSTATUS']),(s['SRXSTATUS'],s['STXMSG'])]:
    needle=b'\xbd'+s['UICLEAR'].to_bytes(2,'big')
    refs=[i+0x4000 for i in range(start-0x4000,end-0x4000) if old[i:i+3]==needle]
    assert len(refs)==1,(hex(start),refs)
    patch(refs[0],needle,b'\xbd'+a.to_bytes(2,'big'))
packing=[r[:] for r in free]
for seed in range(300):
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
assert not pending,[(r['name'],r['bytes']) for r in pending]
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
# Update all error labels simultaneously; new addresses may equal old ones.
reloc={next(x['origin'] for x in items if x['name']==r['name']):r['origin'] for r in placed if r['name'].startswith('error-')}
s={k:reloc.get(v,v) for k,v in s.items()}
s['ERRORRESET']=allocation['origin']
a=old.index(b'Typestar BASIC 0.4.78-dev')+0x4000
patch(a,b'Typestar BASIC 0.4.78-dev',b'Typestar BASIC 0.4.79-dev')
assert all(x==y or any(a<=i+0x4000<b for a,b in allowed) for i,(x,y) in enumerate(zip(old,cpu)))
free=[r for r in free if r[0]<r[1]]
m.update(version='0.4.79-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='Awaiting CPU and physical alignment tests',
    explicit_free_regions=free,explicit_free_bytes=sum(b-a for a,b in free),
    known_free_fragmented_bytes=m['known_free_fragmented_bytes']+19-len(code),
    paper_alignment_patches=patches,paper_alignment_reclaimed=retired,
    paper_reverse_approach_units=32,error_reset_allocation=allocation)
m['font_allocations']=[r for r in m['font_allocations'] if not r['name'].startswith('font-glyph-')]+[r for r in placed if r['name'].startswith('font-glyph-')]
m['console_paper_allocations']=[r for r in m['console_paper_allocations'] if not r['name'].startswith('error-')]+[r for r in placed if r['name'].startswith('error-')]
m['statement_modules'].append(allocation)
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
(out/'font-expected.json').write_bytes((base/'font-expected.json').read_bytes())
print('Free',m['explicit_free_bytes'],m['sha256'])
