""".93: cache/repeat GLYPH bands and add large square mode 4.

Lossless font run selection is optimized to pay for the bounded extension.
All released native motor code and .92 Y compensation remain unchanged.
"""
from pathlib import Path
from collections import Counter
import hashlib,heapq,json,random,re,subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/glyph-repeat'
BASE_SHA='593faec8efc637ce0082609c04f82b47ffe56be45fd9f98e26caac5a0643bffc'
ASSEMBLER=ROOT.parent.parent/'ROMReader/tmp/m680x-tools/a09.exe'


def assemble(name,body,at,definitions):
    own=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    defs=''.join(f'{k} EQU ${v:04X}\n' for k,v in definitions.items() if k not in own)
    path=OUT/(name+'.asm')
    path.write_text(' OPT H01\n'+defs+f' ORG ${at:04X}\n'+body,encoding='ascii')
    run=subprocess.run([str(ASSEMBLER),'-W','-B'+str(path.with_suffix('.bin')),
                        '-L'+str(path.with_suffix('.lst')),str(path)],capture_output=True,text=True)
    assert run.returncode==0,run.stdout+run.stderr
    table=path.with_suffix('.lst').read_text().split('SYMBOL TABLE')[1]
    labels={n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',table)}
    return path.with_suffix('.bin').read_bytes(),labels,own


def font_streams():
    expected={k:bytes.fromhex(v) for k,v in json.loads((ROOT/'build/paper-list/font-expected.json').read_text()).items()}
    deltas={k:bytes(v^(raw[i-3] if i>=3 else 0) for i,v in enumerate(raw)) for k,raw in expected.items()}
    marker,threshold,count=0xB1,8,15
    assert all(not any(marker<=v<marker+count for v in row) for row in deltas.values())
    costs={v:12 for v in range(256)};costs[0]=1
    for _ in range(3):
        packed={}
        for ch,data in deltas.items():
            values=[];i=0
            while i<len(data):
                if data[i]:values.append(data[i]);i+=1;continue
                end=i+1
                while end<len(data) and data[end]==0:end+=1
                size=end-i
                if end==len(data):values.extend([0]*size);i=end;continue
                dp=[(0,[])]
                for n in range(1,size+1):
                    choices=[(dp[n-1][0]+costs[0],dp[n-1][1]+[0])]
                    for v in range(count):
                        take=threshold+v
                        if take<=n:choices.append((dp[n-take][0]+costs[marker+v],dp[n-take][1]+[marker+v]))
                    dp.append(min(choices))
                values.extend(dp[size][1]);i=end
            packed[ch]=values
        freq=Counter(v for row in packed.values() for v in row)
        heap=[(n,v,{v:0}) for v,n in freq.items()];heapq.heapify(heap);serial=256
        while len(heap)>1:
            n,_,a=heapq.heappop(heap);k,_,b=heapq.heappop(heap)
            heapq.heappush(heap,(n+k,serial,{v:d+1 for v,d in (a|b).items()}));serial+=1
        lengths=heap[0][2];assert max(lengths.values())<=12
        order=sorted(lengths,key=lambda v:(lengths[v],v));codes={};code=previous=0
        for v in order:
            size=lengths[v];code<<=size-previous;codes[v]=(code,size);code+=1;previous=size
        assert codes[0][0]==0
        costs={v:lengths.get(v,12) for v in range(256)}
    table=bytes(sum(d==n for d in lengths.values()) for n in range(1,13))+bytes(order)
    streams={}
    for ch,values in packed.items():
        bits=''.join(format(codes[v][0],f'0{codes[v][1]}b') for v in values)
        bits+='0'*(-len(bits)%8)
        streams[f'font-glyph-{ord(ch):02x}']=bytes(int(bits[i:i+8],2) for i in range(0,len(bits),8)).rstrip(b'\0')
    return table,streams


def main():
    OUT.mkdir(exist_ok=True)
    base=ROOT/'release/s70-basic-0.4.92-dev-canon-start-nh7.bin'
    raw=base.read_bytes();old=raw[16384:]+raw[:16384]
    assert hashlib.sha256(old).hexdigest()==BASE_SHA
    s=json.loads((ROOT/'studio/internal/profiles/basic-0.4.92-symbols.json').read_text())
    m=json.loads(base.with_name(base.stem+'-manifest.json').read_text())
    source=(ROOT/'src/paper-glyph-repeat.asm').read_text()
    parts=re.split(r'; @island (\w+)\n',source)
    bodies=dict(zip(parts[1::2],parts[2::2]))
    own=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b','\n'.join(bodies.values()),re.M))
    links=dict(s,SGREPEAT=0x1D9A)
    links.update({k:0x4000 for k in own})
    modules=[]
    for name,body in bodies.items():
        code,_,_=assemble(name,body,0x4000,links)
        modules.append(dict(name=name,data=code,body=body))
    print('Module sizes',[(v['name'],len(v['data'])) for v in modules],flush=True)
    font_table,streams=font_streams()
    table_at=next(v['origin'] for v in m['font_allocations'] if v['name']=='font-huffman-table')
    hf=(ROOT/'src/paper-font-runs-byte.asm').read_text()
    hf_links=dict(s,HFCOUNTS=table_at,HFSYMBOLS=table_at+12)
    decoder,hf_labels,hf_own=assemble('font',hf,s['HFDECODE'],hf_links)
    assert len(decoder)<274 and len(font_table)==131
    links.update({k:hf_labels[k] for k in hf_own})
    links.update(HFCOUNTS=table_at,HFSYMBOLS=table_at+12)
    glyphs=[v.copy() for v in m['font_allocations'] if re.fullmatch('font-glyph-[0-9a-f]{2}',v['name'])]
    assert len(glyphs)==95
    word_sites=set(s['TOKENPTRS']+2*i for i in range(37))
    p=s['CMDTABLE'];seen=set()
    while p:
        assert p not in seen;seen.add(p)
        key=int.from_bytes(old[p-0x4000:p-0x4000+2],'big')
        handler=int.from_bytes(old[p-0x4000+2:p-0x4000+4],'big')
        if not key:p=handler;continue
        word_sites.add(p);p+=4
    word_addresses={int.from_bytes(old[p-0x4000:p-0x4000+2],'big') for p in word_sites}
    word_data={p:old[p-0x4000:].split(b'\0',1)[0]+b'\0' for p in word_addresses}
    assert all(2<=len(v)<=12 and all(65<=c<=90 for c in v[:-1]) for v in word_data.values())
    fixed_aliases={}
    for p,data in word_data.items():
        if data not in (b'RETURN\0',b'NEXT\0'):continue
        found=[i+0x4000 for i in range(len(old)-len(data)+1) if old[i:i+len(data)]==data
               and not any(a<=i+0x4000<a+len(v) for a,v in word_data.items())]
        assert len(found)<=1,(data,found)
        if found:fixed_aliases[p]=found[0]
    # Move only private GLYPH code and pure glyph data, preserving all native services.
    retired=[[s['SGPARSE'],s['SGCOMMANDEND']],[s['SGSUBMIT'],s['SGSELECT']],
             [s['SGRENDER'],s['SGRENDER']+144],[s['PETAIL'],s['PEEND']],
             [s['HFDECODE']+len(decoder),s['HFEND']],
             [table_at+len(font_table),table_at+144]]
    free=[]
    for a,b in sorted(m['explicit_free_regions']+retired+[[p,p+len(v)] for p,v in word_data.items()]+[[v['origin'],v['origin']+v['bytes']] for v in glyphs if v['bytes']]):
        if free and a<=free[-1][1]:free[-1][1]=max(b,free[-1][1])
        else:free.append([a,b])
    cpu=bytearray(old);allowed=[v[:] for v in free];patches=[]
    for a,b in free:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
    def patch(a,expected,new):
        assert len(expected)==len(new)
        assert cpu[a-0x4000:a-0x4000+len(expected)]==expected,hex(a)
        cpu[a-0x4000:a-0x4000+len(new)]=new
        allowed.append([a,a+len(new)])
        patches.append(dict(address=a,old=expected.hex(),new=new.hex()))
    patch(table_at,old[table_at-0x4000:table_at-0x4000+len(font_table)],font_table)
    patch(s['HFDECODE'],old[s['HFDECODE']-0x4000:s['HFDECODE']-0x4000+len(decoder)],decoder)
    # Exact suffix/contained sharing, keeping original per-character bounds.
    groups=[dict(name=name,data=data,members={name:0}) for name,data in streams.items() if data]
    groups += [dict(name=f'word-{p:04x}',data=data,members={f'word-{p:04x}':0})
               for p,data in word_data.items() if p not in fixed_aliases]
    while True:
        best=(0,None,None,0)
        for i,a in enumerate(groups):
            for j,b in enumerate(groups):
                if i==j:continue
                offset=a['data'].find(b['data'])
                if offset>=0:score=len(b['data'])
                else:
                    score=next((n for n in range(min(len(a['data']),len(b['data'])),0,-1) if a['data'][-n:]==b['data'][:n]),0)
                    offset=len(a['data'])-score
                if score>best[0]:best=(score,i,j,offset)
        score,i,j,offset=best
        if not score:break
        a,b=groups[i],groups[j]
        groups=[v for k,v in enumerate(groups) if k not in (i,j)]+[dict(name=a['name'],data=a['data']+b['data'][max(0,len(a['data'])-offset):],members=a['members']|{name:p+offset for name,p in b['members'].items()})]
    groups += [dict(name='module-'+v['name'],data=v['data'],members={}) for v in modules]
    initial_free=[v[:] for v in free]
    print('Budget',sum(b-a for a,b in free),'needed',sum(len(v['data']) for v in groups),flush=True)
    (OUT/'packing-input.json').write_text(json.dumps(dict(bins=initial_free,items=[dict(name=v['name'],size=len(v['data'])) for v in groups])))
    for seed in range(500):
        pending=list(groups);random.Random(seed).shuffle(pending)
        free=[v[:] for v in initial_free];placed=[]
        if seed<400:
            # Place long, indivisible modules before smaller font streams.
            rng=random.Random(seed)
            pending.sort(key=lambda v:-(len(v['data'])+rng.randrange(1+seed//10)))
            rest=[]
            for v in pending:
                bins=[i for i,(a,b) in enumerate(free) if b-a>=len(v['data'])]
                if not bins:rest.append(v);continue
                i=min(bins,key=lambda i:free[i][1]-free[i][0]-len(v['data']))
                placed.append(dict(v,origin=free[i][0]));free[i][0]+=len(v['data'])
            pending=rest
            if not pending:break
            continue
        for i in sorted(range(len(free)),key=lambda i:free[i][1]-free[i][0]):
            a,b=free[i];choices={0:[]}
            for j,v in enumerate(pending):
                for n,items in sorted(list(choices.items()),reverse=True):
                    nn=n+len(v['data'])
                    if nn<=b-a and nn not in choices:choices[nn]=items+[j]
            chosen=choices[max(choices)]
            for j in chosen:
                v=pending[j];placed.append(dict(v,origin=a));a+=len(v['data'])
            pending=[v for j,v in enumerate(pending) if j not in chosen];free[i]=[a,b]
        if not pending:break
    assert not pending,[(v['name'],len(v['data'])) for v in pending]
    locations={v['name']:v['origin'] for v in placed}
    for v in modules:
        _,labels,_=assemble(v['name'],v['body'],locations['module-'+v['name']],links)
        links.update({k:labels[k] for k in own if k in labels and k in set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',v['body'],re.M))})
    positions={}
    for v in placed:
        a=v['origin'];data=v['data']
        if v['name'].startswith('module-'):
            item=next(p for p in modules if 'module-'+p['name']==v['name'])
            data,_,_=assemble(item['name'],item['body'],a,links)
            assert len(data)==len(v['data'])
        assert cpu[a-0x4000:a-0x4000+len(data)]==b'\xff'*len(data)
        cpu[a-0x4000:a-0x4000+len(data)]=data
        positions.update({name:a+offset for name,offset in v['members'].items()})
    for glyph in glyphs:
        name=glyph['name'];n=len(streams[name]);a=positions.get(name,0)
        assert cpu[a-0x4000:a-0x4000+n]==streams[name] if n else True
        ptr=s['HFGLYPHS']+3*(int(name[-2:],16)-32)
        patch(ptr,old[ptr-0x4000:ptr-0x4000+3],a.to_bytes(2,'big')+bytes([n]))
        glyph.update(origin=a,bytes=n)
    reloc={p:fixed_aliases[p] if p in fixed_aliases else positions[f'word-{p:04x}'] for p in word_data}
    for p,data in word_data.items():
        a=reloc[p]
        assert cpu[a-0x4000:a-0x4000+len(data)]==data
    direct=[]
    for target in word_data:
        needle=b'\xce'+target.to_bytes(2,'big')
        for i in range(len(old)-2):
            if old[i:i+3]==needle and not any(a<=i+0x4000<b for a,b in allowed):
                word_sites.add(i+0x4001);direct.append(i+0x4000)
    for p in sorted(word_sites):
        target=int.from_bytes(old[p-0x4000:p-0x4000+2],'big')
        assert target in reloc
        patch(p,target.to_bytes(2,'big'),reloc[target].to_bytes(2,'big'))
    print('Direct word references',list(map(hex,direct)),flush=True)
    # Live incoming references to moved code: command table, staging, renderer,
    # the existing LPFORMAT tail hook, and raw-band next-pointer hook.
    p=s['CMDTABLE'];seen=set();handlers=[]
    while p:
        assert p not in seen;seen.add(p)
        key=int.from_bytes(old[p-0x4000:p-0x4000+2],'big')
        handler=int.from_bytes(old[p-0x4000+2:p-0x4000+4],'big')
        if not key:p=handler;continue
        if handler==s['SGPARSE']:
            patch(p+2,handler.to_bytes(2,'big'),links['SGPARSE'].to_bytes(2,'big'));handlers.append(p)
        p+=4
    assert len(handlers)==1
    for lo,hi,target in [(s['SGSTAGE'],s['SGSTAGEEND'],'SGSUBMIT'),(s['SGSELECTRAW'],s['SGRESET'],'SGRENDER'),(s['LPFORMAT'],s['LPSELECT'],'PETAIL')]:
        needle=b'\x7e'+s[target].to_bytes(2,'big');segment=old[lo-0x4000:hi-0x4000]
        assert segment.count(needle)==1,(target,segment.hex())
        a=lo+segment.index(needle);patch(a,needle,b'\x7e'+links[target].to_bytes(2,'big'))
    patch(s['LPADD64'],bytes.fromhex('c3004039'),b'\x7e'+links['SGWRAP'].to_bytes(2,'big')+b'\x01')
    patch(s['LPNATIVEPRINT'],b'\x7e'+s['GPPRINT'].to_bytes(2,'big'),b'\x7e'+links['SGPRINT'].to_bytes(2,'big'))
    banner=b'Typestar BASIC 0.4.92-dev';a=old.index(banner)+0x4000
    patch(a,banner,b'Typestar BASIC 0.4.93-dev')
    assert all(x==y or any(a<=i+0x4000<b for a,b in allowed) for i,(x,y) in enumerate(zip(old,cpu)))
    s={k:reloc.get(v,v) for k,v in s.items()}
    s.update({k:v for k,v in links.items() if k in own or k in hf_own or k in ('SGREPEAT','HFCOUNTS','HFSYMBOLS')})
    for v in m['command_dispatch']:
        v['key']=reloc[v['key']]
        if v['name']=='GLYPH':v['handler']=s['SGPARSE']
    free=sorted([v for v in free if v[0]<v[1]])
    m['font_allocations']=[v for v in m['font_allocations'] if not re.fullmatch('font-glyph-[0-9a-f]{2}',v['name'])]+glyphs
    for item in m['font_allocations']:
        if item['name']=='font-huffman-table':item['bytes']=len(font_table)
    for item in m['native_allocations']:
        if item['origin'] in reloc:item['origin']=reloc[item['origin']]
    m.update(version='0.4.93-dev',sha256=hashlib.sha256(cpu).hexdigest(),base_cpu_sha256=BASE_SHA,
             explicit_free_regions=free,explicit_free_bytes=sum(b-a for a,b in free),
             known_free_fragmented_bytes=sum(b-a for a,b in free)+m['other_tracked_fragment_bytes'],
             status='Awaiting repeat/mode/font regression and physical test',
             font_run_threshold=8,font_run_stream_bytes=sum(map(len,streams.values())),
             font_run_decoder_bytes=len(decoder),
             glyph_repeat=dict(maximum=16,scratch=0x1D9A,mode4='physical X4/Y2 square',
                               allocations=[dict(name=v['name'],origin=locations['module-'+v['name']],bytes=len(v['data'])) for v in modules],
                               patches=patches,font_run_maximum=22,font_run_marker=0xB1,
                               word_relocations=reloc,
                               packing_seed=seed))
    m.pop('nh7_sha256',None)
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    (ROOT/'studio/internal/profiles/basic-0.4.93-symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    print(json.dumps(dict(version=m['version'],sha256=m['sha256'],free_rom=m['explicit_free_bytes'])))


if __name__=='__main__':main()
