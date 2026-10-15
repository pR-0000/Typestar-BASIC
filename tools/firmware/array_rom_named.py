"""Place named-array helpers in retired .36 code, in the private CPU only."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import re
import json
import subprocess
import os


def install(c, symbols, root, out, assembler):
    full = os.environ.get('TYPESTAR_ARRAY_ROM_FULL') == '1'
    private_end = symbols['ARACCESSEND']
    retired_private = (symbols['ARRAY_CREATE'],symbols['ARRAY_NAMED_END'])
    retired_read = (symbols['ARATOM'],symbols['ARADDRESS'])
    body = (root/'src/array-named-heap.inc').read_text()
    reader = (root/'src/array-access.inc').read_text().split('ARADDRESS JSR',1)[0]
    allocator = (root/'src/array-create.asm').read_text().replace('        INCLUDE "src/array-index.asm"','')
    local = set(re.findall(r'^([A-Z][A-Z0-9_]*)\b', body, re.M))
    local.update(re.findall(r'^([A-Z][A-Z0-9_]*)\b', allocator, re.M))
    local.update(re.findall(r'^([A-Z][A-Z0-9_]*)\b', reader, re.M))
    tail = ''
    if full:
        tail = (root/'src/array-index.asm').read_text().replace('ORG $6000','ORG $9900')
        tail += (root/'src/array-dim.inc').read_text()
        tail += 'ARADDRESS JSR'+(root/'src/array-access.inc').read_text().split('ARADDRESS JSR',1)[1]
        local.update(re.findall(r'^([A-Z][A-Z0-9_]*)\b',tail,re.M))
    equ = ''.join(f'{k} EQU ${v:04X}\n' for k,v in symbols.items() if k not in local)
    find, create = body.split('ARRAY_NAMED_CREATE\n',1)
    entry, reserve = create.split('\nANRESERVE\n',1)
    reserve, errors = reserve.split('ANDUPLICATE LDAA',1)
    # Keep each short conditional branch inside its own fragment. Only the
    # successful lookup crosses from the validation fragment to allocation.
    entry = entry.replace('        BEQ ANRESERVE\n        SEC',
                          '        BNE ANSTATUS\n        JMP ANRESERVE\nANSTATUS SEC')
    body = find.replace('ARRAY_NAMED_FIND LDD','        ORG $44BA\nARRAY_NAMED_FIND LDD')
    body += 'ANFINDEND EQU *\n        ORG $451A\nANRESERVE\n'+reserve
    body += 'ANRESERVEEND EQU *\n        ORG $4F96\n'+allocator
    body += '\n        ORG $55D2\nARRAY_NAMED_CREATE\n'+entry
    body += '\nANDUPLICATE LDAA'+errors
    body += '\n        ORG $67BC\n'+reader+'\nARREADEND EQU *\n'
    body += tail
    source = out/'named-rom.asm'
    source.write_text('        OPT H01\n'+equ+body, encoding='ascii')
    run = subprocess.run([str(assembler), '-W', '-B'+str(out/'named-rom.bin'),
                          '-L'+str(out/'named-rom.lst'), str(source)], capture_output=True,text=True)
    assert run.returncode == 0, run.stdout+run.stderr
    table = (out/'named-rom.lst').read_text().split('SYMBOL TABLE')[1]
    linked = {n:int(v,16) for n,v in re.findall(
        r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',table)}
    payload = (out/'named-rom.bin').read_bytes()
    # The token validator still calls the old CRC byte primitive twice.
    # Preserve this 29-byte position-independent leaf in FNAPPLY's tail gap
    # before reclaiming the larger obsolete CRC traversal.
    leaf = bytes(c.m[0x44FD:0x451A])
    manifest = json.loads((root/'build/token-current/manifest.json').read_text())
    apply = next(m for m in manifest['statement_modules'] if m['name']=='FNAPPLYSTART')
    assert apply['origin']+apply['bytes'] == 0x43E2
    assert len(leaf) == 29 and leaf[-1] == 0x39
    region = bytes(c.m[0x5620:0x56D4])
    assert region.count(bytes.fromhex('BD44FD')) == 2
    c.m[0x43E2:0x43FF] = leaf
    c.m[0x5620:0x56D4] = region.replace(bytes.fromhex('BD44FD'),bytes.fromhex('BD43E2'))
    # Preserve the CRC entry JMP. The old 8-bit line formatter and SLOT
    # search are replaced by token RFORMAT/TSEEK. Their old bodies can be
    # reused, but KFOR and CLEARALL immediately following them remain live.
    # Never copy assembler padding into ROM.
    assert c.m[0x44B7] == 0x7E and c.m[0x5749] == 0x7E
    spans = [(0x44BA,linked['ANFINDEND']),
             (0x451A,linked['ANRESERVEEND']),
             (0x4F96,linked['ARRAY_CREATE_END']),
             (0x55D2,linked['ARRAY_NAMED_END']),
             (0x67BC,linked['ARREADEND'])]
    assert spans[0][1] == 0x450F
    assert spans[0][1] <= symbols['FORMATLINE']
    assert spans[1][1] <= symbols['KFOR']
    # The LCD module ends at 4F96; BASIC begins at 5000. This interval is
    # original paper-font data, not blank ROM. Account for that explicitly.
    base = json.loads((root/'build/canon-basic/manifest.json').read_text())
    lcd = next(m for m in base['modules'] if m['name']=='lcd-triangle')
    assert lcd['origin']+lcd['bytes'] == 0x4F96
    assert spans[2][1] == 0x4FF8 and spans[2][1] <= 0x5000
    assert spans[3][1] <= symbols['CLEARALL']
    assert spans[4][1] == 0x67FD and spans[4][1] <= 0x6800
    assert bytes(c.m[0x67C2:0x6800]) == b'\xff'*62
    if full:
        assert linked['ARACCESSEND'] == 0x9BC7
        spans.append((0x9900,linked['ARACCESSEND']))
    for module in manifest['runtime_segments']+manifest['loop_modules']+manifest['statement_modules']:
        lo,hi = module['origin'],module['origin']+module['bytes']
        assert all(end <= lo or start >= hi for start,end in spans), module
    for start,end in spans:
        c.m[start:end] = payload[start-0x44BA:end-0x44BA]
    # All external calls are absolute JSRs inside the private array module.
    # Its original named helpers are left in place but no longer called.
    module = bytes(c.m[0x1000:symbols['ARACCESSEND']])
    counts = {}
    for name in ('ARRAY_NAMED_FIND','ARRAY_NAMED_CREATE','ARRAY_CREATE'):
        old,new = symbols[name],linked[name]
        needle = bytes((0xBD,old>>8,old&255))
        counts[name] = module.count(needle)
        assert counts[name] > 0
        module = module.replace(needle,bytes((0xBD,new>>8,new&255)))
        symbols[name] = new
    c.m[0x1000:0x1000+len(module)] = module
    entry = symbols['FNFALLBACK']+3
    old,new = symbols['ARATOM'],linked['ARATOM']
    assert bytes(c.m[entry:entry+3]) == bytes((0x7E,old>>8,old&255))
    c.m[entry:entry+3] = bytes((0x7E,new>>8,new&255))
    if full:
        for entry,name in ((symbols['EXECUTE'],'DIMDISPATCH'),(0xA006,'ARLET')):
            assert c.m[entry] == 0x7E
            target = linked[name]
            c.m[entry:entry+3] = bytes((0x7E,target>>8,target&255))
        symbols['ARRAY_ELEMENT'] = linked['ARRAY_ELEMENT']
    # Fail immediately if any call still falls back to the private copies.
    # This makes the CPU tests exercise the ROM placement, not just its bytes.
    original_step = c.step
    def checked_step():
        if full:
            assert not 0x1000 <= c.pc < private_end, ('private array execution',hex(c.pc))
        assert not retired_private[0] <= c.pc < retired_private[1], ('stale array call',hex(c.pc))
        assert not retired_read[0] <= c.pc < retired_read[1], ('stale array reader',hex(c.pc))
        return original_step()
    c.step = checked_step
    return dict(spans=spans, bytes=sum(b-a for a,b in spans),
                crc_leaf=[0x43E2,0x43FF], redirected_calls=counts,
                additional_font_bytes=98,
                read_gateway=[0x67BC,0x67FD],
                full_placement=full,
                linked_symbols={name:linked[name] for name in local if name in linked},
                limitation='CPU placement only; full startup/serial/release checks pending.')
