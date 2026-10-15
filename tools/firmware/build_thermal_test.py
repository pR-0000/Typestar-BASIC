"""Build one-glyph CODE+P paper experiment on the hardware-validated .39."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
from pattern_codec import SCAN_ROW_BITS,encode_columns
OUT=ROOT/'build/thermal-test'

def main():
    OUT.mkdir(exist_ok=True)
    raw=release_input('s70-basic-0.4.39-rx-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='fe00ac3dea9817db0ce7f6809b3c28505048feab14929d0ded1b3034a08365d7'
    cpu=bytearray(raw[16384:]+raw[:16384]);before=bytes(cpu)
    s=json.loads((ROOT/'build/graphics-rx-test/symbols.json').read_text())
    bindings=dict(PRINT_GLYPH_BUSY=0x1B94,GPERROR=0x1B95,GPTICKS=0x1B96,
                  GPSP=0x1B98,GPSAVED08=0x1B9A,GPRAN=0x1B9B,GPPTR=0x1B9C)
    words=[sum(1<<SCAN_ROW_BITS[y] for y in range(16)
               if x in (0,30) or y in (0,15) or y==x//2) for x in range(31)]
    data=encode_columns(words,0,31)+b'\0\0'
    (OUT/'pattern.inc').write_text('GPDATA FCB '+','.join(f'${v:02X}' for v in data)+'\n')
    # Old symbols include prototype names from the RX file only, no printer labels.
    source='        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in (s|bindings).items())+'        ORG $8C00\n'
    for name in ('print-stage-call.inc','print-paper-continuation.inc','print-glyph-complete.inc','thermal-test.inc'):
        source+=(ROOT/'src'/name).read_text()+'\n'
    code,linked=assemble('thermal-test',source)
    assert 0x8C00+len(code)<=0x9000
    cpu[0x4C00:0x4C00+len(code)]=code
    changes=[]
    def patch(address,expected,target,opcode=0x7E):
        at=address-0x4000;n=linked[target]
        assert bytes(cpu[at:at+len(expected)])==expected,(hex(address),cpu[at:at+len(expected)].hex())
        replacement=bytes((opcode,n>>8,n&255))+b'\x01'*(len(expected)-3)
        cpu[at:at+len(expected)]=replacement
        changes.append(dict(address=address,before=expected.hex(),after=replacement.hex(),target=target))
    patch(s['GXSTART'],bytes.fromhex('7F19FB'),'GPSTART')
    patch(s['UIINIT'],bytes.fromhex('7F19DC'),'GPINIT',0xBD)
    patch(0x7716,bytes.fromhex('7B8034'),'GPASIC')
    patch(0x770E,bytes.fromhex('7B200F27FB'),'GPPHASEWAIT',0xBD)
    patch(0x773E,bytes.fromhex('7B200F27FB39'),'GPPHASEWAIT')
    old=b'Typestar BASIC 0.4.39-rx ';new=b'Typestar BASIC 0.4.40-th '
    assert len(old)==len(new) and cpu.count(old)==1
    banner=cpu.index(old);cpu=cpu.replace(old,new)
    allowed=set(range(0x4C00,0x4C00+len(code)))|set(range(banner,banner+len(old)))
    for p in changes:allowed.update(range(p['address']-0x4000,p['address']-0x4000+len(bytes.fromhex(p['before']))))
    assert len(cpu)==32768 and all(a==b or i in allowed for i,(a,b) in enumerate(zip(before,cpu)))
    m=json.loads((ROOT/'build/graphics-rx-test/manifest.json').read_text())
    m.update(version='0.4.40-th',sha256=hashlib.sha256(cpu).hexdigest(),thermal_bytes=len(code),
             status='One thermal glyph per boot; hardware validation pending',thermal_patches=changes,
             base_nh7_sha256=hashlib.sha256(raw).hexdigest(),thermal_scratch=bindings)
    m['statement_modules'].append(dict(name='thermal-test',origin=0x8C00,bytes=len(code)))
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s|bindings|linked,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print(len(code),'bytes',m['sha256'])

if __name__=='__main__':main()
