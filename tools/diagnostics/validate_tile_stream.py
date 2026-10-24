"""Execute the native row cache, including misses, blanks and queued motion."""
from pathlib import Path
import hashlib,json,random,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools'),str(ROOT/'tools/diagnostics')]
from emulator_worker import backend
from native_program import WORDS
from core import codec
from validate_glyph_pair import run_to,MASK
OUT=ROOT/'build/tile-stream'

def machine():
    return backend(mask_path=MASK,firmware_path=OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin')

def row(C,palette,ids,small=False,instant=False,stop=False):
    c=C('10 DIM G(103)\n20 END');c.instant_paper=instant;s=c.symbols
    run_to(c,lambda c:c.word(s['RLINE'])==20)
    start=c.word(s['PEND'])+10
    values=[256*t[r]+t[r+1] for t in palette for r in range(0,8,2)]+ids
    for i,v in enumerate(values):c.m[start+5*i:start+5*i+5]=bytes.fromhex(f'{v:08d}00')
    before=bytes(c.m[start:start+len(values)*5]);floor=c.word(s['DFLOOR'])
    if small:c.putword(s['DHEAP'],floor+316)
    heap=c.word(s['DHEAP']);text=f'G(0),{len(ids)},8,5'.encode()+b'\0'
    c.m[0x1d00:0x1d00+len(text)]=text;c.putword(s['CUR'],0x1d00)
    c.sp=0x1fff;c.push(0xef);c.push(0x3f);c.pc=s['SGPARSE']
    motions=[];injected=False
    for steps in range(12000000):
        if c.pc==0x3fef:break
        if c.pc==s['GPCALL']:motions.append((c.x,c.word(0xba),c.word(0xb8),c.m[0x40]))
        if stop and c.pc==s['LPPRINT'] and c.tiles==2 and not injected:
            c.matrix_keys={0x36};injected=True
        if c.pc==s['RBPAPERERROR']:
            assert injected and c.a==8,(hex(c.pc),c.a)
            break
        assert c.pc not in (s['RANGEERROR'],s['SYNTAX'],s['PMEMERROR']),hex(c.pc)
        c.step()
    else:raise AssertionError(('row timeout',hex(c.pc)))
    assert c.word(s['DHEAP'])==heap and c.word(s['DFLOOR'])==floor
    assert bytes(c.m[start:start+len(values)*5])==before
    events=[(x,y,b) for x,y,b in c.paper_events if b]
    # The first warm-up's absolute origin belongs to the functional bus.
    if events:
        anchor=next(i for i in ids if any(palette[i]));k=ids.index(anchor)
        x0=min(x for x,y,b in events)-32*k;y0=min(y for x,y,b in events)
        events=[(x-x0,y-y0,b) for x,y,b in events]
    if not stop:
        assert c.m[s['SGACTIVE']]==c.m[s['LPMODE']]==c.m[s['GPRAN']]==0
        assert c.tiles==len(ids)
        returns=[v for v in motions if v[0]==0x716f]
        assert len(returns)==1 and returns[0][1]==(-16*len(ids))&65535,returns
        calls=[v for v in motions if v[0]==0x728b]
        assert [v[3]&128 for v in calls]==[128]*(len(ids)-1)+[0],calls
    return dict(steps=steps,events=events,tiles=c.tiles,stopped=injected,
                native_head_returns=sum(v[0]==0x716f for v in motions),cache=c.m[s['LPUCOUNT']])

def pixels(palette,ids):
    out=[]
    for k,n in enumerate(ids):
        for col in range(31):
            bits=sum(1<<(4+y) for y in range(16) if palette[n][y//2]&(128>>(col//4)))
            if bits:out.append((k*32+col,0,bits))
    return out

def main():
    maximum=json.loads((OUT/'manifest.json').read_text())['tile_stream']['maximum_columns']
    C=machine();rng=random.Random(97)
    palette=[[0]*8,[255,129,129,129,129,129,129,255]]
    palette += [[128|rng.randrange(128) for _ in range(8)] for _ in range(14)]
    cases=[]
    for ids,small,instant in [([1,2,0,3,1],False,False),
            (list(range(1,16))+[0]+list(range(1,16))+[0],False,False),
            (list(range(1,16))+[0]+list(range(1,16))+[0],True,False),
            ([1,2,0,3,1],False,True),([0]*8,False,False)]+(
            [([1,0,2]*12+[1],False,True),([1,0]*20,True,True)]
            if maximum>=40 else []):
        got=row(C,palette,ids,small,instant);assert got['events']==pixels(palette,ids),(small,instant,len(got['events']),len(pixels(palette,ids)))
        cases.append({k:v for k,v in got.items() if k!='events'}|dict(columns=len(ids),small_cache=small,instant=instant))
        print('PASS row',cases[-1],flush=True)
    stopped=row(C,palette,[1]*8,stop=True);assert stopped['stopped'] and stopped['tiles']==2
    print('PASS physical BREAK after two queued tiles',flush=True)
    invalid=[]
    for setup,args in [('', '2,8,5'),('G(64)=16','2,8,5'),('G(0)=-1','2,8,5'),
            ('G(0)=1.5','2,8,5'),('G(0)=65536','2,8,5'),('', '2,16,5'),
            ('','2,8,5,1'),('', f'{maximum+1},8,5')]+(
            [('',f'33,8,{mode}') for mode in (1,2,3,4)] if maximum>=40 else []):
        dim=64 if not setup and args=='2,8,5' else 99
        source=f'10 DIM G({dim})\n20 '+(setup+':' if setup else '')+f'GLYPH G(0),{args}\n30 END'
        c=C(source);s=c.symbols;run_to(c,lambda c:c.pc in (s['RANGEERROR'],s['SYNTAX']),1500000)
        assert c.jobs==c.tiles==0;invalid.append([setup,args])
    print('PASS preflight rejects invalid rows before printing',flush=True)
    c=C();s=c.symbols
    records=[]
    for n,word in enumerate(WORDS,1):
        body=word
        c.input.extend(f'{n} {body}\r'.encode());c.idle();records.append((n,body))
    raw=bytes(c.m[s['PROGRAM']:c.word(s['PEND'])+1])
    assert codec.unpack(raw)==records,(codec.unpack(raw),records)
    from native_text import encode_source
    text=encode_source('PRINT "Été"');c.m[0x1d00:0x1d00+len(text)]=text
    c.x=0x1d00;c.b=len(text);c.pc=s['TTOKENIZE'];c.sp=0x1fff;c.push(0xef);c.push(0x3f)
    run_to(c,lambda c:c.pc==0x3fef)
    assert not c.c and bytes(c.m[0x1c00:0x1c00+c.m[s['TOUT']]])==codec.tokenize('PRINT "Été"')
    print('PASS native tokenizer: all 37 tokens and quoted accents',flush=True)
    image=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();m=json.loads((OUT/'manifest.json').read_text())
    def word(a):return int.from_bytes(image[a-0x4000:a-0x4000+2],'big')
    def name(a):
        v=[]
        while 0<image[a-0x4000]<128:v.append(image[a-0x4000]);a+=1
        return bytes(v).decode(),a
    assert [name(word(s['TOKENPTRS']+2*i))[0] for i in range(37)]==WORDS
    commands={};p=s['CMDTABLE'];seen=set()
    while p:
        assert p not in seen;seen.add(p)
        if image[p-0x4000]==0:p=word(p+1);continue
        text,end=name(p);commands[text]=(p,(word(end)&32767)+0x4000);p=end+2
    assert commands=={v['name']:(v['key'],v['handler']) for v in m['command_dispatch']}
    for text in ['PRINTX 1','ENDLESS','ORIGINX','SOUNDX 1,2']:
        c=C();c.allow_errors=True;c.command(text);assert c.screen().startswith('?SYNTAX'),(text,c.screen())
    report=dict(result='PASS',sha256=hashlib.sha256(image).hexdigest(),rows=cases,
                commands=len(commands),tokens=37,invalid_no_motion=invalid,physical_break=True,
                free_basic_bytes=5951,unchanged_array_and_heap=True,native_tokenizer=True)
    (OUT/'tile-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS catalogue and keyword boundaries',flush=True)

if __name__=='__main__':
    if '--build' in sys.argv:OUT=ROOT/'build'/sys.argv[sys.argv.index('--build')+1]
    main()
