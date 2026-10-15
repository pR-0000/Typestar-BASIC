
from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import json,hashlib
from sys import path
path.insert(0,'tools')
from validate_array_tokens import assemble
root=Path(__file__).resolve().parents[2];
import os
os.chdir(root)
s=json.load(open('build/serial-defaults/symbols.json'))
raw=release_input('s70-basic-0.4.48-dev-canon-start-nh7.bin').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='cd4f61f5eaadfff97c3426f99fa711143eecd9260411d3ae8fc569f804388793'
cpu=bytearray(raw[16384:]+raw[:16384])
code,l=assemble('lcd-custom','        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())+Path('src/lcd-custom.inc').read_text())
print(hex(l['LCEND']),hex(l['LCFONTEND']))
assert l['LCEND']<=s['TRIBLANK'] and l['LCFONTEND']<=s['LCDEXTRAEND']
for a,b in [(s['TRILETTERS'],s['TRIBLANK']),(s['LCDEXTRA'],s['LCDEXTRAEND'])]:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
for a,b in [(0x4abc,l['LCEND']),(0x9120,l['LCFONTEND'])]:cpu[a-0x4000:b-0x4000]=code[a-0x4abc:b-0x4abc]
for old,new in [('LCDDISPATCH','LCDNEW'),('TRIBODY','LCTRI'),('TRIOCCUPIED','LCOCCUPIED'),('LXFONT','LCNATIVEFONT')]:
 a=s[old]-0x4000;cpu[a:a+3]=b'\x7e'+l[new].to_bytes(2,'big')
cpu=cpu.replace(b'Typestar BASIC 0.4.48-dev',b'Typestar BASIC 0.4.49-dev')
out=Path('build/lcd-custom');out.mkdir(exist_ok=True)
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|l,indent=2))
m=json.loads(Path('build/serial-fast/manifest.json').read_text())
for mod in m['statement_modules']:
 if mod['name']=='serial-config-lcd-1':mod['bytes']=0x9120-mod['origin']
m['statement_modules'] += [dict(name='lcd-custom-definitions',origin=0x4abc,bytes=l['LCEND']-0x4abc),dict(name='lcd-native-policy',origin=0x9120,bytes=l['LCFONTEND']-0x9120)]
m['free_font_ranges']=[[l['LCEND'],s['TRIBLANK']],[l['LCFONTEND'],s['LCDEXTRAEND']]]
m.update(dict(version='0.4.49-dev',sha256=hashlib.sha256(cpu).hexdigest(),font_bytes_removed=665,code_bytes=l['LCEND']-0x4abc+l['LCFONTEND']-0x9120,ram_added=9))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
