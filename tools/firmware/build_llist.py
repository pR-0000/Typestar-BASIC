"""Build .88 LLIST using shared LIST/SAVE formatting and a lossless run-coded font.

CPU-order image only. Native startup, UART protocol and motor routines remain
byte-identical. Reuse HELP's reserved token without shifting any other id.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib, json, random, re, subprocess, heapq
from collections import Counter
from paper_ascii_font import corrected

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/paper-list'
ASSEMBLER=ROOT.parent.parent/'ROMReader/tmp/m680x-tools/a09.exe'

def assemble(name, source):
    path=OUT/(name+'.asm');path.write_text(source,encoding='ascii')
    run=subprocess.run([str(ASSEMBLER),'-W','-B'+str(OUT/(name+'.bin')),
                        '-L'+str(OUT/(name+'.lst')),str(path)],capture_output=True,text=True)
    if run.returncode:raise RuntimeError(run.stdout+run.stderr)
    table=(OUT/(name+'.lst')).read_text().split('SYMBOL TABLE')[1]
    syms={n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',table)}
    return (OUT/(name+'.bin')).read_bytes(),syms

def main():
    OUT.mkdir(exist_ok=True)
    base=ROOT/'build/paper-empty-tail'
    old=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    assert hashlib.sha256(old).hexdigest()=='330d00173287c65576bb3ee988008750c2953265929441964a08711af59859da'
    s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
    assert m['version']=='0.4.87-dev'
    old_glyphs=[r.copy() for r in m['font_allocations'] if re.fullmatch(r'font-glyph-[0-9a-f]{2}',r['name'])]
    expected,_=corrected(json.loads((ROOT/'build/paper-font/native-trace.json').read_text()))
    packed={}
    for ch,raw in expected.items():
        delta=bytes(v^(raw[i-3] if i>=3 else 0) for i,v in enumerate(raw))
        assert not any(0xBB<=v<=0xBF for v in delta)
        values=[];i=0
        while i<len(delta):
            if delta[i]:values.append(delta[i]);i+=1;continue
            end=i+1
            while end<len(delta) and not delta[end]:end+=1
            n=end-i
            while n>=12 and end<len(delta):
                take=min(n,16);values.append(0xB0+take-1);n-=take
            values.extend([0]*n);i=end
        packed[ch]=values
    freq=Counter(v for row in packed.values() for v in row)
    heap=[(n,v,{v:0}) for v,n in freq.items()];heapq.heapify(heap);serial=256
    while len(heap)>1:
        n,_,a=heapq.heappop(heap);k,_,b=heapq.heappop(heap)
        heapq.heappush(heap,(n+k,serial,{v:d+1 for v,d in (a|b).items()}));serial+=1
    lengths=heap[0][2];assert max(lengths.values())<=s['HFMAXBITS']
    order=sorted(lengths,key=lambda v:(lengths[v],v));codes={};code=0;prev=0
    for v in order:
        bits=lengths[v];code<<=bits-prev;codes[v]=(code,bits);code+=1;prev=bits
    assert codes[0][0]==0
    counts=b''.join(sum(d==n for d in lengths.values()).to_bytes(2,'big') for n in range(1,s['HFMAXBITS']+1))
    huffman_table=bytes([s['HFMAXBITS']])+counts+bytes(order)
    old_table=next(r for r in m['font_allocations'] if r['name']=='font-huffman-table')
    assert len(huffman_table)<=old_table['bytes']
    streams={}
    for ch,values in packed.items():
        bits=''.join(format(codes[v][0],f'0{codes[v][1]}b') for v in values);bits+='0'*(-len(bits)%8)
        streams[f'font-glyph-{ord(ch):02x}']=bytes(int(bits[i:i+8],2) for i in range(0,len(bits),8)).rstrip(b'\0')
    glyphs=[dict(r,bytes=len(streams[r['name']])) for r in old_glyphs]
    hf=(ROOT/'src/paper-font-huffman.asm').read_text()
    def font_link(body,name):
        own=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
        return assemble(name,' OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items() if k not in own)+f" ORG ${s['HFDECODE']:04X}\n"+body)
    old_decoder,old_hf=font_link(hf,'font-old-check')
    # .76 changed only the exhausted-stream branch to a virtual-zero leaf.
    zero=next(r for r in m['ascii_allocations'] if r['name']=='font-zero-suffix')
    check=bytearray(old_decoder);branch=s['HFGETBIT']-s['HFDECODE']+11
    assert check[branch]==0x24 and old[zero['origin']-0x4000:zero['origin']-0x4000+3]==bytes.fromhex('5f0c39')
    check[branch+1]=(zero['origin']-(s['HFGETBIT']+13))&255
    assert old[s['HFDECODE']-0x4000:s['HFDECODE']-0x4000+len(check)]==check
    decoder,new_hf=font_link((ROOT/'src/paper-font-runs.asm').read_text(),'font-runs')
    help_ptr=s['TOKENPTRS']+20;list_ptr=s['TOKENPTRS']+8
    oldhelp=int.from_bytes(old[help_ptr-0x4000:help_ptr-0x4000+2],'big')
    oldlist=int.from_bytes(old[list_ptr-0x4000:list_ptr-0x4000+2],'big')
    assert old[oldhelp-0x4000:oldhelp-0x4000+5]==b'HELP\0'
    assert old[oldlist-0x4000:oldlist-0x4000+5]==b'LIST\0'
    retired=[[s['RLIST'],s['SEGTHREEEND']],[s['SAVECMD'],s['RSVTEXT']],
             [oldhelp,oldhelp+5],[oldlist,oldlist+5],
             [s['HFDECODE'],s['LPPARSE']+3],[zero['origin'],zero['origin']+3],
             [old_table['origin']+len(huffman_table),old_table['origin']+old_table['bytes']]]
    free=[]
    for a,b in sorted(m['explicit_free_regions']+retired+[[r['origin'],r['origin']+r['bytes']] for r in old_glyphs if r['bytes']]):
        if free and a<=free[-1][1]:free[-1][1]=max(b,free[-1][1])
        else:free.append([a,b])
    allowed=[r[:] for r in free];cpu=bytearray(old);patches=[];alloc=[]
    for a,b in free:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)

    def reserve(name,n,at=None):
        options=[(b-a,i) for i,(a,b) in enumerate(free) if b-a>=n and (at is None or a<=at and at+n<=b)]
        assert options,(name,n,free)
        _,i=min(options);a,b=free.pop(i);at=a if at is None else at
        if a<at:free.append([a,at])
        if at+n<b:free.append([at+n,b])
        alloc.append(dict(name=name,origin=at,bytes=n));return at

    def put(at,data):
        assert cpu[at-0x4000:at-0x4000+len(data)]==b'\xff'*len(data),(hex(at),len(data))
        cpu[at-0x4000:at-0x4000+len(data)]=data

    def patch(at,expected,new):
        assert len(expected)==len(new) and old[at-0x4000:at-0x4000+len(expected)]==expected,hex(at)
        assert cpu[at-0x4000:at-0x4000+len(expected)]==expected,hex(at)
        cpu[at-0x4000:at-0x4000+len(new)]=new
        patches.append(dict(address=at,old=expected.hex(),new=new.hex()));allowed.append([at,at+len(new)])

    reserve('font-run-decoder',len(decoder),s['HFDECODE']);put(s['HFDECODE'],decoder)
    patch(old_table['origin'],old[old_table['origin']-0x4000:old_table['origin']-0x4000+len(huffman_table)],huffman_table)
    # The old literal dispatcher is bypassed by CMDENTRY. Its private
    # constant and LPRINT spelling are the only live data in that span.
    quarter=reserve('XMQUARTERPI',9);put(quarter,old[s['XMQUARTERPI']-0x4000:s['XMQUARTERPI']-0x4000+9])
    refs=[i+0x4000 for i in range(len(old)-2) if old[i:i+3]==b'\xce'+s['XMQUARTERPI'].to_bytes(2,'big')]
    assert refs==[0xACED]
    patch(refs[0],b'\xce'+s['XMQUARTERPI'].to_bytes(2,'big'),b'\xce'+quarter.to_bytes(2,'big'))
    lprint_word=reserve('LPRINT-keyword',7);put(lprint_word,b'LPRINT\0')
    patch(0x82C3,s['LPNAME'].to_bytes(2,'big'),lprint_word.to_bytes(2,'big'))
    patch(s['LCDDISPATCH'],b'\x7e'+s['LPDISPATCH'].to_bytes(2,'big'),b'\x7e'+s['CMDENTRY'].to_bytes(2,'big'))
    s.update(XMQUARTERPI=quarter,LPNAME=lprint_word)
    s.update({k:v for k,v in new_hf.items() if k.startswith('HF')})

    parts=re.split(r'; @island \w+\n',(ROOT/'src/paper-list.inc').read_text())
    local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b','\n'.join(parts),re.M))
    labels={k:0x4000 for k in local};definitions={k:v for k,v in s.items() if k not in local}
    def link(i,at):
        body=parts[i];own=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
        defs=definitions|{k:v for k,v in labels.items() if k not in own}
        return assemble('llist-'+str(i),' OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in defs.items())+f' ORG ${at:04X}\n'+body)
    locations={}
    for i,pin in [(0,s['RLIST']),(3,s['SAVECMD']),(1,None),(2,None)]:
        data,_=link(i,pin or 0x4000);at=reserve('llist-'+str(i),len(data),pin)
        data,ls=link(i,at);locations[i]=at
        labels.update({k:v for k,v in ls.items() if k in local})
    for i,at in locations.items():data,_=link(i,at);put(at,data)
    word=reserve('llist-keyword',6);put(word,b'LLIST\0')
    table=reserve('llist-command-table',8)
    put(table,word.to_bytes(2,'big')+labels['LLIST'].to_bytes(2,'big')+b'\0'*4)
    # Last table's null link now names the single new command table.
    p=s['CMDTABLE'];seen=set();list_entry=None
    while p:
        assert p not in seen;seen.add(p)
        key=int.from_bytes(old[p-0x4000:p-0x4000+2],'big')
        handler=int.from_bytes(old[p-0x4000+2:p-0x4000+4],'big')
        if not key:
            if not handler:
                patch(p+2,b'\0\0',table.to_bytes(2,'big'));break
            p=handler;continue
        if key==oldlist:list_entry=p
        p+=4
    assert list_entry is not None
    # LIST shares the suffix of LLIST, recovering its old five-byte spelling.
    for at,oldkey,newkey in [(help_ptr,oldhelp,word),(list_ptr,oldlist,word+1),(list_entry,oldlist,word+1)]:
        patch(at,oldkey.to_bytes(2,'big'),newkey.to_bytes(2,'big'))
    patch(s['LISTACK'],b'\x7e'+s['RLACK'].to_bytes(2,'big'),b'\x7e'+labels['RLACK'].to_bytes(2,'big'))
    # Pack the lossless run-coded glyph streams and relocate their descriptors.
    packing=[r[:] for r in free]
    for seed in range(2000):
        pending=[r for r in glyphs if r['bytes']];random.Random(seed).shuffle(pending)
        free=[r[:] for r in packing];placed=[]
        for i in sorted(range(len(free)),key=lambda i:free[i][1]-free[i][0]):
            a,b=free[i];choices={0:[]}
            for j,r in enumerate(pending):
                for n,selection in sorted(list(choices.items()),reverse=True):
                    nn=n+r['bytes']
                    if nn<=b-a and nn not in choices:choices[nn]=selection+[j]
            chosen=choices[max(choices)]
            for j in chosen:
                r=pending[j];placed.append(dict(r,origin=a));a+=r['bytes']
            pending=[r for j,r in enumerate(pending) if j not in chosen];free[i]=[a,b]
        if not pending:break
    assert not pending,[(r['name'],r['bytes']) for r in pending]
    for r in placed:
        put(r['origin'],streams[r['name']])
    places={r['name']:r for r in placed}
    for r in glyphs:
        if not r['bytes']:places[r['name']]=dict(r,origin=new_hf['HFZERO'])
    index=b''.join(places[f'font-glyph-{ch:02x}']['origin'].to_bytes(2,'big')+bytes([places[f'font-glyph-{ch:02x}']['bytes']]) for ch in range(32,127))
    patch(s['HFGLYPHS'],old[s['HFGLYPHS']-0x4000:s['HFGLYPHS']-0x4000+285],index)
    banner=b'Typestar BASIC 0.4.87-dev';at=old.index(banner)+0x4000
    patch(at,banner,b'Typestar BASIC 0.4.88-dev')
    assert len(cpu)==32768
    assert all(x==y or any(a<=i+0x4000<b for a,b in allowed) for i,(x,y) in enumerate(zip(old,cpu)))
    m['font_allocations']=[r for r in m['font_allocations'] if not r['name'].startswith('font-glyph-')]+list(places.values())
    next(r for r in m['font_allocations'] if r['name']=='font-huffman-table')['bytes']=len(huffman_table)
    m['font_data_bytes']=sum(r['bytes'] for r in places.values())+285+len(huffman_table)
    m['font_code_bytes']+=len(decoder)-len(old_decoder)
    for row in m.get('ascii_allocations',[]):
        if row['name']=='font-zero-suffix':row['origin']=new_hf['HFZERO']
    m['font_decoder_scratch_bytes']=26
    m['font_scratch']=[s['HFSTATE'],s['HFSTATE']+26]
    next(r for r in m['extension_allocations'] if r['name']=='XMQUARTERPI')['origin']=quarter
    m['native_allocations']=[r for r in m['native_allocations'] if r['name'] not in ('native-word-4','native-word-10')]
    m['native_allocations'] += [dict(name='native-word-10',origin=word,bytes=6),dict(name='native-word-4',origin=word+1,bytes=0)]
    for row in m['command_dispatch']:
        if row['name']=='LIST':row['key']=word+1
        if row['name']=='LPRINT':row['key']=lprint_word
    m['command_dispatch'].append(dict(name='LLIST',key=word,handler=labels['LLIST']))
    free=[r for r in free if r[0]<r[1]];count=sum(b-a for a,b in free)
    m.update(version='0.4.88-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='LLIST candidate; validation pending',
             explicit_free_regions=free,explicit_free_bytes=count,
             known_free_fragmented_bytes=m['known_free_fragmented_bytes']-m.get('explicit_free_bytes',75)+count,
             llist_allocations=alloc,llist_patches=patches,llist_token=138,llist_retired_regions=retired,
             llist_max_columns=69,font_descriptor_bytes=3,font_index_bytes=285,
             font_run_stream_bytes=sum(map(len,streams.values())),font_run_decoder_bytes=len(decoder),font_run_threshold=12,
             llist_scratch='Existing LIST/SAVE pointers and LPRINT 72-byte buffer; no persistent RAM')
    # Preserve the historical untracked eleven-byte reserve in the statistics.
    m['known_free_fragmented_bytes']=count+11
    s.update(labels);s.update(LLISTWORD=word,LLISTTABLE=table,LLISTTOKEN=138)
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    (OUT/'font-expected.json').write_text(json.dumps({k:v.hex() for k,v in expected.items()},indent=2)+'\n')
    (ROOT/'studio/internal/profiles/basic-0.4.88-symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    print(json.dumps(dict(version=m['version'],sha256=m['sha256'],free=count,allocations=alloc,packing_seed=seed),indent=2))

if __name__=='__main__':main()
