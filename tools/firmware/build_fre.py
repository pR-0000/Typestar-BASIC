"""Link FRE into a released font gap; preserve the validated .49 image."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
OUT=ROOT/'build/fre'
def main():
    raw=release_input('s70-basic-0.4.49-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='1b73f8cd7edc8ced313b59f44941f20669b3061295d0d8304bb72059858b272f'
    cpu=bytearray(raw[16384:]+raw[:16384]);s=json.loads((ROOT/'build/lcd-custom/symbols.json').read_text())
    code,l=assemble('basic-fre','        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())+(ROOT/'src/basic-fre.inc').read_text())
    a=0x912A;b=l['FREEND'];assert b<=0x924D and cpu[a-0x4000:b-0x4000]==b'\xff'*(b-a)
    cpu[a-0x4000:b-0x4000]=code[:b-a]
    at=s['FNENTRY']-0x4000;assert cpu[at:at+3]==b'\x7e'+s['SBENTRY'].to_bytes(2,'big')
    cpu[at:at+3]=b'\x7e'+l['FRENTRY'].to_bytes(2,'big')
    assert cpu.count(b'Typestar BASIC 0.4.49-dev')==1
    cpu=cpu.replace(b'Typestar BASIC 0.4.49-dev',b'Typestar BASIC 0.4.50-dev')
    m=json.loads((ROOT/'build/lcd-custom/manifest.json').read_text())
    m.update(version='0.4.50-dev',sha256=hashlib.sha256(cpu).hexdigest(),fre_bytes=b-a)
    m['statement_modules'].append(dict(name='FRE',origin=a,bytes=b-a))
    m['free_font_ranges'][1][0]=b
    OUT.mkdir(exist_ok=True)
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s|l,indent=2))
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2))
    print(m['version'],b-a,'bytes')
if __name__=='__main__':main()
