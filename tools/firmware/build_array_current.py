"""Build a complete ROM-resident array candidate; never flashes or publishes."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib
import json
import os
from pathlib import Path
os.environ['TYPESTAR_ARRAY_ROM_FULL'] = '1'
from validate_named_array_heap import setup, ROOT, emu
from validate_array_tokens import install


def main():
    out = ROOT/'build/array-current'
    out.mkdir(exist_ok=True)
    c, symbols, _, base = setup()
    tokens = install(c,include_rnd=True)
    from link_array_random import install as link_random
    random = link_random(c,symbols,ROOT)
    cpu = bytes(c.m[0x4000:0xC000])
    original = base[16384:]+base[:16384]
    # All retained startup/motor/keyboard code below the deliberately
    # replaced editor region, and the upper services, remain identical.
    for lo,hi in ((0x4000,0x4200),(0x6800,0x9900),(random['spans'][-1][1],0x9C00),(0xAC00,0xC000)):
        assert cpu[lo-0x4000:hi-0x4000] == original[lo-0x4000:hi-0x4000]
    assert cpu.count(b'Typestar BASIC 0.4.36-dev') == 1
    cpu = cpu.replace(b'Typestar BASIC 0.4.36-dev',b'Typestar BASIC 0.4.37-dev')
    placement = json.loads((ROOT/'build/array-heap/named-rom-placement.json').read_text())
    assert placement['full_placement'] and placement['bytes'] == 1038
    manifest = json.loads((ROOT/'build/token-current/manifest.json').read_text())
    manifest.update(version='0.4.37-dev',status='Complete ROM placement; NOT hardware validated',
        sha256=hashlib.sha256(cpu).hexdigest(),array_placement=placement,tokens=tokens,random=random)
    for m in manifest['statement_modules']:
        if m['name']=='FNPEEKSTART':m['origin']=tokens['peek_start']
    manifest['statement_modules'] += [dict(name=f'array-{i}',origin=a,bytes=b-a)
        for i,(a,b) in enumerate(placement['spans'])]
    manifest['statement_modules'].append(dict(name='crc-byte-relocated',origin=0x43E2,bytes=29))
    manifest['statement_modules'] += [dict(name=f'random-{i}',origin=a,bytes=b-a)
        for i,(a,b) in enumerate(random['spans'])]
    (out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (out/'symbols.json').write_text(json.dumps(emu.S,indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Complete array ROM: {placement["bytes"]} bytes, CPU SHA256 {manifest["sha256"]}')


if __name__ == '__main__':main()
