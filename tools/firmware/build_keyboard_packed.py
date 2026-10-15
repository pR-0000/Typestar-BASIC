"""Losslessly share keyboard table blocks; preserve the .57 graphics engine."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib
import json
from validate_array_tokens import ROOT, assemble

base = ROOT/'build/paper-geometry'
out = ROOT/'build/keyboard-packed'
out.mkdir(exist_ok=True)
s = json.loads((base/'symbols.json').read_text())
raw = release_input('s70-basic-0.4.57-dev-canon-start-nh7.bin').read_bytes()
assert hashlib.sha256(raw).hexdigest() == '4447056116750bc6a7e9d47f9d831134efe01841fb2c687b328e663079471153'
cpu = bytearray(raw[16384:]+raw[:16384])
start, end = s['KEYTABLES'], s['KEYMAP9']+176
assert end == s['KICON'] and end-start == 1780
blocks = []
indices = []
for locale in range(10):
    a = s['KEYMAP'+str(locale)]-0x4000
    for offset in range(0,176,22):
        block = bytes(cpu[a+offset:a+offset+22])
        if block not in blocks:
            blocks.append(block)
        indices.append(blocks.index(block))
source = '        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())
source += f'        ORG ${start:04X}\n'+(ROOT/'src/keyboard-packed.inc').read_text()
source += 'KPTABLE FDB '+','.join('KPB'+str(i) for i in indices)+'\n'
for i,block in enumerate(blocks):
    source += 'KPB'+str(i)+' FCB '+','.join('$%02X'%b for b in block)+'\n'
source += 'KPDATAEND EQU *\n'
code,labels = assemble('keyboard-packed',source)
assert len(code)<end-start
cpu[start-0x4000:end-0x4000] = code+b'\xff'*(end-start-len(code))
entry=s['KBDCHAR']+4
assert cpu[entry-0x4000:entry-0x4000+3] == b'\xf6'+s['KLOCALE'].to_bytes(2,'big')
cpu[entry-0x4000:entry-0x4000+3] = b'\x7e'+start.to_bytes(2,'big')
# Keep the old lookup tail intact pending a separate reference audit.
cpu=cpu.replace(b'Typestar BASIC 0.4.57-dev',b'Typestar BASIC 0.4.58-dev')
assert len(cpu)==32768
m=json.loads((base/'manifest.json').read_text())
m.update(version='0.4.58-dev',sha256=hashlib.sha256(cpu).hexdigest(),
         status='Keyboard compression candidate; not yet packaged',
         keyboard_packed=dict(original_bytes=end-start,packed_bytes=len(code),
                              code_bytes=labels['KPACKEND']-start,unique_blocks=len(blocks),
                              free_start=start+len(code),free_end=end,free_bytes=end-start-len(code)),
         known_free_fragmented_bytes=63+end-start-len(code))
m['statement_modules'].append(dict(name='keyboard-packed',origin=start,bytes=len(code)))
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|labels,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print(json.dumps(m['keyboard_packed'],indent=2))
