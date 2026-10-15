"""Link RND only into the complete array candidate, preserving .36 builders."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import re
from validate_array_tokens import assemble

def install(c,symbols,root):
    body=(root/'src/decimal-random.inc').read_text()
    local=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    equ=''.join(f'{k} EQU ${v:04X}\n' for k,v in symbols.items() if k not in local)
    blob,linked=assemble('decimal-random','        OPT H01\n'+equ+body)
    spans=[(0x47DF,linked['RNDDISPATCHEND'],0x4800),
           (0x54C4,linked['RNDTHENEND'],0x54DD),
           (0x9BC7,linked['RNDEND'],0x9C00)]
    for a,b,limit in spans:
        assert a<b<=limit,(hex(a),hex(b),hex(limit))
        c.m[a:b]=blob[a-0x47DF:b-0x47DF]
    # Fifth fixed-width function-name slot; original four IDs unchanged.
    assert symbols['FNPARSEEND']==0x47DA
    c.m[0x47DA:0x47DF]=b'\x03RND '
    a,b=symbols['FNMISS'],symbols['FNFALLBACK']
    region=bytes(c.m[a:b]);assert region.count(bytes.fromhex('C104'))==1
    c.m[a:b]=region.replace(bytes.fromhex('C104'),bytes.fromhex('C105'))
    a,b=symbols['FNENTRY'],symbols['FNMISS']
    region=bytes(c.m[a:b]);assert region.count(bytes.fromhex('7E43A2'))==1
    c.m[a:b]=region.replace(bytes.fromhex('7E43A2'),bytes.fromhex('7E47DF'))
    a,b=symbols['THENSTART'],symbols['THENEND']
    region=bytes(c.m[a:b]);needle=bytes.fromhex('815327')
    assert region.count(needle)==1
    p=a+region.index(needle)
    assert c.m[p+4]==0x20 # old BRA THENEXEC
    c.m[p:p+6]=bytes.fromhex('7E54C4010101')
    return dict(spans=[(a,b) for a,b,_ in spans],
                bytes=sum(b-a for a,b,_ in spans)+5,state=0x1EC6,
                syntax='RND(1)',result='0 <= value < 1; four decimal places')
