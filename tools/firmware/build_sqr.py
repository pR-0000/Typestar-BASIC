"""Link FRE into a released font gap; preserve the validated .49 image."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
OUT=ROOT/'build/sqr'
def main():
    raw=release_input('s70-basic-0.4.50-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='470f94201cebcda9550e0d1095b9afb3ea1d849c294d8e554b3611e87149fa22'
    cpu=bytearray(raw[16384:]+raw[:16384]);s=json.loads((ROOT/'build/fre/symbols.json').read_text())
    code,l=assemble('basic-sqr','        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())+(ROOT/'src/basic-sqr.inc').read_text())
    spans=[(0x4B93,l['SQPARSEEND'],0x4C28),(0x9192,l['SQEND'],0x924D),(0x9003,l['SQSAFEEND'],s['SBBOOT'])]
    for a,b,end in spans:
        assert b<=end,(hex(b),hex(end))
        if a!=0x9003:assert cpu[a-0x4000:b-0x4000]==b'\xff'*(b-a)
        cpu[a-0x4000:b-0x4000]=code[a-0x4B93:b-0x4B93]
    at=s['FNENTRY']-0x4000;assert cpu[at:at+3]==b'\x7e'+s['FRENTRY'].to_bytes(2,'big')
    cpu[at:at+3]=b'\x7e'+l['SQENTRY'].to_bytes(2,'big')
    cpu=cpu.replace(b'Typestar BASIC 0.4.50-dev',b'Typestar BASIC 0.4.51-dev')
    m=json.loads((ROOT/'build/fre/manifest.json').read_text())
    m.update(version='0.4.51-dev',sha256=hashlib.sha256(cpu).hexdigest(),sqr_bytes=sum(b-a for a,b,_ in spans))
    m['statement_modules'] += [dict(name='SQR'+str(i),origin=a,bytes=b-a) for i,(a,b,_) in enumerate(spans[:2])]
    m['free_font_ranges']=[[b,end] for _,b,end in spans[:2]]
    OUT.mkdir(exist_ok=True)
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s|l,indent=2))
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2))
    print(m['version'],m['sqr_bytes'],'bytes')
if __name__=='__main__':main()
