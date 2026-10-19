"""Build .91 from .89: forward compensation after normal paper positioning.

Preserve the complete native reverse/forward approach. Repack compressed font
records and keyword spellings, checking their final consumers. Exact shared
stream bytes save eight bytes; decoded glyphs and dictionary text are unchanged.
"""
from pathlib import Path
import hashlib
import json
import random
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BASE_SHA='597b72267738f65a4abb01c9728d9f67410d16edb72fc0a8edd575f1be51dd26'


def main():
    base=ROOT/'release/s70-basic-0.4.89-dev-canon-start-nh7.bin'
    raw=base.read_bytes();old=raw[16384:]+raw[:16384]
    assert len(old)==32768 and hashlib.sha256(old).hexdigest()==BASE_SHA
    m=json.loads(base.with_name(base.stem+'-manifest.json').read_text())
    s=json.loads((ROOT/'studio/internal/profiles/basic-0.4.89-symbols.json').read_text())
    out=ROOT/'build/paper-y-poststep';out.mkdir(exist_ok=True)
    cpu=bytearray(old);allowed=[];patches=[]

    def patch(a,expected,value):
        assert len(expected)==len(value)
        assert bytes(cpu[a-0x4000:a-0x4000+len(value)])==expected,hex(a)
        cpu[a-0x4000:a-0x4000+len(value)]=value
        allowed.append([a,a+len(value)])
        patches.append(dict(address=a,old=expected.hex(),new=value.hex()))

    glyphs=[dict(v) for v in m['font_allocations'] if re.fullmatch('font-glyph-[0-9a-f]{2}',v['name'])]
    assert len(glyphs)==95
    words=[dict(v) for v in m['native_allocations'] if v['name'].startswith('native-word-') and v['bytes']]
    assert len(words)==22
    assert old[s['KTO']-0x4000:s['KTO']-0x4000+3]==b'TO\0'
    words.append(dict(name='native-TO',origin=s['KTO'],bytes=3))
    records=glyphs+words
    streams={v['name']:old[v['origin']-0x4000:v['origin']-0x4000+v['bytes']] for v in records}
    for v in glyphs:
        p=s['HFGLYPHS']+3*(int(v['name'][-2:],16)-32)
        assert int.from_bytes(old[p-0x4000:p-0x4000+2],'big')==v['origin']
        assert old[p-0x4000+2]==v['bytes']
    free=[]
    for a,b in sorted(m['explicit_free_regions']+[[v['origin'],v['origin']+v['bytes']] for v in records if v['bytes']]):
        if free and a<=free[-1][1]:free[-1][1]=max(b,free[-1][1])
        else:free.append([a,b])
    allowed+=free
    for a,b in free:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)

    def consume(a,z):
        i=next(i for i,(lo,hi) in enumerate(free) if lo<=a<z<=hi)
        lo,hi=free.pop(i)
        if lo<a:free.append([lo,a])
        if z<hi:free.append([z,hi])

    # The boot helper gains one byte from its already audited following hole.
    boot=s['SPBOOT'];consume(boot+8,boot+9)
    post=0x1000  # size-only assembly; the exact packer chooses its ROM slot
    links=dict(s,YPACC=0x1B8D,YPPOST=post,YPBOOT=boot,YPGAIN=96)
    bodies=re.split(r'; @island \w+\n',(ROOT/'src/paper-y-poststep.asm').read_text())
    assert len(bodies)==2
    assembler=ROOT.parent.parent/'ROMReader/tmp/m680x-tools/a09.exe'
    allocations=[]
    for name,body,address,size in [('post',bodies[0],post,39),('boot',bodies[1],boot,9)]:
        names=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
        defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in links.items() if k not in names)
        source=out/(name+'.asm');binary=source.with_suffix('.bin');listing=source.with_suffix('.lst')
        source.write_text(' OPT H01\n'+defs+f' ORG ${address:04X}\n'+body,encoding='ascii')
        run=subprocess.run([str(assembler),'-W','-B'+str(binary),'-L'+str(listing),str(source)],capture_output=True,text=True)
        assert run.returncode==0,run.stdout+run.stderr
        code=binary.read_bytes();assert len(code)==size,(name,len(code))
        table=listing.read_text().split('SYMBOL TABLE')[1]
        labels={k:int(v,16) for k,v in re.findall(r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',table)}
        links.update({k:labels[k] for k in names})
        if name!='post':patch(address,bytes(cpu[address-0x4000:address-0x4000+size]),code)
        allocations.append(dict(name='paper-y-'+name,origin=address,bytes=size))
    assert old[s['PMFEED']-0x4000:s['PMFEED']-0x4000+10]==(
        b'\xfc'+s['PMTY'].to_bytes(2,'big')+b'\xb3'+s['PMY'].to_bytes(2,'big')+
        bytes((0x27,s['PMCOMMIT']-s['PMFEED']-8,0xDD,0xB8)))

    # Share exact suffix/prefix bytes and contained streams. Each original
    # record still reads precisely the same byte sequence at its own pointer.
    groups=[dict(name=v['name'],data=streams[v['name']],members={v['name']:0})
            for v in records if v['bytes']]
    original_bytes=sum(len(v['data']) for v in groups)
    while True:
        best=(0,None,None,0)
        for i,a in enumerate(groups):
            if any(name.startswith('native-') for name in a['members']):continue
            for j,b in enumerate(groups):
                if i==j:continue
                if any(name.startswith('native-') for name in b['members']):continue
                offset=a['data'].find(b['data'])
                if offset>=0:
                    score=len(b['data'])
                else:
                    score=next((n for n in range(min(len(a['data']),len(b['data'])),0,-1)
                                if a['data'][-n:]==b['data'][:n]),0)
                    offset=len(a['data'])-score
                if score>best[0]:best=(score,i,j,offset)
        score,i,j,offset=best
        if not score:break
        a,b=groups[i],groups[j]
        data=a['data']+b['data'][max(0,len(a['data'])-offset):]
        members=a['members']|{name:pos+offset for name,pos in b['members'].items()}
        groups=[v for k,v in enumerate(groups) if k not in (i,j)]+[dict(name=a['name'],data=data,members=members)]
    saved=original_bytes-sum(len(v['data']) for v in groups)
    print('Shared exact data bytes:',saved,flush=True)
    groups.append(dict(name='__post',data=bytes(39),members={}))
    packing=[v[:] for v in free]
    for seed in range(20):
        pending=list(groups);random.Random(seed).shuffle(pending)
        free=[v[:] for v in packing];placed_groups=[]
        for i in sorted(range(len(free)),key=lambda i:free[i][1]-free[i][0]):
            a,b=free[i];choices={0:[]}
            for j,v in enumerate(pending):
                for n,items in sorted(list(choices.items()),reverse=True):
                    nn=n+len(v['data'])
                    if nn<=b-a and nn not in choices:choices[nn]=items+[j]
            chosen=choices[max(choices)]
            for j in chosen:
                v=pending[j];placed_groups.append(dict(v,origin=a));a+=len(v['data'])
            pending=[v for j,v in enumerate(pending) if j not in chosen];free[i]=[a,b]
        if not pending:break
    assert not pending,[(v['name'],len(v['data'])) for v in pending]
    positions={}
    for v in placed_groups:
        a=v['origin'];data=v['data']
        assert cpu[a-0x4000:a-0x4000+len(data)]==b'\xff'*len(data)
        cpu[a-0x4000:a-0x4000+len(data)]=data
        positions.update({name:a+offset for name,offset in v['members'].items()})
        if v['name']=='__post':post=a
    assert 0x4000<=post<0xC000
    links['YPPOST']=post
    names=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',bodies[0],re.M))
    defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in links.items() if k not in names)
    source=out/'post.asm';source.write_text(' OPT H01\n'+defs+f' ORG ${post:04X}\n'+bodies[0],encoding='ascii')
    run=subprocess.run([str(assembler),'-W','-B'+str(source.with_suffix('.bin')),
        '-L'+str(source.with_suffix('.lst')),str(source)],capture_output=True,text=True)
    assert run.returncode==0,run.stdout+run.stderr
    code=source.with_suffix('.bin').read_bytes();assert len(code)==39
    labels={k:int(v,16) for k,v in re.findall(r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',source.with_suffix('.lst').read_text().split('SYMBOL TABLE')[1])}
    links.update({k:labels[k] for k in names})
    allocations[0]['origin']=post
    patch(post,bytes(39),code)
    patch(s['PMCOMMIT'],b'\xfc'+s['PMTX'].to_bytes(2,'big'),b'\x7e'+post.to_bytes(2,'big'))
    placed=[dict(v,origin=positions.get(v['name'],v['origin'])) for v in records]
    for v in placed:
        assert cpu[v['origin']-0x4000:v['origin']-0x4000+v['bytes']]==streams[v['name']]
    for v in placed[:95]:
        p=s['HFGLYPHS']+3*(int(v['name'][-2:],16)-32)
        patch(p,old[p-0x4000:p-0x4000+2],v['origin'].to_bytes(2,'big'))
    reloc={v['origin']:positions[v['name']] for v in words}
    # LIST shares the suffix of LLIST; retain that alias after moving LLIST.
    alias=next(v for v in m['native_allocations'] if v['name']=='native-word-4')
    parent=next(v for v in words if v['name']=='native-word-10')
    assert alias['bytes']==0 and alias['origin']==parent['origin']+1
    reloc[alias['origin']]=reloc[parent['origin']]+1
    pointer_sites=set(s['TOKENPTRS']+2*i for i in range(37))
    p=s['CMDTABLE'];seen=set()
    while p:
        assert p not in seen;seen.add(p)
        key=int.from_bytes(old[p-0x4000:p-0x4000+2],'big')
        handler=int.from_bytes(old[p-0x4000+2:p-0x4000+4],'big')
        if not key:p=handler;continue
        pointer_sites.add(p);p+=4
    direct=[]
    for target in reloc:
        needle=b'\xce'+target.to_bytes(2,'big')
        for i in range(len(old)-2):
            if old[i:i+3]==needle:
                assert not any(v['origin']<=i+0x4000<v['origin']+v['bytes'] for v in records)
                pointer_sites.add(i+0x4001);direct.append(i+0x4000)
    assert sorted(direct)==[0x4AC4,0x5491,0x58A4,0x9D26],direct
    for p in sorted(pointer_sites):
        target=int.from_bytes(old[p-0x4000:p-0x4000+2],'big')
        if target in reloc:patch(p,old[p-0x4000:p-0x4000+2],reloc[target].to_bytes(2,'big'))
    for v in m['command_dispatch']:v['key']=reloc.get(v['key'],v['key'])
    for v in m['native_allocations']:
        if v['origin'] in reloc:v['origin']=reloc[v['origin']]
    m['native_allocations'].append(next(v for v in placed if v['name']=='native-TO'))
    banner=b'Typestar BASIC 0.4.89-dev';assert old.count(banner)==1
    patch(old.index(banner)+0x4000,banner,b'Typestar BASIC 0.4.91-dev')
    assert all(x==y or any(a<=i+0x4000<b for a,b in allowed) for i,(x,y) in enumerate(zip(old,cpu)))
    assert cpu[s['PRPREP']-0x4000:s['PRFEED']-0x4000]==old[s['PRPREP']-0x4000:s['PRFEED']-0x4000]
    free=sorted([v for v in free if v[0]<v[1]])
    available=sum(b-a for a,b in free)
    assert available==62+saved
    for a,b in free:assert cpu[a-0x4000:b-0x4000]==b'\xff'*(b-a)
    m['font_allocations']=[v for v in m['font_allocations'] if not re.fullmatch('font-glyph-[0-9a-f]{2}',v['name'])]+placed[:95]
    for collection in ('statement_modules','spacing_allocations'):
        for v in m[collection]:
            if v['name']=='spacing-1':v['bytes']=9
    m['statement_modules'].append(allocations[0])
    m['ram_map']['blocks'].append(['paper Y fractional accumulator','1B8D','1B8E'])
    m.update(version='0.4.91-dev',sha256=hashlib.sha256(cpu).hexdigest(),base_cpu_sha256=BASE_SHA,
        explicit_free_regions=free,explicit_free_bytes=available,
        known_free_fragmented_bytes=m['known_free_fragmented_bytes']-40+saved,
        status='Awaiting motion-sequence equivalence, X/Y coil and font validation',
        y_poststep=dict(numerator=3,denominator=8,accumulator=0x1B8D,minimum_reverse_units=2,
            method='normal reverse approach, then separate forward unit on fraction overflow',
            native_reverse_approach_unchanged=True,allocations=allocations,patches=patches,
            font_packing_seed=seed,font_streams_unchanged=True,shared_bytes_saved=saved,
            word_relocations=reloc))
    m.pop('nh7_sha256',None)
    s={k:reloc.get(v,v) for k,v in s.items()}
    s.update({k:v for k,v in links.items() if k.startswith('YP')})
    (out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (out/'symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    (ROOT/'studio/internal/profiles/basic-0.4.91-symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    print(json.dumps(dict(version=m['version'],sha256=m['sha256'],free_rom=available,packing_seed=seed)))


if __name__=='__main__':main()
