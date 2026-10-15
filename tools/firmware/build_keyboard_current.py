"""0.4.38 editor patch on pinned 0.4.37, preserving the earlier release."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import assemble
from validate_named_array_heap import ROOT

def main():
    out=ROOT/'build/keyboard-current';out.mkdir(exist_ok=True)
    raw=release_input('s70-basic-0.4.37-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='2625b63227746eb1c3eca47b7ee163b36ff5758cb7fe9f5ba4e185ae7c324d19'
    cpu=bytearray(raw[16384:]+raw[:16384])
    symbols=json.loads((ROOT/'build/array-current/symbols.json').read_text())
    equ=''.join(f'{k} EQU ${v:04X}\n' for k,v in symbols.items())
    code,linked=assemble('editor-clear-left','        OPT H01\n'+equ+(ROOT/'src/editor-clear-left.inc').read_text())
    assert linked['EDCLEAREND']<=0x9E00
    manifest=json.loads((ROOT/'build/array-current/manifest.json').read_text())
    for m in manifest['loop_modules']+manifest['statement_modules']:
        assert m['origin']+m['bytes']<=0x9DCB or m['origin']>=linked['EDCLEAREND'],m
    start=symbols['EDNOTRIGHT']-0x4000
    assert cpu[start:start+2]==bytes.fromhex('8108') and cpu[start+2]==0x26
    cpu[start:start+4]=bytes.fromhex('7E9DCB01')
    cpu[0x5DCB:0x5DCB+len(code)]=code
    cpu=cpu.replace(b'Typestar BASIC 0.4.37-dev',b'Typestar BASIC 0.4.38-dev')
    manifest.update(version='0.4.38-dev',sha256=hashlib.sha256(cpu).hexdigest(),
        editor_clear_left_bytes=len(code))
    manifest['statement_modules'].append(dict(name='editor-clear-left',origin=0x9DCB,bytes=len(code)))
    (out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (out/'symbols.json').write_text(json.dumps(symbols,indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Keyboard candidate',len(code),'bytes',manifest['sha256'])

if __name__=='__main__':main()
