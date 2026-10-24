"""Check uninterrupted .98 playback, v3 plateaus, counters and RAM limits."""
from pathlib import Path
import hashlib
import json
import random
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools/diagnostics')]
from emulator_worker import backend
from hd6301 import HD6301CPU
from validate_buzzer_survey_v3 import CRITICAL_CYCLES,TimedCPU
from validate_sound_synth import MASK,run

OUT=ROOT/'build/sound-continuous'
CYCLES=CRITICAL_CYCLES|{0x86:2,0xcc:3,0x83:3}


def main():
    image=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    s=json.loads((OUT/'symbols.json').read_text())
    boot=backend(mask_path=MASK,firmware_path=OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin')()

    class CPU(TimedCPU):
        def __init__(self):
            super().__init__(image)
            self.m[:0x4000]=boot.m[:0x4000]
            self.m[0xc000:]=MASK.read_bytes()
            self.polls=[]
            self.kernel=None

        def read(self,address):
            if address in (9,10,0x30,0x32):self.polls.append(address)
            return super().read(address)

        def write(self,address,value):
            if 0x100<=address<0x3800:
                self.m[address]=value&255
                return
            super().write(address,value)

        def step(self):
            if self.kernel and self.kernel[0]<=self.pc<self.kernel[1]:
                op=self.m[self.pc]
                assert op in CYCLES,hex(op)
                HD6301CPU.step(self)
                self.time+=CYCLES[op]
            else:super().step()

    def prepare(rate,duty=50,mode=1,ms=320):
        c=CPU();c.m[0x1801]=0x91
        c.putword(s['SNDHZ'],rate);c.putword(s['SNDLEFT'],ms)
        c.m[s['SNDDUTY']]=duty;c.m[s['SNDMODE']]=mode
        c.enter(s['SNDPREP']);run(c,lambda c:c.pc==s['SNDPLAYPREP'])
        c.kernel=(c.word(s['SNDBASE']),c.word(s['SNDWRITE']))
        return c

    # All eight notes must repeat the very same plateaus as standalone v3.
    manifest=json.loads((ROOT/'build/buzzer-survey-v3/manifest.json').read_text())
    waves={w['label']:w for w in manifest['waves']}
    section=next(row for row in manifest['sections'] if row['id']==502)
    ref=[]
    for rate,row in zip((5365,5301,5229,5190,5105,5009,4901,4842),section['runs']):
        c=prepare(rate)
        c.pc=c.kernel[0];c.sp=0x1fff;c.enter(c.pc);c.x=100
        c.time=0;c.edges=[]
        run(c,lambda c:c.pc==0x3fff)
        expected=waves[row['wave']]['states'];period=row['period_cycles']
        assert len(c.edges)==200
        for n in range(99):
            assert c.edges[2*n+1][0]-c.edges[2*n][0]==expected[0][1]
            assert c.edges[2*n+2][0]-c.edges[2*n+1][0]==expected[1][1]
            assert c.edges[2*n+2][0]-c.edges[2*n][0]==period
        ref.append(dict(rate=rate,period_cycles=period,on_cycles=expected[0][1],continuous_periods=100))
    print('PASS eight v3 reference waveforms, 100 uninterrupted periods each',flush=True)

    # Actual count arithmetic, including byte carries and the 2-second limit.
    rng=random.Random(98)
    durations=sorted(set([1,2,7,25,80,255,256,257,320,511,512,1000,1999,2000]+
                         [rng.randrange(1,2001) for _ in range(80)]))
    counters=[]
    c=CPU()
    for rate,mode in [(50,1),(53,1),(131,1),(1963,1),(4842,1),(5365,1),
                      (5889,1),(31250,1),(1000,3),(1001,3),(8000,3),(31250,3),
                      (1000,0),(1000,64)]:
        period=round(1000000/rate);cycle=period*(31 if mode==3 else 1)
        for ms in durations:
            c.sp=0x1fff;c.enter(s['SNDPLAYPREP'])
            c.putword(s['SNDPER'],period);c.putword(s['SNDLEFT'],ms)
            c.putword(s['SNDBASE'],0x1400);c.m[s['SNDMODE']]=mode
            run(c,lambda c:c.pc==s['SNDCALL'],2000)
            assert c.x==max(1,ms*1000//cycle),(rate,mode,ms,c.x,cycle)
            assert c.x*cycle<=max(ms*1000,cycle)
            assert c.word(s['SNDLEFT'])==ms
        counters.append(dict(rate=rate,mode=mode,durations=len(durations)))
    assert not c.polls,c.polls
    print('PASS duration counters and no timer/keyboard reads',flush=True)

    # Prove the compiler's worst-case size across every supported noise period.
    def emitted_delay(clocks):
        return clocks if clocks<11 else 10+(clocks-3)%8
    sizes={period:30*(4+emitted_delay(period-5))+4+emitted_delay(period-12)+7
           for period in range(32,1001)}
    assert max(sizes.values())<=672
    ram=[]
    for period in (32,39,47,125,127,255,999,1000):
        rate=round(1000000/period)
        c=prepare(rate,mode=3,ms=80)
        actual_period=c.word(s['SNDPER']);a,z=c.kernel
        assert z-a==sizes[actual_period],(period,z-a,sizes[actual_period])
        assert z-a<=672
        ram.append(dict(rate=rate,period=actual_period,kernel_bytes=z-a))
    print('PASS noise kernel size, including 651-byte worst case',flush=True)

    # Execute full playback, with a held BREAK key; every edge stays on-grid.
    playback=[]
    for rate,mode,ms in [(50,1,2000),(5365,1,320),(31250,1,2000),
                         (8000,3,80),(1000,64,2000),(0,1,80)]:
        c=prepare(rate,mode=mode,ms=ms);period=c.word(s['SNDPER'])
        actual_mode=c.m[s['SNDMODE']];cycle=period*(31 if actual_mode==3 else 1)
        count=max(1,ms*1000//cycle)
        c.keys={0x36};c.edges=[];c.polls=[];c.time=0
        before=bytes(c.m[0x2000:0x3800]);heap=c.word(s['DHEAP'])
        run(c,lambda c:c.pc==0x3fff,6000000)
        assert not c.polls,c.polls
        assert c.m[0x34]==c.m[0x1801]==0x91
        assert c.sp==0x1fff
        assert bytes(c.m[0x2000:0x3800])==before and c.word(s['DHEAP'])==heap
        if actual_mode==1:
            rises=[t for t,v in c.edges if v&64]
            assert len(rises)==count
            assert all(b-a==period for a,b in zip(rises,rises[1:])),rate
        playback.append(dict(rate=rate,mode=actual_mode,ms=ms,periods=count,
                             counted_waveform_us=count*cycle))
    print('PASS full playback, no periodic gaps, held BREAK and gate/RAM/stack cleanup',flush=True)
    # Studio follows the same deferred BREAK behavior for this ROM profile.
    C=backend(realtime_sound=True,mask_path=MASK,firmware_path=OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin')
    with patch('basic_adapter.time.monotonic',return_value=1000.) as clock:
        c=C('10 SOUND 5365,320\n20 GOTO 10')
        run(c,lambda c:bool(c.sound_until))
        deadline=c.sound_until;c.request_break()
        for _ in range(10):c.step()
        assert c.sound_until==deadline and c.break_requested
        assert not any(e.get('stop') for e in c.audio_events)
        clock.return_value=deadline+.001
        run(c,lambda c:c.pc==s['BREAK'],100000)
        assert len(c.sounds)==1 and not c.sound_until
    print('PASS Studio defers BREAK until the sound ends',flush=True)
    report=dict(result='PASS',sha256=hashlib.sha256(image).hexdigest(),
                v3_reference=ref,counter_cases=counters,
                noise_periods_checked=len(sizes),noise_max_kernel_bytes=max(sizes.values()),
                noise_temporary_bytes=672,noise_buffers=ram,playback=playback,
                keyboard_timer_reads_during_sound=0,studio_deferred_break=True)
    (OUT/'continuous-validation.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    if '--build' in sys.argv:OUT=ROOT/'build'/sys.argv[sys.argv.index('--build')+1]
    main()
