"""Extract all 95 ASCII glyph streams through original Canon CPU routines.

Keeps three output lanes per column: no lossy projection to 16-row graphics.
The 31 columns are those consumed by native counters, NOT inferred spans.
Timer scheduling is stubbed; this does not establish physical 24-row order.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import sys,json,hashlib
PROJECT=Path(__file__).resolve().parents[2]
ROOT=PROJECT.parents[1]/'ROMReader'
sys.path.insert(0,str(ROOT/'tools'))
from trace_s70_glyph_extent import ExtentMachine

def trace(path,ram_patterns=None,initial_ram=None,characters='ABCD',stack_top=0x1FFF):
    raw=path.read_bytes()
    assert len(raw)==32768
    mem=bytearray(65536)
    mem[0x4000:0xC000]=raw[16384:]+raw[:16384]
    mem[0xC000:]=(ROOT/'dumps/dump_hd6301_v3_fast_1.bin').read_bytes()
    if initial_ram:
        for address,data in initial_ram.items():
            assert 0<=address<0x4000 and address+len(data)<=0x4000
            mem[address:address+len(data)]=data
    rows=[]
    for char in characters:
        record=0x401E+4*(ord(char)-16)
        start=int.from_bytes(mem[record+2:record+4],'big')
        end=int.from_bytes(mem[record+6:record+8],'big')
        if start<0x4000:
            end=start+64 # Caller-owned RAM glyph, not a packed-ROM span.
        m=ExtentMachine(mem)
        m.sp=stack_top
        if ram_patterns is not None:
            # Simulation-only caller-owned record/buffer. This demonstrates
            # decoder consumption, NOT availability of these addresses while
            # Canon's real editor/IRQ state is running on hardware.
            record,start,end=0x1120,0x1000,0x1040
            data=ram_patterns[char]
            assert len(data)==64 and data[-2:]==b'\0\0'
            m.m[record:record+4]=bytes.fromhex('20 00 10 00')
            m.m[start:end]=data
        m.m[0xBC]=ord(char)
        m.m[0x41]=0x48
        m.m[0x49]=2
        m.m[0x4E:0x50]=(0x6EE9).to_bytes(2,'big')
        m.m[0x4A:0x4C]=(0x6F6D).to_bytes(2,'big')
        m.m[0x5E:0x60]=record.to_bytes(2,'big')
        # The normal built-in glyph width is 32/2 = 16, four intervals/unit.
        assert m.m[record]==32
        stride=3 if m.m[record+1]==1 else 2
        m.m[0x6F:0x71]=(64).to_bytes(2,'big')
        m.call(0x75AE)
        units=[]
        complete=False
        for phase in range(130):
            m.pc=0x739D if phase%2==0 else 0x73AF
            before=int.from_bytes(m.m[0x5E:0x60],'big')
            for _ in range(300):
                if m.pc in (0x73C1,0x76E7,0x76E8): break
                m.step()
            assert m.pc in (0x73C1,0x76E7,0x76E8)
            assert m.sp==stack_top and not m.events
            if m.pc==0x73C1:
                complete=True; break
            if phase%2==0:
                after=int.from_bytes(m.m[0x5E:0x60],'big')
                assert after==before+stride
                units.append({'address':f'{before:04X}',
                              'lanes':list(m.m[0x66:0x69]),
                              'outside_pointer_span':before>=end})
        assert complete and len(units)==31
        rows.append({'char':char,'start':f'{start:04X}','next_pointer':f'{end:04X}',
                     'consumed_units':len(units),'units':units,
                     'nonzero_overhang':[u for u in units if u['outside_pointer_span'] and any(u['lanes'])]})
    return {'image':str(path.resolve()),'sha256':hashlib.sha256(raw).hexdigest(),'glyphs':rows,
            'limits':'Normal width, built-in formats 0..3, no composition or underline. Timer scheduling stubbed, interrupts driven explicitly, physical output not simulated.'}


if __name__=='__main__':
    out=PROJECT/'build/paper-font';out.mkdir(exist_ok=True)
    path=ROOT/'dumps/256ROM_NH7_1181.bin'
    assert hashlib.sha256(path.read_bytes()).hexdigest()=='5eb09f28e9e93989631544f1f13defe32679e86300702692e5c7d137f168f03c'
    report=trace(path,characters=''.join(map(chr,range(32,127))))
    (out/'native-trace.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Extracted',len(report['glyphs']),'native ASCII streams')
