"""Rename public paper commands only; preserve .58 code and hardware paths."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble

base=ROOT/'build/paper-line-linked';out=ROOT/'build/paper-names';out.mkdir(exist_ok=True)
raw=release_input('s70-basic-0.4.58-dev-canon-start-nh7.bin').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='63123b20763624f734bb0e6a56d599adf7272a19fce576183e3eeca3fc7f2766'
original=raw[16384:]+raw[:16384];cpu=bytearray(original)
s=json.loads((base/'symbols.json').read_text())
source='        OPT H01\n'+''.join(f'{k} EQU ${s[k]:04X}\n' for k in ('PXNAME','LNNAME'))+(ROOT/'src/paper-command-names.inc').read_text()
code,_=assemble('paper-command-names',source)
changed=set()
holes=[]
for symbol,old,new in [('PXNAME',b'PBOX\0',b'BOX\0'),('LNNAME',b'PLINE\0',b'LINE\0')]:
    a=s[symbol];i=a-0x4000
    assert cpu[i:i+len(old)]==old
    assert code[a-s['PXNAME']:a-s['PXNAME']+len(new)]==new
    cpu[i:i+len(old)]=new+b'\xff'
    changed.update(range(i,i+len(old)));holes.append(a+len(new))
old=b'Typestar BASIC 0.4.58-dev';new=b'Typestar BASIC 0.4.59-dev'
assert cpu.count(old)==1
i=cpu.index(old);cpu[i:i+len(old)]=new;changed.update(range(i,i+len(old)))
assert len(cpu)==32768 and all(a==b or i in changed for i,(a,b) in enumerate(zip(original,cpu)))
m=json.loads((base/'manifest.json').read_text())
m.update(version='0.4.59-dev',sha256=hashlib.sha256(cpu).hexdigest(),
         status='BOX/LINE naming update; native paths unchanged from validated .58',
         public_paper_commands={'box':'BOX','line':'LINE'},
         paper_code_bytes=m['paper_code_bytes']-2,
         known_free_fragmented_bytes=m['known_free_fragmented_bytes']+2,
         renamed_keyword_holes=holes,
         changes=[dict(address=f'{a+0x4000:04X}',old=original[a],new=cpu[a]) for a in sorted(changed) if original[a]!=cpu[a]])
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('Built .59: BOX and LINE; 2 isolated bytes freed; no aliases')
