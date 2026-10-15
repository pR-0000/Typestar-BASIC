"""Build/test a Canon-context buzzer module. Not a flashable ROM."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import sys,subprocess,re,json,hashlib
ROOT=Path(__file__).resolve().parents[2]; READER=ROOT.parents[1]/'ROMReader'
OUT=ROOT/'build/buzzer'; OUT.mkdir(parents=True,exist_ok=True)
p=subprocess.run([str(READER/'tmp/m680x-tools/a09.exe'),'-W',
 '-Bbuild/buzzer/module.bin','-Lbuild/buzzer/module.lst','src/buzzer.asm'],cwd=ROOT,capture_output=True,text=True)
lst=(OUT/'module.lst').read_text(); assert p.returncode==0 and re.search(r'\b0 error\(s\)',lst),lst
symbols={n:int(v,16) for n,v in re.findall(r'\b(BEEP_\w+)\s+02\s+([0-9A-F]{4})',lst)}
code=(OUT/'module.bin').read_bytes()
sys.path.insert(0,str(READER/'tools'))
from trace_s70_asic import AsicMachine,memory,validate
validate()
mem=memory(); mem[0x6000:0x6000+len(code)]=code
for duration in range(256):
 for irq in (False,True):
    m=AsicMachine(mem); m.i=irq; m.x=0x1234
    m.call(symbols['BEEP_REQUEST'],a=duration)
    assert m.i==irq and m.x==0x1234
    assert m.b==(0 if duration>=2 else 2)
    assert m.m[0x18F6]==(duration if duration>=2 else 0)
    if duration>=2:
        for _ in range(duration): m.tick()
        assert m.controls==[(0x34,64),(0x34,0)]
for shadow in range(256):
 for irq in (False,True):
    m=AsicMachine(mem); m.m[0x1801]=shadow; m.m[0x18F5:0x18F7]=bytes((1,60))
    m.a=0xA5; m.b=0x5A; m.x=0x1234; m.i=irq
    m.call(symbols['BEEP_STOP'])
    assert (m.a,m.b,m.x,m.i)==(0xA5,0x5A,0x1234,irq)
    assert m.m[0x18F5:0x18F7]==bytes(2)
    assert m.controls==[(0x34,shadow&191)] and m.m[0x1801]==shadow&191
for pending,ticks in ((0,12),(1,0),(1,12)):
    m=AsicMachine(mem); m.m[0x18F5:0x18F7]=bytes((pending,ticks))
    m.call(symbols['BEEP_REQUEST'],a=20)
    assert m.b==1 and m.m[0x18F5:0x18F7]==bytes((pending,ticks))
manifest=dict(size=len(code),symbols=symbols,sha256=hashlib.sha256(code).hexdigest(),
 status='module-only-not-flashable',tests='512 duration/IRQ cases, 512 stop/shadow/IRQ cases, 3 busy cases; original tick service executed',
 limits='Requires native Canon periodic service and RAM ownership. No frequency or wall-clock calibration, not yet integrated in BASIC.')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('PASS:',manifest)
