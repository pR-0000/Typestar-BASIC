"""Repack keyboard maps only; keep .59 paper/native code at fixed addresses."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble

base=ROOT/'build/paper-names'
out=ROOT/'build/keyboard-delta';out.mkdir(exist_ok=True)
raw=release_input('s70-basic-0.4.59-dev-canon-start-nh7.bin').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='aedcb86390fec11353153be19c9c91a1c4437ddc8588411eced617b74ce6695e'
original=raw[16384:]+raw[:16384];cpu=bytearray(original)
s=json.loads((base/'symbols.json').read_text())
m=json.loads((base/'manifest.json').read_text())
reference=ROOT/'build/paper-geometry'
r=json.loads((reference/'symbols.json').read_text())
image=(reference/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
rows=[image[r['KEYMAP'+str(i)]-0x4000+j:r['KEYMAP'+str(i)]-0x4000+j+44]
      for i in range(10) for j in range(0,176,44)]
assert all(len(row)==44 for row in rows)
# Deterministic Prim tree. Each new node inherits only from an existing node,
# so there are no cycles. Equal mappings produce an empty difference node.
parents={0:None};differences={0:[]}
while len(parents)<40:
    distance,parent,child=min((sum(x!=y for x,y in zip(rows[a],rows[b])),a,b)
                             for a in parents for b in range(40) if b not in parents)
    parents[child]=parent
    differences[child]=[(k,y) for k,(x,y) in enumerate(zip(rows[parent],rows[child])) if x!=y]
start=s['KPACK'];end=m['keyboard_packed']['free_start']
source='        OPT H01\n'+''.join(f'{k} EQU ${s[k]:04X}\n' for k in
        ('KLOCALE','KMODE','KRAW','KBDNONE','KBDRETURN'))
source+=f'        ORG ${start:04X}\n'+(ROOT/'src/keyboard-delta.inc').read_text()
source+='KDTABLE FDB '+','.join('KDN'+str(i) for i in range(40))+'\n'
for i in range(40):
    source+='KDN'+str(i)+' FCB '
    if i==0:
        source+=','.join(str(v) for v in [255,*rows[0]])+'\n'
    else:
        source+=','.join(str(v) for pair in differences[i] for v in pair)+(',' if differences[i] else '')+'254\n'
        source+='        FDB KDN'+str(parents[i])+'\n'
source+='KDDATAEND EQU *\n'
code,labels=assemble('keyboard-delta',source)
assert len(code)<end-start
cpu[start-0x4000:end-0x4000]=code+b'\xff'*(end-start-len(code))
old=b'Typestar BASIC 0.4.59-dev';new=b'Typestar BASIC 0.4.60-dev'
assert cpu.count(old)==1
banner=cpu.index(old);cpu[banner:banner+len(old)]=new
assert len(cpu)==32768
assert all(a==b or start<=i+0x4000<end or banner<=i<banner+len(old)
           for i,(a,b) in enumerate(zip(original,cpu)))
gain=end-start-len(code)
m.update(version='0.4.60-dev',sha256=hashlib.sha256(cpu).hexdigest(),
         status='Keyboard delta compression; paper and native paths unchanged',
         keyboard_delta=dict(bytes=len(code),code_bytes=labels['KDCODEEND']-start,
                             recovered_bytes=gain,free_start=start+len(code),free_end=end,
                             inherited_differences=sum(map(len,differences.values())),parents=parents),
         known_free_fragmented_bytes=m['known_free_fragmented_bytes']+gain)
for module in m['statement_modules']:
    if module['name']=='keyboard-packed':
        module.update(name='keyboard-delta',bytes=len(code))
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s|labels,indent=2))
(out/'manifest.json').write_text(json.dumps(m,indent=2))
print(json.dumps(m['keyboard_delta'],indent=2))
