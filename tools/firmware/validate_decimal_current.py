"""Run actual BASIC dispatch/PRINT/LET and original Canon reset, offline."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
from collections import deque
import binascii,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];RESEARCH=ROOT.parents[1]/'ROMReader'
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from cpu6301 import CPU
from audit_startup_retention import BootMachine,until
OUT=ROOT/'build/decimal-current'
S=json.loads((OUT/'symbols.json').read_text())
IMAGE=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
MASK=(RESEARCH/'dumps/dump_hd6301_v3_fast_1.bin').read_bytes()

class DecimalCPU(CPU):
    def __init__(self):
        super().__init__(IMAGE);self.m[0xC000:]=MASK;self.input=deque()
    def write(self,address,value):
        if address==0x18E5:
            self.writes.add(address);self.m[address]=value&255;return
        super().write(address,value)
    def step(self):
        if self.pc in (S['KBDPOLL'],S['KBDFAST']):
            if self.pc==S['KBDFAST']:self.a=0 # Queued test text belongs to blocking INPUT, not RUN polling.
            elif self.input and self.word(self.sp+3)==S['RESULTKEY']+3:self.a=13
            else:self.a=self.input.popleft() if self.input else 0
            self.z=self.a==0;self.pc=self.pop()*256+self.pop();return
        op=self.m[self.pc]
        if op==0x31: # INS: discard one stack byte, condition codes unchanged.
            self.pc+=1;self.sp=(self.sp+1)&65535;return
        if op==0x04: # HD6301 LSRD: logical right shift, V=N xor C, N=0.
            self.pc+=1
            self.c=bool(self.d&1);self.d>>=1
            self.n=False;self.z=self.d==0;self.v=self.c
            return
        if op not in (0x06,0x07,0x18,0x3D,0x8D,0x10,0x1B,0x40,0x50):
            return super().step()
        self.pc+=1
        if op==0x06:self.c,self.v,self.z,self.n,self.i=[bool(self.a&m) for m in (1,2,4,8,16)]
        elif op==0x07:self.a=0xC0|int(self.c)|(int(self.v)<<1)|(int(self.z)<<2)|(int(self.n)<<3)|(int(self.i)<<4)
        elif op==0x18:self.d,self.x=self.x,self.d
        elif op==0x3D:
            self.d=self.a*self.b;self.c=bool(self.b&128)
        elif op==0x8D:
            offset=self.fetch();self.push(self.pc&255);self.push(self.pc>>8)
            self.pc=(self.pc+(offset if offset<128 else offset-256))&65535
        elif op==0x10:self.a=self.sub(self.a,self.b)
        elif op==0x1B:self.a=self.add(self.a,self.b)
        else:
            reg='a' if op==0x40 else 'b';setattr(self,reg,self.sub(0,getattr(self,reg)))
    def idle(self):
        for _ in range(1500000):
            if self.pc==S['GETC'] and not self.input:return
            self.step()
        raise AssertionError(f'No keyboard wait at {self.pc:04X}')
    def command(self,text):
        self.input.extend((text+'\r').encode());self.idle()
    def screen(self):return bytes(self.lcd[:32]).decode().strip()

def main():
    c=DecimalCPU();c.pc=0x6829;c.m[0x3C]=0;c.idle();c.command('');c.command('')
    outputs=[]
    def expect(text,want):
        c.command(text);actual=c.screen()
        assert actual.startswith(want),(text,actual,want)
        outputs.append((text,actual))
        if want.startswith('?'):c.command('')
    expect('MEM','5951 BYTES FREE')
    expect('PRINT 0.1+0.2','0.3')
    c.command('a=12.5');expect('print a*2','25')
    expect('PRINT "TOTAL=";A/2','TOTAL=6.25')
    expect('MEM','5945 BYTES FREE')
    expect('B=1/0','?DECIMAL MATH');expect('PRINT A','12.5')
    expect('MEM','5945 BYTES FREE')
    # Fractions must never silently turn into a hardware address or value.
    c.command('POKE 7003.0,42.000');assert c.m[7003]==42
    expect('POKE 7003.5,99','?RANGE');assert c.m[7003]==42
    expect('POKE 7003,99.5','?RANGE');assert c.m[7003]==42
    expect('FOR A=1 TO 2','?DECIMAL TODO')
    expect('IF A THEN 20','?DECIMAL TODO')
    # Successful program edits invalidate variables; RUN uses decimal LET.
    c.command('NEW')
    for line in ('100 A=12.5','200 PRINT A/2','255 END'):c.command(line)
    expect('RUN','6.25')
    # INPUT uses the real line editor, native decimal evaluation and heap.
    for answer,want in [('12.5','6.25'),('-0.25','-0.125'),('0.1+0.2','0.15'),('1/0','?DECIMAL MATH'),('2.5 X','?SYNTAX')]:
        c.command('NEW')
        for line in ('10 A=7.25','20 INPUT "VALUE?";A','30 PRINT A/2','40 END'):c.command(line)
        expect('RUN\r'+answer,want)
        if want.startswith('?'):expect('PRINT A','7.25')
    c.command('NEW')
    for line in ('10 INPUT Z','20 PRINT Z','30 END'):c.command(line)
    expect('RUN\r-12.75','-12.75')
    end=c.word(S['PEND']);program=bytes(c.m[S['PROGRAM']:end+1])
    assert c.word(0x19FC)==0x5423
    assert c.word(0x19FE)==binascii.crc_hqx(program,0xFFFF)
    # Exact converter at all 16-bit boundaries and fractional trailing zeroes.
    converted=[]
    for text,want in [('0',0),('-0.0',0),('12.000',12),('32767',32767),('32768',32768),('65535',65535),('65536',None),('-32768',32768),('-32769',None),('12.001',None),('0.0000001',None),('99999999',None)]:
        negative=text.startswith('-');unsigned=text.lstrip('-');whole,_,fraction=unsigned.partition('.')
        digits=(whole+fraction).rjust(8,'0');assert len(digits)==8
        c.m[0x1E94:0x1E9D]=bytes(int(x) for x in digits)+bytes([len(fraction)|(128 if negative else 0)])
        oldsp=c.sp;c.push(0xF0);c.push(0xFF);c.pc=0xA400
        for _ in range(10000):
            if c.pc==0xFFF0:break
            c.step()
        else:raise AssertionError('converter did not return')
        assert c.sp==oldsp
        assert bool(c.c)==(want is None),(text,c.c,c.d)
        if want is not None:assert c.d==want,(text,c.d,want)
        converted.append((text,want))
    # Resume at idle and reset the program through the actual command path.
    c.pc=S['GETC'];c.command('NEW')
    records=b''.join(bytes([n])+b'REM '+b'A'*48+b'\0' for n in range(1,106))+b'\0'
    start=S['PROGRAM'];end=start+len(records)-1
    c.m[start:end+1]=records;c.m[S['PEND']:S['PEND']+2]=end.to_bytes(2,'big')
    c.command('105 REM '+('A'*48))
    c.command('A=0.125');expect('PRINT A*8','1')
    expect('MEM','275 BYTES FREE')
    assert bytes(c.m[start:end+1])==records
    assert c.word(0x19FE)==binascii.crc_hqx(records,0xFFFF)
    reboots=[]
    for bank in (0,1):
        memory=bytearray(c.m);memory[0x36]=bank
        boot=BootMachine(memory,True);boot.pc=0xFFE0
        steps=until(boot,0x6829,budget=2000000)
        c=DecimalCPU();c.m[:0x4000]=boot.m[:0x4000];c.pc=0x6829
        c.idle();c.command('');c.command('')
        assert bytes(c.m[start:end+1])==records
        expect('MEM','281 BYTES FREE');expect('PRINT A','0')
        reboots.append(dict(bank=bank,steps=steps))
    # A full arena permits no variable, and must not corrupt program bytes.
    full=b''.join(bytes([n])+b'REM '+b'A'*48+b'\0' for n in range(1,111))
    full+=bytes([111])+b'REM '+b'A'*5+b'\0'+b'\0'
    assert len(full)==5952
    end=start+len(full)-1;c.m[start:end+1]=full
    c.m[S['PEND']:S['PEND']+2]=end.to_bytes(2,'big')
    c.command('111 REM AAAAA') # Same length, commit and reset heap through editor.
    expect('MEM','0 BYTES FREE');expect('A=1','?PROGRAM FULL')
    assert bytes(c.m[start:end+1])==full
    assert c.word(S['PEND'])==end
    assert c.word(0x19FC)==0x5423
    assert c.word(0x19FE)==binascii.crc_hqx(full,0xFFFF)
    report=dict(candidate_sha256=hashlib.sha256(IMAGE).hexdigest(),outputs=outputs,
        integer_conversion_cases=converted,reboots=reboots,full_arena_bytes=len(full),
        limits='Offline candidate only. FOR/IF, binary literals and numeric functions pending; printer ROM placement not audited. No hardware validation.')
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
