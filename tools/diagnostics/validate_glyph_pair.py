"""Actual-ROM regressions for .94: legacy modes/repeats, shared unpacker and font."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools')]
from emulator_worker import backend
from native_program import WORDS

MASK=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin'
OUT=ROOT/'build/glyph-pair'


def run_to(c,predicate,limit=8000000):
    for steps in range(limit):
        if predicate(c):return steps
        c.step()
    raise AssertionError(('timeout',hex(c.pc),c.screen()))


def draw(C,rows,w,mode,repeat=0,matrix=False,stop=False,instant=False):
    c=C('10 DIM G(495)\n20 END');c.instant_paper=instant;s=c.symbols
    run_to(c,lambda c:c.word(s['RLINE'])==20)
    address=c.word(s['PEND'])+10
    values=[int(bool(row&(1<<(w-1-x)))) for row in rows for x in range(w)] if matrix else [v for row in rows for v in (row>>16,row&65535)] if w==32 else rows
    for i,value in enumerate(values):c.m[address+5*i:address+5*i+5]=bytes.fromhex(f'{value:08d}00')
    c.putword(s['SGSRC'],address);c.putword(s['SGENDPTR'],address+5*len(values))
    c.m[s['SGWIDTH']]=w;c.m[s['SGHEIGHT']]=len(rows);c.m[s['SGZOOM']]=mode
    c.m[s['SGRANK']]=(1 if matrix else 0) if 'SGPAIR' in s else (2 if matrix else 1)
    c.m[s['SGACTIVE']]=c.m[s['LPMODE']]=0
    if 'SGREPEAT' in s:c.m[s['SGREPEAT']]=repeat
    outw=4*w-1 if mode==4 else w*(1 if mode==1 else 2)
    tiles=outw//32+1;reserve=64*tiles+220
    c.putword(s['DHEAP'],c.word(s['DFLOOR'])+reserve)
    c.sp=0x1fff;c.push(0xEF);c.push(0x3F);c.pc=s['SGSTAGE']
    motions=[];injected=False
    for steps in range(8000000):
        if c.pc==0x3fef:break
        if c.pc==s['GPCALL']:motions.append((c.x,c.word(0xBA),c.word(0xB8)))
        if stop and c.pc==s.get('SGPRINT') and c.tiles==2 and not injected:
            if stop=='logical':c.break_requested=True
            else:c.matrix_keys={0x36}
            injected=True
        if c.pc==s['RBPAPERERROR']:
            assert stop and injected and c.a==8
            break
        assert c.pc not in (s['RANGEERROR'],s['SYNTAX']),hex(c.pc)
        c.step()
    else:raise AssertionError(('draw timeout',w,mode,repeat,hex(c.pc)))
    assert c.m[s['SGACTIVE']]==c.m[s['GPRAN']]==0
    # Initial homing is outside the calibrated origin in the functional model.
    events=[(x,y,b) for x,y,b in c.paper_events if b]
    x0=min((x for x,y,b in events),default=0);y0=min((y for x,y,b in events),default=0)
    events=[(x-x0,y-y0,b) for x,y,b in events]
    return dict(steps=steps,tiles=c.tiles,events=events,motions=motions,
                reserve=reserve,stopped=injected,sp=c.sp)


def main():
    old=ROOT/'firmware/0.4.93-dev/typestar-basic-32k.bin'
    candidate=OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin'
    cases=[([1],1,1,False),([65535]*16,16,1,False),
           ([1<<i for i in range(16)],16,2,False),
           ([32769,0,12345,65535,1,32768,2,4,8],16,3,False),
           ([((1<<31)-1)^(1<<i) for i in range(16)],31,2,True),
           ([1,2,4,8,16,32,64],7,3,False)]
    cache=OUT/'partial-validation.json'
    saved=json.loads(cache.read_text()) if cache.exists() else None
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    if saved and saved['sha256']==digest:
        repeats=saved['repeats']
    else:
        baseline=backend(mask_path=MASK,firmware_path=old)
        golden=[draw(baseline,*row[:3],matrix=row[3]) for row in cases]
        C=backend(mask_path=MASK,firmware_path=candidate);s=C.symbols
        for i,row in enumerate(cases):
            got=draw(C,*row[:3],matrix=row[3])
            assert got['events']==golden[i]['events'],('legacy pixels',i)
            assert got['tiles']==golden[i]['tiles']
        print('PASS six legacy packed/matrix/mode cases',flush=True)
        repeats=[]
        for rows,w,count,matrix in [([65535]*16,16,10,False),([0x8001]*16,16,3,False),
                                    ([1],1,16,False),([(1<<31)-1]*3,31,2,True)]:
            got=draw(C,rows,w,4,count,matrix)
            pitch=((4*w-1)//32+1)*32
            expected=[]
            for band in range((len(rows)*2+15)//16):
                for rep in range(count):
                    for x in range(pitch):
                        if x%32==31 or x>=4*w:continue
                        bits=sum(1<<(4+y) for y in range(16)
                                 if (band*16+y)//2<len(rows) and rows[(band*16+y)//2]&(1<<(w-1-x//4)))
                        if bits:expected.append((rep*pitch+x,112*band,bits))
            assert got['events']==expected,('repeat pixels',w,count,got['events'][:5],expected[:5])
            head_returns=[v for v in got['motions'] if v[0]==0x716f]
            assert len(head_returns)==(len(rows)*2+15)//16
            assert all(v[1]==((-pitch*count//2)&65535) for v in head_returns)
            repeats.append(dict(width=w,repeat=count,tiles=got['tiles'],steps=got['steps'],
                                native_head_returns=len(head_returns),buffer_bytes=got['reserve']))
            print('PASS large continuous group',w,count,flush=True)
        cache.write_text(json.dumps(dict(sha256=digest,repeats=repeats))+'\n')
    C=backend(mask_path=MASK,firmware_path=candidate);s=C.symbols
    blank=draw(C,[0]*16,16,4,10)
    assert blank['tiles']==0 and not blank['events']
    stopped=draw(C,[65535]*16,16,4,10,stop=True)
    assert stopped['stopped'] and stopped['tiles']==2
    logical_stop=draw(C,[65535]*16,16,4,10,stop='logical')
    assert logical_stop['stopped'] and logical_stop['tiles']==2
    print('PASS empty bands and BREAK between repeated blocks',flush=True)
    c=C();assert c.word(s['DHEAP'])-c.word(s['DFLOOR'])==5951
    font=json.loads((ROOT/'build/paper-list/font-expected.json').read_text())
    for ch,raw in font.items():
        c.m[0x11ff:0x125e]=b'\xa5'*95;c.a=ord(ch);c.x=0x1200;c.pc=s['HFDECODE'];c.sp=0x1fff
        c.push(0xF0);c.push(0xFF)
        run_to(c,lambda c:c.pc==0xfff0,150000)
        expected=bytes.fromhex(raw)
        if 'TMDECODE' in s:expected=b''.join(expected[i:i+3][::-1] for i in range(0,93,3))
        assert c.m[0x1200:0x125d]==expected and not c.c,ch
        assert c.m[0x11ff]==c.m[0x125d]==0xa5,ch
    print('PASS all 95 unchanged paper characters',flush=True)
    image=candidate.read_bytes();manifest=json.loads((OUT/'manifest.json').read_text())
    def word(p):return int.from_bytes(image[p-0x4000:p-0x4000+2],'big')
    def string(p):
        out=[]
        while 0<image[p-0x4000]<128:out.append(image[p-0x4000]);p+=1
        return bytes(out).decode('ascii')
    assert all(string(word(s['TOKENPTRS']+2*i))==name for i,name in enumerate(WORDS))
    p=s['CMDTABLE'];seen=set();commands={}
    while p:
        assert p not in seen;seen.add(p)
        if manifest.get('command_layout')=='inline-tagged':
            if image[p-0x4000]==0:p=word(p+1);continue
            name=string(p);key=p;p+=len(name);handler=(word(p)&32767)+0x4000;p+=2
        else:
            key,handler=word(p),word(p+2)
            if not key:p=handler;continue
            name=string(key);p+=4
        commands[name]=(key,handler)
    assert commands=={v['name']:(v['key'],v['handler']) for v in manifest['command_dispatch']}
    print('PASS 37 tokens and 54 command links',flush=True)
    invalid=[]
    for args in ('16,16,4,0','16,16,4,17','16,16,4,-1','16,16,5','16,16,4,1.5'):
        c=C('10 DIM G(15)\n20 GLYPH G(0),'+args+'\n30 END')
        run_to(c,lambda c:c.pc in (s['RANGEERROR'],s['SYNTAX']),1000000)
        assert c.tiles==0 and not c.paper_events
        invalid.append(args)
    valid=C('10 DIM G(15)\n20 FOR I=0 TO 15:G(I)=65535:NEXT I\n30 GLYPH G(0),16,16,4,3\n40 PRINT 1.5*2\n50 END')
    run_to(valid,lambda c:valid.word(s['RLINE'])==50,4000000)
    assert valid.tiles==12 and '3' in valid.screen()
    wide_cases=[]
    for mode in (1,2,3,4):
        rows=[0x80010001 ^ ((0x1100+i)<<8) for i in range(16)]
        got=draw(C,rows,32,mode)
        scale=1 if mode==1 else 4 if mode==4 else 2
        sy=2 if mode in (2,4) else 1
        expected=[];physical=0
        for band in range((16*sy+15)//16):
            physical=0
            for col in range(32*scale):
                if mode==4 and col%32==31:continue
                if physical%32==31:physical+=1
                bits=sum(1<<(4+y) for y in range(16)
                         if (band*16+y)//sy<16 and rows[(band*16+y)//sy]&(1<<(31-col//scale)))
                if bits:expected.append((physical,112*band,bits))
                physical+=1
        assert got['events']==expected,('wide pixels',mode,len(got['events']),len(expected),next(((a,b) for a,b in zip(got['events'],expected) if a!=b),None),got['events'][-3:],expected[-3:])
        fast=draw(C,rows,32,mode,instant=True)
        assert fast['events']==got['events'] and fast['tiles']==got['tiles'], ('instant paper',mode)
        wide_cases.append(dict(mode=mode,tiles=got['tiles'],steps=got['steps'],instant_steps=fast['steps']))
    # Public parser, second-word validation, end-of-array and unsupported widths.
    c=C('10 DIM G(31)\n20 FOR I=0 TO 15:G(2*I)=32769:G(2*I+1)=255:NEXT I\n30 GLYPH G(0),32,16,4\n40 END')
    run_to(c,lambda c:c.word(s['RLINE'])==40,4000000)
    assert c.tiles==8
    for body in ('DIM G(30):GLYPH G(0),32,16,4',
                 'DIM G(31):G(1)=65536:GLYPH G(0),32,16,4',
                 'DIM G(31):G(1)=-1:GLYPH G(0),32,16,4',
                 'DIM G(31):GLYPH G(0),17,16,4',
                 'DIM G(31):GLYPH G(0),33,16,4'):
        c=C('10 '+body+'\n20 END')
        run_to(c,lambda c:c.pc in (s['RANGEERROR'],s['SYNTAX']),1000000)
        assert c.tiles==0 and not c.paper_events,body
    matrix_rows=[0x80010001,0xf00f000f,0x11111111]
    assert draw(C,matrix_rows,32,4,matrix=True)['events']==draw(C,matrix_rows,32,4)['events']
    assert draw(C,[0]*16,32,4)['tiles']==0
    assert draw(C,[0xffffffff]*16,32,4,stop=True)['stopped']
    print('PASS wide rows: four modes, parser, bounds, invalid cells, blank and BREAK',flush=True)
    report=dict(result='PASS',sha256=hashlib.sha256(image).hexdigest(),legacy_cases=len(cases),
                wide_cases=wide_cases,continuous_cases=repeats,font_characters=95,tokens=37,commands=54,
                break_cleanup=True,blank_skip=True,invalid_no_motion=invalid,
                public_syntax_and_decimal=True,free_basic_bytes=5951,
                scope='Actual ROM routines and representative interpreter runs; physical validation pending')
    (OUT/('validation.json' if OUT.name=='glyph-pair' else 'graphics-validation.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    if '--build' in sys.argv:OUT=ROOT/'build'/sys.argv[sys.argv.index('--build')+1]
    main()
