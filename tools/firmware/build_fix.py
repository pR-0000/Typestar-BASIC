"""Link FRE into a released font gap; preserve the validated .49 image."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
OUT=ROOT/'build/fix'
def main():
    raw=release_input('s70-basic-0.4.53-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='25659c95f59a00bee404eec80206b5b1d08e872af1160ef455ec4a5c07fce510'
    cpu=bytearray(raw[16384:]+raw[:16384]);s=json.loads((ROOT/'build/numeric-dispatch/symbols.json').read_text())
    code,l=assemble('basic-fix','        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())+(ROOT/'src/basic-fix.inc').read_text())
    a=0x8E9B;b=l['FXEND'];assert b<=0x8EE6
    assert cpu[a-0x4000:b-0x4000]==b'\xff'*(b-a)
    cpu[a-0x4000:b-0x4000]=code[:b-a]
    slot=s['NFTABLEEND']-0x4000;assert cpu[slot:slot+6]==b'\xff'*6
    cpu[slot:slot+6]=b'\x03FIX  '
    at=s['NFAPPLY']-0x4000;assert cpu[at:at+2]==b'\xc1\x05'
    oldbranch=cpu[at+2:at+4]
    # Preserve the original BCS at +2 by patching its caller, not NFAPPLY.
    p=s['FNENTRY'];q=s['FNBADARG'];part=bytes(cpu[p-0x4000:q-0x4000]);old=b'\x7e'+s['NFAPPLY'].to_bytes(2,'big')
    assert part.count(old)==1;at=p-0x4000+part.index(old);cpu[at:at+3]=b'\x7e'+l['FXDISPATCH'].to_bytes(2,'big')
    p=s['FNMISS'];q=s['FNFALLBACK'];part=bytes(cpu[p-0x4000:q-0x4000]);assert part.count(b'\xc1\x09')==1
    at=p-0x4000+part.index(b'\xc1\x09');cpu[at:at+2]=b'\xc1\x0a'
    cpu=cpu.replace(b'Typestar BASIC 0.4.53-dev',b'Typestar BASIC 0.4.54-dev')
    m=json.loads((ROOT/'build/numeric-dispatch/manifest.json').read_text())
    m.update(version='0.4.54-dev',sha256=hashlib.sha256(cpu).hexdigest(),fix_bytes=b-a+6)
    m['dispatch_free'][0][0]=b;m['dispatch_free'][3][0]+=6
    OUT.mkdir(exist_ok=True)
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s|l,indent=2))
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2))
    print(m['version'],m['fix_bytes'],'bytes')
if __name__=='__main__':main()
