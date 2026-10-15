""".81: allow LCD native codes 32..255; no new RAM or tokens."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
base=ROOT/'build/paper-spacing'; out=ROOT/'build/lcd-native';out.mkdir(exist_ok=True)
cpu=bytearray((base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes())
assert hashlib.sha256(cpu).hexdigest()=='c8fcd220e9c52f74f07ad4860943938f4fa1e6e89d0e63ec6b8bfa5cc22a01f4'
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text())
a=s['LCDPRINTABLE']-0x4000
assert cpu[a:a+10]==bytes.fromhex('8120253a817e2236367d')
# Keep instruction layout and condition flags: CMPA #255 never rejects a byte.
cpu[a+5]=255
old=b'Typestar BASIC 0.4.80-dev';at=cpu.index(old)
cpu[at:at+len(old)]=b'Typestar BASIC 0.4.81-dev'
m.update(version='0.4.81-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='Awaiting LCD native-code validation',lcd_native_range=[32,255])
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print(m['sha256'])
