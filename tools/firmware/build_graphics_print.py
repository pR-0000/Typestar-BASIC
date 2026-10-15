"""Build bounded PC-image printer on the hardware-validated .40 driver."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
OUT=ROOT/'build/graphics-print'
VERSION='0.4.41-gp'

def main():
    OUT.mkdir(exist_ok=True)
    raw=release_input('s70-basic-0.4.40-th-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='ed84eabcf5890a7a7c4714d3c9ee8bfd38224992d9ceb00dae4c64eef38a76bd'
    cpu=bytearray(raw[16384:]+raw[:16384]);before=bytes(cpu)
    # Replace both experimental modules. Keep the complete .38 BASIC placement.
    s=json.loads((ROOT/'build/keyboard-current/symbols.json').read_text())
    bindings=dict(GXBUFFER=0x1DCB,GXPATTERN=0x1BC0,GXCOUNT=0x1B91,
        GXPTR=0x1B92,GXLEFT=0x1B94,GFCRC=0x1B95,GFLEFT=0x1B97,GFBITS=0x1B98,
        GFVALUE=0x1B99,GFHIGH=0x1B9A,GPRAN=0x1B9B,
        GXSTATE=0x1E61,GXROW=0x1E62,GXCOL=0x1E63,GXSEQ=0x1E64,
        GXNX=0x1E66,GXNY=0x1E67,GXHIGH=0x1E68,
        PRINT_GLYPH_BUSY=0x1E80,GPERROR=0x1E81,GPTICKS=0x1E82,
        GPSP=0x1E84,GPSAVED08=0x1E86)
    source='        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|bindings).items())+'        ORG $8800\n'
    for name in ('graphics-key.inc','graphics-frame.inc','graphics-print.inc',
                 'print-stage-call.inc','print-paper-continuation.inc',
                 'print-glyph-complete.inc','graphics-thermal.inc'):
        source+=(ROOT/'src'/name).read_text()+'\n'
    # Reuse the EXACT validated bounded SCI and ASIC/shutdown implementations.
    rx=(ROOT/'src/graphics-rx-test.inc').read_text()
    source+=rx[rx.index('GXRX PSHX'):rx.index('GXIDENT FCC')]
    th=(ROOT/'src/thermal-test.inc').read_text()
    source+=th[th.index('GPASIC PSHA'):th.index('GPDESC FCB')]
    code,linked=assemble('graphics-print',source)
    assert 0x8800+len(code)<=0x9000,len(code)
    # Remove retired .39/.40 module tails by restoring original ROM bytes,
    # not by claiming the entire window as blank/free memory.
    original=(ROOT.parents[1]/'ROMReader/dumps/256ROM_NH7_1181.bin').read_bytes()
    assert hashlib.sha256(original).hexdigest()=='5eb09f28e9e93989631544f1f13defe32679e86300702692e5c7d137f168f03c'
    original_cpu=original[16384:]+original[:16384]
    cpu[0x4800:0x5000]=original_cpu[0x4800:0x5000]
    cpu[0x4800:0x4800+len(code)]=code
    changes=[]
    def patch(address,target,size=3,op=0x7E):
        at=address-0x4000;n=linked[target]
        expected=before[at:at+size]
        assert expected[0] in (0x7E,0xBD),(hex(address),expected.hex())
        replacement=bytes((op,n>>8,n&255))+b'\x01'*(size-3)
        cpu[at:at+size]=replacement
        changes.append(dict(address=address,before=expected.hex(),after=replacement.hex(),target=target))
    patch(s['KBDREAD'],'GRAPHICS_SCAN',op=0xBD)
    patch(s['KBDCHAR'],'GRAPHICS_KEYCHAR',4)
    patch(s['EDPRINTABLE'],'GXEDIT',4)
    patch(s['UIINIT'],'GPINIT',op=0xBD)
    patch(0x7716,'GPASIC')
    patch(0x770E,'GPPHASEWAIT',5,0xBD)
    patch(0x773E,'GPPHASEWAIT',6)
    previous=b'Typestar BASIC 0.4.40-th ';replacement=f'Typestar BASIC {VERSION} '.encode()
    assert len(previous)==len(replacement)
    banner=cpu.index(previous)
    cpu[banner:banner+len(previous)]=replacement
    assert len(cpu)==32768
    allowed=set(range(0x4800,0x5000))|set(range(banner,banner+len(previous)))
    for p in changes:allowed.update(range(p['address']-0x4000,p['address']-0x4000+len(bytes.fromhex(p['before']))))
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(before,cpu)))
    m=json.loads((ROOT/'build/keyboard-current/manifest.json').read_text())
    for module in m['runtime_segments']+m['loop_modules']+m['statement_modules']:
        assert module['origin']+module['bytes']<=0x8800 or module['origin']>=0x9000,module
    m.update(version=VERSION,sha256=hashlib.sha256(cpu).hexdigest(),graphics_bytes=len(code),
        status='Serial thermal image printer; hardware validation pending',graphics_patches=changes,
        graphics_scratch=bindings,base_nh7_sha256=hashlib.sha256(raw).hexdigest())
    m['statement_modules'].append(dict(name='graphics-print',origin=0x8800,bytes=len(code)))
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s|bindings|linked,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print(VERSION,len(code),m['sha256'])

if __name__=='__main__':main()
