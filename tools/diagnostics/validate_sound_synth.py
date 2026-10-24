"""Execute .95's real parser, compiler and waveform opcodes; check prior data."""
from pathlib import Path
import argparse,hashlib,json,random,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools/diagnostics')]
from emulator_worker import backend
from validate_buzzer_survey_v3 import TimedCPU,CRITICAL_CYCLES
from hd6301 import HD6301CPU
OUT=ROOT/'build/sound-synth'
MASK=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin'

def run(c,stop,limit=2500000):
    for n in range(limit):
        if stop(c):return n
        c.step()
    raise AssertionError(('timeout',hex(c.pc),getattr(c,'screen',lambda:'')()))

def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--build',default='sound-synth')
    OUT=ROOT/'build'/parser.parse_args().build
    image=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();s=json.loads((OUT/'symbols.json').read_text())
    continuous=bool(s.get('SNDCONTINUOUS'));noise_reserve=672 if continuous else 512
    C=backend(mask_path=MASK,firmware_path=OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin')
    c=C();assert c.word(s['DHEAP'])-c.word(s['DFLOOR'])==5951
    # All native glyph bytes and both guard bytes must match the original font.
    for ch,raw in json.loads((ROOT/'src/paper-font-reference.json').read_text()).items():
        c.m[0x11ff:0x125e]=b'\xa5'*95;c.a=ord(ch);c.x=0x1200;c.pc=s['HFDECODE'];c.sp=0x1fff;c.push(0xf0);c.push(0xff)
        run(c,lambda c:c.pc==0xfff0,180000)
        expected=bytes.fromhex(raw)
        if 'TMDECODE' in s:expected=b''.join(expected[i:i+3][::-1] for i in range(0,93,3))
        assert c.m[0x1200:0x125d]==expected and not c.c,(ch,c.m[0x1200:0x125d].hex())
        assert c.m[0x11ff]==c.m[0x125d]==0xa5,ch
    print('PASS 95 byte-identical native paper glyphs',flush=True)
    # Run the actual compact keyboard decoder, including SHIFT / layout II.
    rows=json.loads((ROOT/'src/keyboard-reference.json').read_text())
    for i,row in enumerate(rows):
        for key,want in enumerate(row):
            c.m[s['KLOCALE']]=i//4;c.m[s['KMODE']]=i//2%2;c.matrix_shift=bool(i%2)
            c.m[s['KRAW']]=key;c.pc=s['KDENTRY']
            run(c,lambda c:c.pc==s['KBDRETURN'],5000)
            assert c.a==want,(i,key,c.a,want)
    print('PASS 1760 keyboard translations',flush=True)
    # Fast bounded 24/16 division: the high byte is the initial remainder.
    t=TimedCPU(image);t.capture=False
    rng=random.Random(95)
    cases=[(1000000+f//2,f) for f in (60,100,131,750,1000,1963,5000,5889,8000,31250)]
    cases += [(rng.randrange(1,16668)*rng.randrange(1,100),100) for _ in range(150)]
    for numerator,divisor in cases:
        t.m[s['SNDHIGH']]=numerator>>16;t.putword(s['SNDWIDE'],numerator&65535);t.putword(s['SNDDIVISOR'],divisor)
        t.sp=0x1fff;t.enter(s['SNDDIV']);t.run_until_return()
        assert t.x==numerator//divisor,(numerator,divisor,t.x)
    print('PASS 160 divisions',flush=True)
    class SoundCPU(TimedCPU):
        def __init__(self):
            super().__init__(image);self.m[:0x4000]=c.m[:0x4000];self.m[0xc000:]=MASK.read_bytes();self.edges=[]
        def write(self,address,value):
            if 0x100<=address<0x3800:
                self.m[address]=value&255;self.writes.add(address);return
            super().write(address,value)
        def step(self):
            if continuous and 0x100<=self.word(s['SNDBASE'])<=self.pc<self.word(s['SNDWRITE'])<=0x3800:
                cycles=CRITICAL_CYCLES|{0x86:2,0xcc:3,0x83:3}
                op=self.m[self.pc];assert op in cycles,hex(op)
                HD6301CPU.step(self);self.time+=cycles[op];return
            if self.pc==s['RFASTBREAK']:
                self.a=0x40;self.z=False;self.pc=self.pop()*256+self.pop();self.time+=35;return
            super().step()
    checks=[]
    for f,duty,wave in [(50,1,0),(50,99,0),(60,50,0),(131,20,0),(750,50,0),(1963,10,0),(1963,90,0),(5000,50,0),(5889,50,0),(8000,33,0),(31250,50,0),(31250,1,0),(31250,99,0),(1000,50,1),(2000,50,1),(8000,50,1),(31250,50,1)]:
        t=SoundCPU();t.m[0x1801]=0x91;t.putword(s['SNDHZ'],f);t.putword(s['SNDLEFT'],80);t.m[s['SNDMODE']]=3 if wave else 1;t.m[s['SNDDUTY']]=duty
        t.sp=0x1fff;t.enter(s['SNDPREP']);run(t,lambda t:t.pc==s['SNDPLAYPREP'])
        base=t.word(s['SNDBASE']);end=t.word(s['SNDWRITE']);period=round(1000000/f)
        assert end-base<= (noise_reserve if wave else 64),(f,duty,wave,end-base)
        memory=bytes(t.m[0x2000:0x3800]);heap=t.word(s['DHEAP']);floor=t.word(s['DFLOOR'])
        # Exact timing across three complete generated periods/patterns.
        t.time=0;t.edges=[];t.pc=base;t.sp=0x1fff;t.push(0xff);t.push(0x3f);t.b=3
        if continuous:t.x=3
        cycles=CRITICAL_CYCLES|{0x86:2,0xce:3,0x5a:1,0xcc:3,0x83:3,0x18:2}
        while t.pc!=0x3fff:
            op=t.m[t.pc];assert op in cycles,(hex(t.pc),hex(op))
            HD6301CPU.step(t);t.time+=cycles[op]
        width=31 if wave else 1
        expected=width*period
        assert t.edges[width*(1 if wave else 2)][0]-t.edges[0][0]==expected,(f,wave,t.edges[:4],expected)
        assert all((value&~64)==0x91 for _,value in t.edges)
        if not wave:
            on=max(5,min(period-12,round(period*duty/100) if continuous else period*duty//100))
            assert t.edges[1][0]-t.edges[0][0]==on,(f,duty,on,t.edges[:4])
        else:
            state=31;bits=[]
            for _ in range(31):bits.append(state&1);state=(state>>1)|(((state^(state>>2))&1)<<4)
            assert [bool(v&64) for _,v in t.edges[:31]]==list(map(bool,bits)),(f,t.edges[:31],bits)
        # Real foreground duration loop, including timer wrap and cleanup.
        t.time=65000;t.edges=[];t.pc=s['SNDPLAYPREP'];t.sp=0x1fff;t.push(0xff);t.push(0x3f)
        run(t,lambda t:t.pc==0x3fff)
        elapsed=t.time-65000
        if continuous:
            # Foreground functional timing is approximate outside the kernel.
            expected=max(1,80000//expected)*expected
            assert abs(elapsed-expected)<5000,(f,wave,elapsed,expected)
        else:assert 80000<=elapsed<=115000,(f,wave,elapsed)
        assert not t.m[0x34]&64 and t.m[0x1801]==0x91
        assert t.word(s['DHEAP'])==heap and t.word(s['DFLOOR'])==floor and bytes(t.m[0x2000:0x3800])==memory
        checks.append(dict(rate=f,duty=duty,wave=wave,kernel_bytes=end-base,elapsed_us=elapsed))
    print('PASS generated square/noise timing, duration, timer wrap, RAM and gate cleanup',flush=True)
    # Real BASIC expressions, optional arguments, colons and error paths.
    parser=[]
    for command in ('BEEP','BEEP 20','BEEP 0:PRINT 7','SOUND 0,30','SOUND 50,10','SOUND 60,10','SOUND 31250,20,99',
                    'SOUND 8000,40,50,1','SOUND 5500,40,10,0','SOUND 5000+500,10+10,25*2'):
        c=C();c.command(command)
        assert not c.screen().startswith('?'),(command,c.screen())
        parser.append(command)
    for command in ('SOUND 49,10','SOUND 31251,10','SOUND -60,10','SOUND 100,2001',
                    'SOUND 100,10,0','SOUND 100,10,100','SOUND 100,10,50,2',
                    'SOUND 999,10,50,1','SOUND 100,10,50,1,2','BEEP 2001'):
        c=C('10 '+command+'\n20 END')
        run(c,lambda c:c.pc in (s['RANGEERROR'],s['SYNTAX']))
        assert not c.sounds,command
    # Noise refuses insufficient free heap before writing its RAM kernel.
    t=SoundCPU();t.putword(s['SNDHZ'],8000);t.putword(s['SNDLEFT'],80);t.m[s['SNDMODE']]=3
    t.putword(s['DHEAP'],t.word(s['DFLOOR'])+noise_reserve-1);before=bytes(t.m[0x2000:0x3800]);t.pc=s['SNDPREP'];t.edges=[]
    run(t,lambda t:t.pc==s['PMEMERROR'])
    assert not t.edges and bytes(t.m[0x2000:0x3800])==before
    # A physical BREAK cleans the known gate, then uses the normal BASIC route.
    t=SoundCPU();t.putword(s['SNDHZ'],5889);t.putword(s['SNDLEFT'],2000);t.m[s['SNDDUTY']]=50;t.m[s['SNDMODE']]=1;t.m[0x1801]=0x91
    if continuous:
        # No keyboard poll during sound; physical BREAK resumes in BASIC.
        t.keys={0x36};t.enter(s['SNDPREP']);run(t,lambda t:t.pc==0x3fff)
    else:
        t.pc=s['SNDPREP'];run(t,lambda t:t.pc==s['RFASTBREAK']);t.z=True;t.pc=t.pop()*256+t.pop()
        run(t,lambda t:t.pc==s['BREAK'])
    assert t.m[0x1801]==0x91 and not t.m[0x34]&64
    print('PASS BASIC parser, errors, free-heap guard and BREAK cleanup',flush=True)
    # Host input mapping must agree with all physical keyboard maps.
    for locale in range(10):
        c=C();c.m[s['KLOCALE']]=locale
        for value in set(rows[locale*4]+rows[locale*4+1])-{0}:
            result=c.key_position(value);assert result is not None,(locale,value)
            key,shift=result;assert rows[locale*4+int(shift)][key]==value
    # Drive every synth mode and all parameter controls through INKEY.
    piano=[]
    for language in ('fr','en'):
        c=C((ROOT/f'examples/piano-{language}.bas').read_text(encoding='utf-8'))
        c.idle();assert 'PIANO' in c.screen()
        for mode in range(9):
            c.held_key=ord('A');run(c,lambda c:c.pc==s['SNDPLAYPREP'])
            count=len(c.sounds);c.held_key=0;c.step();run(c,lambda c:c.pc==0x8ee6)
            assert len(c.sounds)>count
            c.held_key=19;run(c,lambda c:c.pc==0x8ef0);c.step();c.held_key=0
            run(c,lambda c:c.pc==0x8ee6)
        if 'TMDECODE' in s:
            count=len(c.sounds);c.held_key=32;run(c,lambda c:c.pc==s['SNDPLAYPREP'])
            c.held_key=0;c.step();run(c,lambda c:c.pc==0x8ee6,5000000)
            assert c.sounds[count:]==[(v,320) for v in (5365,5301,5229,5190,5105,5009,4901,4842)]
        c.held_key=13;run(c,lambda c:c.pc==0x8ef0);c.step();c.held_key=0;c.idle()
        piano.append(dict(language=language,sound_commands=len(c.sounds)))
    print('PASS Piano FR/EN, all nine modes and host key mapping',flush=True)
    result=dict(result='PASS',sha256=hashlib.sha256(image).hexdigest(),font_characters=95,keyboard_cases=1760,divisions=len(cases),sound_cases=checks,free_basic_bytes=5951)
    result.update(parser_cases=len(parser)+10,noise_heap_guard=True,break_cleanup=True,piano=piano,
                  continuous_sound=continuous,noise_temporary_bytes=noise_reserve)
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
