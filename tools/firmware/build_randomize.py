"""Link FRE into a released font gap; preserve the validated .49 image."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
OUT=ROOT/'build/randomize'
def main():
    raw=release_input('s70-basic-0.4.54-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='e8c079b4a58471ea10bbf3de6f4bf2ac8a53a08b091ef02b2fa3872a431db636'
    cpu=bytearray(raw[16384:]+raw[:16384]);s=json.loads((ROOT/'build/fix/symbols.json').read_text())
    code,l=assemble('basic-randomize','        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())+(ROOT/'src/basic-randomize.inc').read_text())
    a=0x8F13;b=l['RZEND'];assert b<=0x8F5E
    assert cpu[a-0x4000:b-0x4000]==b'\xff'*(b-a)
    cpu[a-0x4000:b-0x4000]=code[:b-a]
    at=s['LCDDISPATCH']-0x4000;assert cpu[at:at+3]==b'\x7e'+s['LCDNEW'].to_bytes(2,'big')
    cpu[at:at+3]=b'\x7e'+l['RZDISPATCH'].to_bytes(2,'big')
    cpu=cpu.replace(b'Typestar BASIC 0.4.54-dev',b'Typestar BASIC 0.4.55-dev')
    m=json.loads((ROOT/'build/fix/manifest.json').read_text())
    m.update(version='0.4.55-dev',sha256=hashlib.sha256(cpu).hexdigest(),randomize_bytes=b-a)
    m['dispatch_free'][1][0]=b
    OUT.mkdir(exist_ok=True)
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s|l,indent=2))
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2))
    print(m['version'],m['randomize_bytes'],'bytes')
if __name__=='__main__':main()
