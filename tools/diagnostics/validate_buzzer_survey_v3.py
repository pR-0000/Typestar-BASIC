"""Validate actual v3 opcodes before publishing local flashable images.

Critical kernels/padding run instruction by instruction with documented cycle
counts. Full-suite checks accelerate these independently verified kernels and
timer waits; Canon keyboard/LCD calls are mocked in those functional checks.
"""
from pathlib import Path
import copy
import csv
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/buzzer-survey-v3'
sys.path.insert(0,str(ROOT/'studio/internal'))
from hd6301 import HD6301CPU

# HD6301 table in Hitachi handbook, pp. 51 (BNE), 60 (DEX), 80 (JSR),
# 89 (NOP), 99 (RTS), 106 (STA). This is a narrow timing checker, not an ASIC.
CRITICAL_CYCLES={0x01:1,0x09:1,0x97:3,0xD7:3,0x26:3,0x27:3,0x7E:3,0xBD:6,0x39:5}


class TimedCPU(HD6301CPU):
    def __init__(self,image,strict=False):
        super().__init__(image)
        self.time=0;self.strict=strict;self.edges=[];self.capture=True;self.latch=0

    def read(self,address):
        if address==9:self.latch=self.time&65535;return self.latch>>8
        if address==10:return self.latch&255
        return super().read(address)

    def write(self,address,value):
        if address==0x34 and self.capture:self.edges.append((self.time,value&255))
        if address in (0x18f5,0x18f6):
            self.m[address]=value&255;self.writes.add(address);return
        super().write(address,value)

    def step(self):
        op=self.m[self.pc]
        if self.strict:assert op in CRITICAL_CYCLES,(hex(self.pc),hex(op))
        super().step()
        self.time+=CRITICAL_CYCLES.get(op,4)

    def enter(self,address):
        self.push(0xFF);self.push(0x3F);self.pc=address

    def return_now(self):
        self.pc=self.pop()*256+self.pop()

    def run_until_return(self,budget=2000000):
        for _ in range(budget):
            if self.pc==0x3fff:return
            self.step()
        raise AssertionError(('timeout',hex(self.pc)))


def main():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    image=(OUT/'cpu.bin').read_bytes();s=manifest['symbols']
    # Real instruction execution: every padding subroutine, including recursion.
    pad_count=0
    for name,address in s.items():
        if not name.startswith('AUPAD'):continue
        ticks=int(name[5:]);c=TimedCPU(image,strict=True)
        c.a=0xA1;c.b=0x35;c.x=0x1289
        c.m[0x1e00:0x1e03]=bytes((0xBD,address>>8,address&255));c.pc=0x1e00
        for _ in range(100000):
            if c.pc==0x1e03:break
            c.step()
        else:raise AssertionError(name)
        assert c.time==ticks,(name,c.time,ticks)
        assert (c.a,c.b,c.x,c.sp)==(0xA1,0x35,0x1289,0x1fff)
        pad_count+=1
    # Three complete periods prove the exact plateau timing across both loops.
    for wave in manifest['waves']:
        c=TimedCPU(image,strict=True);c.a=0xD1;c.b=0x91;c.x=3
        c.enter(s[wave['label']]);c.run_until_return()
        expected=[]
        for period in range(3):
            t=period*wave['period_cycles']
            for on,ticks in wave['states']:
                expected.append((t,0xD1 if on else 0x91));t+=ticks
        assert c.edges==expected,(wave['label'],c.edges[:8],expected[:8])
        assert (c.a,c.b,c.x,c.sp)==(0xD1,0x91,0,0x1fff)

    wave_by_pc={s[w['label']]:w for w in manifest['waves']}
    wave_by_name={w['label']:w for w in manifest['waves']}
    job_by_pc={s[f"AUJ{r['id']}"]:r for r in manifest['sections']}
    rows=manifest['sections']

    class Suite(TimedCPU):
        def __init__(self,event,initial=0x91,irq=False):
            super().__init__(image)
            self.event=event;self.initial=initial;self.i=irq;self.capture=False
            self.m[0x1801]=initial;self.m[0x19eb:0x19f5]=bytes(range(10))
            self.messages=[];self.jobs=[];self.wave_calls=[];self.gate_writes=0
            self.borrowed_initial=bytes(self.m[0x19eb:0x19f5]);self.last_job=None
            self.enter(s['AUWAIT'])

        def write(self,address,value):
            assert address in (0x34,0x1801,0x18f5,0x18f6,0xfa) or 0x19eb<=address<0x19f5 or 0x1f00<=address<=0x1fff,hex(address)
            if address==0x34:
                assert value&0xbf==self.initial&0xbf,(hex(address),hex(value),hex(self.initial))
                self.gate_writes+=1
                assert self.i
            super().write(address,value)

        def step(self):
            pc=self.pc
            if pc==0x69b2:
                self.a=self.event;self.b=self.event&127;self.x=0x1234;self.return_now();return
            if pc==0xf33b:self.return_now();return
            if pc==0xddd1:
                self.messages.append(bytes(self.m[self.x:self.x+self.a]).decode('ascii').strip())
                self.return_now();return
            if pc==s['AUTIME']:
                deadline=self.word(s['AULIMIT']);delta=(deadline-self.time)&65535
                assert 0<delta<=25000,delta
                self.time+=delta;self.return_now();return
            if pc in job_by_pc:
                row=job_by_pc[pc];self.jobs.append(row['id']);self.last_job=row
            if pc in wave_by_pc:
                w=wave_by_pc[pc];loops=self.x;assert loops>0
                assert (self.a,self.b)==(self.initial|64,self.initial&0xbf)
                self.wave_calls.append((self.last_job['id'],w['label'],loops))
                # The exact instructions for these plateaus were checked above.
                for _ in range(loops):
                    for on,ticks in w['states']:
                        self.write(0x34,self.a if on else self.b);self.time+=ticks
                # Last loop takes no long JMP for the 31-bit pattern.
                self.time+=5-(3 if len(w['states'])>2 else 0)
                self.x=0;self.z=True;self.return_now();return
            super().step()

    full_checks=[]
    for event,initial,irq in ((0x3a,0,False),(0xba,0x91,False),(0x3a,0xff,True),
                              (0x1b,0xd1,True),(0x1c,0x91,False),(0x1d,0x91,False),
                              (0x1e,0x91,False),(0x1f,0x91,False)):
        selected=0 if event&127==0x3a else (event&127)-0x1a
        expected=[r for r in rows if not selected or r['group']==selected]
        c=Suite(event,initial,irq);c.run_until_return()
        assert c.jobs==[r['id'] for r in expected]
        assert c.messages==[r['label'] for r in expected]+['END V3 - I/II OR 1-5']
        expected_calls=[(r['id'],run['wave'],run['loops']) for r in expected for run in r['runs']]
        assert c.wave_calls==expected_calls
        assert c.m[0x1801]==c.m[0x34]==initial&0xbf
        assert c.m[0x19eb:0x19f5]==c.borrowed_initial
        assert (c.a,c.b,c.m[0xfa],c.x,c.sp,c.i)==(0x3d,0x3d,0x3d,0x1234,0x1fff,irq)
        expected_writes=2+len(expected)+sum(1 if r['hold'] else sum(run['loops']*len(wave_by_name[run['wave']]['states']) for run in r['runs']) for r in expected)
        assert c.gate_writes==expected_writes,(c.gate_writes,expected_writes)
        full_checks.append(dict(event=event,sections=len(expected),gate_writes=c.gate_writes,
                                functional_approx_seconds=c.time/1e6,min_sp=c.min_sp))
    passthrough=0
    for event in range(256):
        if event&127 in (0x3a,0x1b,0x1c,0x1d,0x1e,0x1f):continue
        c=Suite(event);c.run_until_return()
        assert not c.messages and c.gate_writes==0
        assert (c.a,c.b,c.x,c.sp)==(event,event&127,0x1234,0x1fff)
        passthrough+=1
    # Real reset, native IRQ-driven matrix decoding and LCD routines, with the
    # patched font region in place. The hardware model is functional only.
    from machine import GenericMachine
    mask=(ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin').read_bytes()
    native=GenericMachine(image,mask,mechanics=True)
    for boot_steps in range(2500000):
        if native.pc==s['AUWAIT']:break
        native.step()
    else:raise AssertionError(('native boot timeout',hex(native.pc)))
    for key in (0x1b,0x1c,0x1d,0x1e,0x1f,0x3a):
        c=copy.deepcopy(native);c.set_matrix([key])
        for _ in range(400000):
            if c.pc==s['AUWAIT']+3:break
            c.step()
        else:raise AssertionError(('native key timeout',key,hex(c.pc)))
        assert c.a&127==key
    native.i=True
    def native_call(address):
        saved_sp=native.sp;native.push(0xff);native.push(0x3f);native.pc=address
        for _ in range(300000):
            if native.pc==0x3fff:assert native.sp==saved_sp;return
            native.step()
        raise AssertionError(('native display timeout',hex(native.pc)))
    native_call(0xf33b)
    for name in ('AUT101','AUT143','AUT318','AUT408','AUT507','AUENDTEXT'):
        native.a=24;native.x=s[name];native_call(0xddd1)
        assert bytes(native.lcd[:24])==bytes(native.m[s[name]:s[name]+24]),name
    raw=(ROOT.parent.parent/'ROMReader/dumps/256ROM_NH7_1181.bin').read_bytes()
    original=raw[16384:]+raw[:16384]
    changes=[i+0x4000 for i,(a,b) in enumerate(zip(image,original)) if a!=b]
    assert all(0x4000<=p<0x4000+manifest['payload_bytes'] or 0x682e<=p<0x6831 for p in changes)
    manifest.update(status='PASS - physical recording required',validation=dict(
        exact_cycle_kernels=len(manifest['waves']),exact_cycle_padding=pad_count,
        full_functional_checks=full_checks,passthrough_keys=passthrough,
        write_allowlist=True,scratch_restored=True,irq_mask_restored=True,
        final_gate_muted=True,patch_ranges_checked=True,
        native_boot_instructions=boot_steps,native_key_checks=6,native_lcd_checks=6,
        limits='Critical waveforms use documented cycle counts; ASIC electrical latency, oscillator, clock accuracy and physical sound are not simulated. Full-suite checks accelerate verified kernels and timer waits; Canon display/keyboard are mocked.'))
    socket=image[16384:]+image[:16384]
    assert hashlib.sha256(socket).hexdigest()==manifest['socket_sha256']
    release=ROOT/'release';release.mkdir(exist_ok=True)
    for suffix,content in (('-nh7',socket),('-64k-mirror',socket*2)):
        p=release/f's70-buzzer-survey-v3{suffix}.bin';p.write_bytes(content)
        p.with_suffix('.sha256').write_text(hashlib.sha256(content).hexdigest()+'  '+p.name+'\n',encoding='ascii')
    for p in (OUT/'manifest.json',release/'s70-buzzer-survey-v3-manifest.json'):
        p.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    # Approximate anchors for later matching to an acoustic recording. Native
    # LCD/dispatch time and CPU-clock tolerance remain outside this timeline.
    with (release/'s70-buzzer-survey-v3-sequences.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f);writer.writerow(('ID','Group','Label','Approx start s','Nominal sound s','Gap s','Gate Hz','On fraction'))
        t=0
        for r in rows:
            writer.writerow((r['id'],r['group'],r['label'],round(t,6),round(r['nominal_seconds'],6),.35,
                             r['runs'][0]['nominal_hz'] if len(r['runs'])==1 else '',
                             r['runs'][0]['on_fraction'] if len(r['runs'])==1 else ''))
            t+=r['nominal_seconds']+.35
    print(json.dumps(dict(status=manifest['status'],kernels=len(manifest['waves']),padding=pad_count,
                         functional_suites=len(full_checks),passthrough_keys=passthrough,
                         socket_sha256=manifest['socket_sha256']),indent=2))


if __name__=='__main__':main()
