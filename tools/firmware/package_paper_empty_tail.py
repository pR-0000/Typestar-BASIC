"""Package the CPU-validated .87 candidate in IC8 order; never flash."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[2];base=root/'build/paper-empty-tail'
cpu=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
m=json.loads((base/'manifest.json').read_text());v=json.loads((base/'validation.json').read_text())
assert v['result']=='PASS' and len(cpu)==32768
assert hashlib.sha256(cpu).hexdigest()==m['sha256']=='330d00173287c65576bb3ee988008750c2953265929441964a08711af59859da'
raw=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.87-dev-canon-start-nh7'
(root/'release'/f'{name}.bin').write_bytes(raw)
report=dict(version=m['version'],status='Hardware test; physical validation pending',cpu_sha256=m['sha256'],nh7_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),explicit_free_bytes=m['explicit_free_bytes'],ram_free=5951,validation=v,limitations=['Trailing empty tiles and wholly empty BASIC bands only; interior/leading gaps unchanged','Serial graphics and LPRINT are unchanged','No new Y calibration'])
(root/'release'/f'{name}-manifest.json').write_text(json.dumps(report,indent=2))
print(report['nh7_sha256'])
