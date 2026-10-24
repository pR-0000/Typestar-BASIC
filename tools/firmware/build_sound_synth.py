""".95 known-gate sound synthesis; lossless keyboard/font repacking pays for it.

All reclaimed ranges are private BASIC code or explicitly described data.
Original startup, motor services, math and serial code stay byte-identical.
"""
from pathlib import Path
from collections import Counter
import hashlib, heapq, json, random, re, subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/sound-synth'
ASSEMBLER=ROOT.parent.parent/'ROMReader/tmp/m680x-tools/a09.exe'
BASE_SHA='a0e94545bd5b8ff1fc551fe8c2478fdab6b3e04c26aec382e0d62ad163b621ba'

def assemble(name,body,at,s):
    own=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    text=' OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items() if k not in own)
    path=OUT/(name+'.asm');path.write_text(text+f' ORG ${at:04X}\n'+body)
    run=subprocess.run([str(ASSEMBLER),'-W','-B'+str(path.with_suffix('.bin')),'-L'+str(path.with_suffix('.lst')),str(path)],capture_output=True,text=True)
    assert not run.returncode,run.stdout+run.stderr
    listing=path.with_suffix('.lst').read_text()
    assert 'out of range' not in listing.lower(),name
    table=listing.split('SYMBOL TABLE')[1]
    labels={n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',table)}
    return path.with_suffix('.bin').read_bytes(),{n:labels[n] for n in own}

def font():
    expected={k:bytes.fromhex(v) for k,v in json.loads((ROOT/'src/paper-font-reference.json').read_text()).items()}
    mirrors={'\\':'/','>':'<',']':'[','}':'{'}
    for a,b in mirrors.items():
        assert expected[a]==b''.join(expected[b][i:i+3] for i in range(90,-1,-3))
    deltas={k:bytes(v^(r[i-3] if i>=3 else 0) for i,v in enumerate(r)) for k,r in expected.items() if k not in mirrors}
    costs=[{v:12 for v in range(256)} for _ in range(3)]
    for c in costs:c[0]=1
    for _ in range(4):
        packed={};freq=[Counter() for _ in range(3)]
        for ch,data in deltas.items():
            vals=[];i=0
            while i<len(data):
                if data[i]:vals.append((i%3,data[i]));i+=1;continue
                end=i+1
                while end<len(data) and not data[end]:end+=1
                if end==len(data):vals.extend((j%3,0) for j in range(i,end));i=end;continue
                dp=[(0,[])]
                for n in range(1,end-i+1):
                    choices=[(dp[n-1][0]+costs[(i+n-1)%3][0],dp[n-1][1]+[(n-1,0)])]
                    for v in range(15):
                        take=13+v
                        if take<=n:choices.append((dp[n-take][0]+costs[(i+n-take)%3][177+v],dp[n-take][1]+[(n-take,177+v)]))
                    dp.append(min(choices))
                vals.extend(((i+j)%3,v) for j,v in dp[-1][1]);i=end
            packed[ch]=vals
            for c,v in vals:freq[c][v]+=1
        books=[];tables=[]
        for f in freq:
            heap=[(n,v,{v:0}) for v,n in f.items()];heapq.heapify(heap);serial=256
            while len(heap)>1:
                n,_,a=heapq.heappop(heap);k,_,b=heapq.heappop(heap)
                heapq.heappush(heap,(n+k,serial,{v:d+1 for v,d in (a|b).items()}));serial+=1
            lengths=heap[0][2];assert max(lengths.values())<=11
            order=sorted(lengths,key=lambda v:(lengths[v],v));codes={};code=prev=0
            for v in order:
                size=lengths[v];code<<=size-prev;codes[v]=(code,size);code+=1;prev=size
            assert codes[0]==(0,1),codes[0]
            books.append(codes);tables.append(bytes(sum(d==n for d in lengths.values()) for n in range(1,12))+bytes(order))
            costs[len(books)-1]={v:lengths.get(v,12) for v in range(256)}
        streams={}
        for ch,vals in packed.items():
            bits=''.join(format(books[c][v][0],f'0{books[c][v][1]}b') for c,v in vals);bits+='0'*(-len(bits)%8)
            streams[ch]=bytes(int(bits[i:i+8],2) for i in range(0,len(bits),8)).rstrip(b'\0')
    return tables,{k:v for k,v in streams.items() if k not in mirrors},mirrors

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    old=(ROOT/'build/glyph-pair/EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    assert hashlib.sha256(old).hexdigest()==BASE_SHA
    s=json.loads((ROOT/'build/glyph-pair/symbols.json').read_text());base_symbols=s.copy()
    m=json.loads((ROOT/'build/glyph-pair/manifest.json').read_text())
    rows=json.loads((ROOT/'src/keyboard-reference.json').read_text())
    normalized=[[v+32 if i%2 and 65<=v<=90 else v for v in row] for i,row in enumerate(rows)]
    assert all(not any(97<=v<=122 for v in row) for row in rows[1::2])
    parents={0:None};diff={0:[]}
    while len(parents)<40:
        _,a,b=min((sum(x!=y for x,y in zip(normalized[a],normalized[b])),a,b) for a in parents for b in range(40) if b not in parents)
        parents[b]=a;diff[b]=[(k,y) for k,(x,y) in enumerate(zip(normalized[a],normalized[b])) if x!=y]
    aliases={}
    for i in range(40):
        a=i
        while a and not diff[a]:a=parents[a]
        aliases[i]=a
    retired=[[s['KDENTRY'],s['KDDATAEND']],[s['HFDECODE'],s['HFEND']],[s['BASICBEEP'],s['SNDDIVDONE']+1],[s['HFCOUNTS'],s['HFCOUNTS']+131]]
    for i in range(95):
        p=s['HFGLYPHS']-0x4000+3*i;a=int.from_bytes(old[p:p+2],'big');n=old[p+2]
        if n:retired.append([a,a+n])
    word_sites=set(s['TOKENPTRS']+2*i for i in range(37));p=s['CMDTABLE'];commands=[]
    while p:
        key=int.from_bytes(old[p-0x4000:p-0x4000+2],'big');h=int.from_bytes(old[p-0x4000+2:p-0x4000+4],'big')
        if not key:p=h;continue
        word_sites.add(p);commands.append((p,key,h));p+=4
    word_data={int.from_bytes(old[p-0x4000:p-0x4000+2],'big'):None for p in word_sites}
    for a in word_data:
        word_data[a]=old[a-0x4000:].split(b'\0',1)[0]+b'\0';retired.append([a,a+len(word_data[a])])
    free=[]
    for a,b in sorted(retired+m['explicit_free_regions']):
        if free and a<=free[-1][1]:free[-1][1]=max(b,free[-1][1])
        else:free.append([a,b])
    initial=[v[:] for v in free];cpu=bytearray(old);patches=[]
    for a,b in free:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
    def patch(a,new):
        assert not any(lo<=a<hi for lo,hi in initial),hex(a)
        before=old[a-0x4000:a-0x4000+len(new)];cpu[a-0x4000:a-0x4000+len(new)]=new
        patches.append(dict(address=a,old=before.hex(),new=new.hex()))
    tables,streams,mirrors=font()
    bodies={'keyboard':(ROOT/'src/keyboard-normalized.asm').read_text(),'font':(ROOT/'src/paper-font-relative.asm').read_text()}
    text=(ROOT/'src/sound-synth.asm').read_text();p=re.split(r'; @island (\w+)\n',text)
    for name,body in zip(p[1::2],p[2::2]):bodies['snd-'+name]=p[0]+body
    links=dict(s,HFTABLES=0x4000,KDDATA=0x4000);own=set()
    for body in bodies.values():own.update(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    links.update({k:0x4000 for k in own})
    groups=[]
    for name,body in bodies.items():
        data,_=assemble(name,body,0x4000,links);groups.append(dict(name='code-'+name,data=data,members={}))
    groups.extend(dict(name='font-'+str(ord(k)),data=v,members={'font-'+str(ord(k)):0}) for k,v in streams.items() if v)
    groups.extend(dict(name='word-'+str(a),data=v,members={'word-'+str(a):0}) for a,v in word_data.items())
    for i,table in enumerate(tables):groups.append(dict(name='hf-'+str(i),data=table,members={'hf-'+str(i):0}))
    # A root omits the mechanically generated a..z prefix.
    keydata=bytearray([255]+normalized[0][26:]+[0]);keyoffsets={0:0}
    for i in range(1,40):
        if aliases[i]==i:
            keyoffsets[i]=len(keydata);keydata.extend([v for pair in diff[i] for v in pair]+[254,parents[i]])
    assert len(keydata)<=512 and all(not n%2 for n in keyoffsets.values())
    groups.extend([dict(name='key-data',data=bytes(keydata),members={}),
                   dict(name='key-table',data=bytes(40),members={}),dict(name='hf-table',data=bytes(6),members={})])
    # Share exact/suffix overlaps among immutable keyword/font streams.
    immutable=[v for v in groups if v['name'].startswith(('font-','word-'))]
    groups=[v for v in groups if v not in immutable]
    while True:
        best=(0,None,None,0)
        for i,a in enumerate(immutable):
            for j,b in enumerate(immutable):
                if i==j:continue
                offset=a['data'].find(b['data'])
                if offset>=0:score=len(b['data'])
                else:
                    score=next((n for n in range(min(len(a['data']),len(b['data'])),0,-1) if a['data'][-n:]==b['data'][:n]),0);offset=len(a['data'])-score
                if score>best[0]:best=(score,i,j,offset)
        score,i,j,offset=best
        if not score:break
        a,b=immutable[i],immutable[j]
        immutable=[v for k,v in enumerate(immutable) if k not in (i,j)]+[dict(name=a['name'],data=a['data']+b['data'][max(0,len(a['data'])-offset):],members=a['members']|{name:p+offset for name,p in b['members'].items()})]
    groups+=immutable
    need=sum(len(v['data']) for v in groups);budget=sum(b-a for a,b in initial)
    print('Modules',[(v['name'],len(v['data'])) for v in groups if v['name'].startswith('code')],flush=True)
    print('Budget',budget,'need',need,'remaining',budget-need,flush=True)
    (OUT/'packing-input.json').write_text(json.dumps(dict(bins=initial,items=[dict(name=v['name'],size=len(v['data'])) for v in groups])))
    assert need<=budget
    for seed in range(1000):
        free=[v[:] for v in initial];pending=list(groups);random.Random(seed).shuffle(pending)
        rng=random.Random(seed);pending.sort(key=lambda v:-(len(v['data'])+rng.randrange(1+seed//20)))
        placed=[]
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
        if len(placed)==len(groups):break
    assert len(placed)==len(groups),[(v['name'],len(v['data'])) for v in pending]
    locations={v['name']:v['origin'] for v in placed};positions={n:v['origin']+off for v in placed for n,off in v['members'].items()}
    links.update(KDTABLE=locations['key-table'],KDDATA=locations['key-data'],HFTABLES=locations['hf-table'])
    for name,body in bodies.items():
        _,labels=assemble(name,body,locations['code-'+name],links);links.update(labels)
    for v in placed:
        name=v['name'];a=v['origin'];data=v['data']
        if name.startswith('code-'):data,_=assemble(name,bodies[name[5:]],a,links)
        elif name=='key-table':data=bytes(keyoffsets[aliases[i]]//2 for i in range(40))
        elif name=='hf-table':data=b''.join(positions['hf-'+str(i)].to_bytes(2,'big') for i in range(3))
        assert len(data)==len(v['data'])
        assert cpu[a-0x4000:a-0x4000+len(data)]==b'\xff'*len(data)
        cpu[a-0x4000:a-0x4000+len(data)]=data
    reloc={a:positions['word-'+str(a)] for a in word_data}
    for a in word_data:
        needle=b'\xce'+a.to_bytes(2,'big')
        for i in range(len(old)-2):
            if old[i:i+3]==needle and not any(lo<=i+0x4000<hi for lo,hi in initial):word_sites.add(i+0x4001)
    for p in sorted(word_sites):patch(p,reloc[int.from_bytes(old[p-0x4000:p-0x4000+2],'big')].to_bytes(2,'big'))
    for ch in map(chr,range(32,127)):
        base=mirrors.get(ch,ch);n=len(streams[base]);a=positions.get('font-'+str(ord(base)),0)
        patch(s['HFGLYPHS']+3*(ord(ch)-32),a.to_bytes(2,'big')+bytes([n|(128 if ch in mirrors else 0)]))
    for p,key,h in commands:
        for label in ('BASICBEEP','BASICSOUND'):
            if h==s[label]:patch(p+2,links[label].to_bytes(2,'big'))
    # Incoming calls to decoder / keyboard: only instruction-shaped references.
    incoming=[]
    for label in ('HFDECODE','KDENTRY'):
        for op in (0x7e,0xbd):
            needle=bytes([op])+s[label].to_bytes(2,'big')
            for i in range(len(old)-2):
                if old[i:i+3]==needle and not any(a<=i+0x4000<b for a,b in initial):
                    patch(i+0x4001,links[label].to_bytes(2,'big'));incoming.append((label,i+0x4000))
    assert len(incoming)==2,incoming
    banner=b'Typestar BASIC 0.4.94-dev';patch(old.index(banner)+0x4000,b'Typestar BASIC 0.4.95-dev')
    allowed=initial+[[v['address'],v['address']+len(bytes.fromhex(v['new']))] for v in patches]
    assert all(a==b or any(lo<=i+0x4000<hi for lo,hi in allowed) for i,(a,b) in enumerate(zip(old,cpu)))
    s={k:reloc.get(v,v) for k,v in s.items()};s.update(links)
    # Restore relocated keyword symbols after code labels were applied.
    for k,v in list(s.items()):
        if k not in own and v in reloc:s[k]=reloc[v]
    s['KDTABLE']=locations['key-table'];s['HFTABLES']=locations['hf-table']
    digest=hashlib.sha256(cpu).hexdigest();free=[v for v in free if v[0]<v[1]]
    manifest=dict(version='0.4.95-dev',sha256=digest,base_cpu_sha256=BASE_SHA,
                  explicit_free_regions=free,explicit_free_bytes=sum(b-a for a,b in free),
                  other_tracked_fragment_bytes=m['other_tracked_fragment_bytes'],ram_program_bytes=5951,
                  command_dispatch=[dict(name=word_data[key][:-1].decode(),key=reloc[key],handler=next((links[n] for n in ('BASICBEEP','BASICSOUND') if h==base_symbols[n]),h)) for p,key,h in commands],
                  allocations=[dict(name=v['name'],origin=v['origin'],bytes=len(v['data'])) for v in placed],
                  patches=patches,reclaimed=initial,keyboard_incoming=incoming,
                  sound=dict(rate_min=60,rate_max=31250,duty_min=1,duty_max=99,noise_min=1000,maximum_ms=2000,heap_noise_reserve=512))
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s,indent=2)+'\n');(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ROOT/'studio/internal/profiles/basic-0.4.95-symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    print(json.dumps(dict(sha256=digest,free_rom=manifest['explicit_free_bytes'],packing_seed=seed)))

if __name__=='__main__':main()
