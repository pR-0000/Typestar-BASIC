"""Link FRE into a released font gap; preserve the validated .49 image."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
OUT=ROOT/'build/pi'
def main():
    raw=release_input('s70-basic-0.4.51-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='6ee9e6f13a3ab3b5294db9982313184a32d24b5c1de7bc2e481f6db6822410c6'
    cpu=bytearray(raw[16384:]+raw[:16384]);s=json.loads((ROOT/'build/sqr/symbols.json').read_text())
    code,l=assemble('basic-pi','        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())+(ROOT/'src/basic-pi.inc').read_text())
    spans=[(0x4934,l['PIPARSEEND'],s['TRISPACE']),(0x9015,l['PIEND'],s['SBBOOT'])]
    for a,b,end in spans:
        assert b<=end,(hex(b),hex(end))
        cpu[a-0x4000:b-0x4000]=code[a-0x4934:b-0x4934]
    at=s['FNENTRY']-0x4000;assert cpu[at:at+3]==b'\x7e'+s['SQENTRY'].to_bytes(2,'big')
    cpu[at:at+3]=b'\x7e'+l['PIENTRY'].to_bytes(2,'big')
    cpu=cpu.replace(b'Typestar BASIC 0.4.51-dev',b'Typestar BASIC 0.4.52-dev')
    m=json.loads((ROOT/'build/sqr/manifest.json').read_text())
    m.update(version='0.4.52-dev',sha256=hashlib.sha256(cpu).hexdigest(),pi_bytes=sum(b-a for a,b,_ in spans))
    # Both patches replace already occupied legacy code; no new RAM or arena use.
    m['pi_spans']=[(a,b) for a,b,_ in spans]
    OUT.mkdir(exist_ok=True)
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s|l,indent=2))
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2))
    print(m['version'],m['pi_bytes'],'bytes')
if __name__=='__main__':main()
