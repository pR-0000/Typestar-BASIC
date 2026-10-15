"""Patch the validated .45 without moving prior modules or changing UART clocks."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
OUT=ROOT/'build/serial-framing';VERSION='0.4.46-dev'

def main():
    OUT.mkdir(exist_ok=True)
    raw=release_input('s70-basic-0.4.45-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='a0a0dacab614f86dbd5d9008ef51d1df4f384a6ec3ab7038ff1a157f3d2b9575'
    cpu=bytearray(raw[16384:]+raw[:16384]);before=bytes(cpu)
    s=json.loads((ROOT/'build/serial-config/symbols.json').read_text())
    source='        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())
    code,linked=assemble('serial-framing',source+(ROOT/'src/serial-framing.inc').read_text())
    assert linked['CFEND']<=0x9000 and linked['CFTAILEND']<=0x9277
    spans=[(0x8FA5,linked['CFEND']),(0x924D,linked['CFTAILEND'])]
    m=json.loads((ROOT/'build/serial-config/manifest.json').read_text())
    for module in m['runtime_segments']+m['loop_modules']+m['statement_modules']:
        for a,b in spans:assert module['origin']+module['bytes']<=a or module['origin']>=b,module
    changes=[]
    def patch(address,expected,replacement):
        at=address-0x4000;assert cpu[at:at+len(expected)]==expected,(hex(address),cpu[at:at+len(expected)].hex())
        assert len(expected)==len(replacement)
        cpu[at:at+len(expected)]=replacement
        changes.append(dict(address=address,before=expected.hex(),after=replacement.hex()))
    def jump(op,target):return bytes([op])+target.to_bytes(2,'big')
    patch(s['UIINIT'],jump(0xBD,s['SBBOOT']),jump(0xBD,linked['CFBOOT']))
    patch(s['EXECUTE'],jump(0x7E,s['SBDISPATCH']),jump(0x7E,linked['CFDISPATCH']))
    lo=s['SERIALINIT']-0x4000;hi=s['SERIALCLOSE']-0x4000
    part=bytes(cpu[lo:hi]);needle=bytes.fromhex('8604971E');assert part.count(needle)==1
    patch(lo+0x4000+part.index(needle),needle,jump(0xBD,linked['CFAPPLY'])+b'\x01')
    for a,b in spans:cpu[a-0x4000:b-0x4000]=code[a-0x8FA5:b-0x8FA5]
    old=b'Typestar BASIC 0.4.45-dev';new=b'Typestar BASIC 0.4.46-dev'
    patch(cpu.index(old)+0x4000,old,new)
    allowed={p-0x4000 for a,b in spans for p in range(a,b)}
    for p in changes:allowed.update(range(p['address']-0x4000,p['address']-0x4000+len(bytes.fromhex(p['before']))))
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(before,cpu)))
    used=sum(b-a for a,b in spans)
    m.update(version=VERSION,sha256=hashlib.sha256(cpu).hexdigest(),framing_bytes=used,
        framing_spans=spans,framing_patches=changes,status='Configurable parity/stop; hardware test pending')
    m['statement_modules'] += [dict(name=f'serial-framing-{i}',origin=a,bytes=b-a) for i,(a,b) in enumerate(spans)]
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s|linked,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print(VERSION,used,m['sha256'])

if __name__=='__main__':main()
