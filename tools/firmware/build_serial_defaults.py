"""Build .48 from hardware-validated .47: only banner and boot baud change."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/serial-defaults'
def main():
    raw=release_input('s70-basic-0.4.47-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='a66e2b6a0c2d0cff8890d885e2ee70ae6026a2cf5ff413740e235b080d24ffde'
    s=json.loads((ROOT/'build/serial-fast/symbols.json').read_text())
    cpu=bytearray(raw[16384:]+raw[:16384]);before=bytes(cpu)
    # SBBOOT calls IKBOOT, then LDAA #25/STAA BAUDCONST. Use divider zero.
    at=s['SBBOOT']-0x4000+3
    assert cpu[at:at+5]==b'\x86\x19\xB7'+s['BAUDCONST'].to_bytes(2,'big')
    cpu[at+1]=0
    old=b'Typestar BASIC 0.4.47-dev';new=b'Typestar BASIC 0.4.48-dev'
    assert cpu.count(old)==1
    cpu=cpu.replace(old,new)
    assert sum(a!=b for a,b in zip(before,cpu))==2
    OUT.mkdir(exist_ok=True)
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    report=dict(version='0.4.48-dev',sha256=hashlib.sha256(cpu).hexdigest(),
        base_nh7_sha256=hashlib.sha256(raw).hexdigest(),changed_bytes=2,
        default_baud=31250,default_format='7E1',added_rom_bytes=0,added_ram_bytes=0,
        boot_immediate_address=at+1+0x4000)
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report)
if __name__=='__main__':main()
