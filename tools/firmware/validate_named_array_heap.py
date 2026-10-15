"""CPU-only coexistence of named arrays and the live 0.4.36 scalar heap.

DIM is hooked only in this private CPU copy, not a flash image. The module is
at emulator address 1000; LET/INPUT floor reset and MEM are patched here only.
"""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib
import json
import re
import subprocess
import os
import validate_decimal_current as emu
ROOT=emu.ROOT
OUT=ROOT/'build/array-heap';OUT.mkdir(exist_ok=True)
JOB=0x1CDE
FLOOR=0x1EC0
HEAP=0x1EBE

def setup():
    current=ROOT/'build/token-current'
    emu.S=json.loads((current/'symbols.json').read_text())
    image=release_input('s70-basic-0.4.36-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(image).hexdigest()=='3842d911260ec7fa6534be37b224046dd04998e4805b9f043f706060a1fa480e'
    emu.IMAGE=image[16384:]+image[:16384]
    links=dict(emu.S)
    for path in (ROOT/'build/decimal-current/decimal-expressions.lst',current/'decimal-functions.lst'):
        table=path.read_text().split('SYMBOL TABLE')[1]
        links.update({n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',table)})
    for name,lo,hi in json.loads((ROOT/'tools/firmware/candidate_ram_map.json').read_text())['blocks']:
        assert JOB+32<=int(lo,16) or JOB>=int(hi,16),name
    source=f'PEND EQU ${emu.S["PEND"]:04X}\nDHEAP EQU $1EBE\nDFLOOR EQU $1EC0\n'
    source+=''.join(f'{k} EQU ${v:04X}\n' for k,v in links.items() if k not in ('PEND','DHEAP','DFLOOR'))
    source+=(ROOT/'src/array-index.asm').read_text().replace('ORG $6000','ORG $1000')
    source+=(ROOT/'src/array-create.asm').read_text().replace('        INCLUDE "src/array-index.asm"','')
    source+=(ROOT/'src/array-named-heap.inc').read_text()
    source+=(ROOT/'src/array-dim.inc').read_text()
    source+=(ROOT/'src/array-access.inc').read_text()
    (OUT/'module.asm').write_text(source)
    r=subprocess.run([str(emu.RESEARCH/'tmp/m680x-tools/a09.exe'),'-W',
        '-B'+str(OUT/'module.bin'),'-L'+str(OUT/'module.lst'),str(OUT/'module.asm')],capture_output=True,text=True)
    assert r.returncode==0,r.stdout+r.stderr
    table=(OUT/'module.lst').read_text().split('SYMBOL TABLE')[1]
    symbols={n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',table)}
    code=(OUT/'module.bin').read_bytes()
    c=emu.DecimalCPU();c.pc=0x6829;c.idle();c.command('');c.command('')
    # Keep validated release immutable. This is a tentative RAM ABI change.
    old=bytes.fromhex('FE19CE08FF1EC0')
    assert bytes(c.m[0x4000:0xC000]).count(old)==2 # LET and INPUT.
    patched=bytes(c.m[0x4000:0xC000]).replace(old,b'\x01'*len(old))
    oldmem=bytes.fromhex('FC1EBEB319CE830001')
    assert patched.count(oldmem)==1
    patched=patched.replace(oldmem,bytes.fromhex('FC1EBEB31EC0010101'))
    c.m[0x4000:0xC000]=patched;c.m[0x1000:0x1000+len(code)]=code
    entry=emu.S['EXECUTE'];space=emu.S['SPACE']
    assert bytes(c.m[entry:entry+3])==bytes((0xBD,space>>8,space&255))
    c.m[entry:entry+3]=bytes((0x7E,symbols['DIMDISPATCH']>>8,symbols['DIMDISPATCH']&255))
    for entry,oldtarget,newtarget in ((0xA006,links['DECIMAL_LET'],symbols['ARLET']),
        (links['FNFALLBACK']+3,links['DVARIABLE'],symbols['ARATOM'])):
        assert bytes(c.m[entry:entry+3])==bytes((0x7E,oldtarget>>8,oldtarget&255))
        c.m[entry:entry+3]=bytes((0x7E,newtarget>>8,newtarget&255))
    if os.environ.get('TYPESTAR_ARRAY_ROM_NAMED') == '1' or os.environ.get('TYPESTAR_ARRAY_ROM_FULL') == '1':
        from array_rom_named import install
        placement = install(c, symbols, ROOT, OUT, emu.RESEARCH/'tmp/m680x-tools/a09.exe')
        (OUT/'named-rom-placement.json').write_text(json.dumps(placement,indent=2)+'\n')
    return c,symbols,code,image

def main():
    c,symbols,code,image=setup()
    def call(label,address=JOB):
        regs=(c.pc,c.sp,c.a,c.b,c.x,c.i)
        c.x=address;c.push(0xF0);c.push(0xFF);c.pc=symbols[label] if isinstance(label,str) else label
        for _ in range(250000):
            if c.pc==0xFFF0:break
            c.step()
        else:raise AssertionError(('call timeout',label,hex(c.pc)))
        assert c.sp==regs[1] and c.x==address and c.i==regs[5]
        result=(c.c,c.a)
        c.pc,c.sp,c.a,c.b,c.x,c.i=regs
        return result
    def put(address,n):c.m[address:address+2]=n.to_bytes(2,'big')
    def allocate(name,n0,n1=1,rank=1,error=None):
        before=bytes(c.m[0x20C0:0x3800]);floor=c.word(FLOOR);heap=c.word(HEAP)
        c.m[JOB:JOB+6]=bytes((rank,5))+n0.to_bytes(2,'big')+n1.to_bytes(2,'big')
        c.m[JOB+29]=ord(name)
        c.writes.clear()
        failed,status=call('ARRAY_NAMED_CREATE')
        permitted=set(range(JOB,JOB+32))|set(range(floor,heap))|{FLOOR,FLOOR+1}|set(range(0x1F00,0x2000))
        assert not c.writes-permitted,sorted(c.writes-permitted)
        assert failed==(error is not None),(name,status,error)
        assert c.word(HEAP)==heap
        if error is not None:
            assert status==error and c.word(FLOOR)==floor
            assert bytes(c.m[0x20C0:0x3800])==before
            return None
        assert c.word(FLOOR)==floor+9+5*n0*n1
        assert bytes(c.m[floor:floor+7])==bytes((ord(name),rank,5))+n0.to_bytes(2,'big')+n1.to_bytes(2,'big')
        assert not any(c.m[floor+9:c.word(FLOOR)])
        return floor
    c.command('10 PRINT 12.5');c.command('A=12.5')
    program=bytes(c.m[0x20C0:c.word(emu.S['PEND'])+1])
    crc=bytes(c.m[0x19FC:0x1A00])
    first=allocate('A',10);second=allocate('B',4,5,2)
    floor=c.word(FLOOR)
    arrays=bytes(c.m[first:floor])
    c.command('A=A+0.25:B=-0.125');c.command('PRINT A+B')
    assert c.screen()=='12.625' and c.word(FLOOR)==floor
    assert bytes(c.m[first:floor])==arrays
    c.command('MEM');assert c.screen()==f'{c.word(HEAP)-floor} BYTES FREE'
    allocate('A',1,error=2);allocate('?',1,error=3);allocate('C',0,error=1)
    allocate('C',13108,error=1);allocate('C',65535,65535,2,error=1)
    span=bytes(c.m[first+7:first+9]);c.m[first+7:first+9]=b'\xff\xff'
    allocate('D',1,error=4)
    c.m[first+7:first+9]=span
    for name,location in [('A',first),('B',second)]:
        c.m[JOB+29]=ord(name);assert call('ARRAY_NAMED_FIND')==(False,0)
        assert c.word(JOB+25)==location+1
    # Checked last matrix element, using its actual allocated descriptor.
    c.m[JOB:JOB+6]=c.m[second+1:second+7]
    put(JOB+6,second+9);put(JOB+8,3);put(JOB+10,4)
    assert not call('ARRAY_ELEMENT')[0]
    cell=c.word(JOB+12);assert cell==second+9+19*5
    # Store/restore one native decimal using the real packing codec. Byte
    # copies stand in for the future array assignment code, not a BASIC API.
    native=bytes((0,0,0,0,0,1,2,5,0x83)) # -0.125
    c.m[0x1E94:0x1E9D]=native
    call(0x9E00,0x1E94)
    c.m[cell:cell+5]=c.m[0x1E94:0x1E99]
    assert bytes(c.m[cell:cell+5])==bytes.fromhex('00 00 01 25 83')
    c.m[0x1E94:0x1E9D]=bytes(c.m[cell:cell+5])+b'\0'*4
    call(0x9E03,0x1E94);assert bytes(c.m[0x1E94:0x1E9D])==native
    # Use remaining arena, leaving <6 bytes: a new scalar must fail atomically.
    count=(c.word(HEAP)-c.word(FLOOR)-9)//5
    allocate('Z',count)
    full=bytes(c.m[0x20C0:0x3800]);floor=c.word(FLOOR)
    c.command('C=7');assert c.screen()=='?PROGRAM FULL',c.screen()
    c.command('');assert bytes(c.m[0x20C0:0x3800])==full
    assert c.word(FLOOR)==floor
    allocate('D',1,error=1)
    assert bytes(c.m[0x20C0:c.word(emu.S['PEND'])+1])==program
    assert bytes(c.m[0x19FC:0x1A00])==crc
    # Editing intentionally discards volatile arrays and scalars together.
    c.command('20 END')
    assert c.word(FLOOR)==c.word(emu.S['PEND'])+1 and c.word(HEAP)==0x3800
    allocate('A',1)
    c.command('RUN');assert c.screen()=='12.5'
    assert c.word(FLOOR)==c.word(emu.S['PEND'])+1 and c.word(HEAP)==0x3800
    c.command('NEW');c.command('10 INPUT A');c.command('20 PRINT A')
    c.command('RUN') # Pause inside the real INPUT editor, before allocation.
    active=allocate('B',3);floor=c.word(FLOOR)
    c.m[active+9]=0x12
    c.command('2.5');assert c.screen()=='2.5'
    assert c.word(FLOOR)==floor and c.m[active+9]==0x12
    c.command('NEW')
    assert c.word(FLOOR)==0x20C1 and c.word(HEAP)==0x3800
    report=dict(result='PASS',module_bytes=len(code),named_wrapper_bytes=161,
        partial_rom_placement=os.environ.get('TYPESTAR_ARRAY_ROM_NAMED') == '1',
        module_sha256=hashlib.sha256(code).hexdigest(),base_nh7_sha256=hashlib.sha256(image).hexdigest(),
        checks=['named 1D/2D allocation','scalar/array same name','LET preserves arrays',
                'MEM shared gap','duplicate/invalid/full refusal','lookup','scalar refusal at full heap',
                'last matrix element and decimal codec roundtrip',
                'program/CRC preserved','edit reset','RUN reset','INPUT preserves arrays','NEW reset'],limits=__doc__)
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
