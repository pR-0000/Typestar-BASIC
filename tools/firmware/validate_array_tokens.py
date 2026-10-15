"""Append DIM in a private CPU image; leave the released token ABI unchanged.

The extra dictionary entry displaces PEEK by six bytes. Adjust its checked
absolute entry reference; its relative branch and outgoing calls stay valid.
Array routines themselves still live at emulator-only address 1000.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import binascii
import hashlib
import json
import re
import subprocess
from validate_named_array_heap import setup, ROOT, OUT, emu
from tokenized_program import WORDS, pack


def assemble(name, source):
    path = OUT / (name + '.asm')
    path.write_text(source, encoding='ascii')
    run = subprocess.run([str(emu.RESEARCH/'tmp/m680x-tools/a09.exe'), '-W',
        '-B'+str(OUT/(name+'.bin')), '-L'+str(OUT/(name+'.lst')), str(path)],
        capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    table = (OUT/(name+'.lst')).read_text().split('SYMBOL TABLE')[1]
    symbols = {n:int(v,16) for n,v in re.findall(
        r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b', table)}
    return (OUT/(name+'.bin')).read_bytes(), symbols


def install(c, include_rnd=False):
    before = bytes(c.m)
    assert len(WORDS) == 35 and 'DIM' not in WORDS
    words = WORDS + ['DIM'] + (['RND'] if include_rnd else [])
    table = f'\nTOKENCOUNT EQU {len(words)}\nTOKENPTRS\n'
    table += ''.join(f'        FDB TW{i}\n' for i in range(len(words)))
    table += ''.join(f'TW{i} FCC "{word}"\n        FCB 0\n' for i,word in enumerate(words))
    token, symbols = assemble('tokens-dim', (ROOT/'src/token-records.asm').read_text()+table)
    end = 0xA800 + len(token)
    assert end == (0xABE0 if include_rnd else 0xABDA)
    # PEEK is a separate 21-byte leaf. Its only absolute incoming reference
    # is FNAPPLY's JMP. Internal BCS is relative, outgoing jumps unchanged.
    old, size = 0xABD4, 21
    peek = bytes(c.m[old:old+size])
    assert peek[:3] == bytes.fromhex('BDA400')
    needle = bytes.fromhex('7EABD4')
    region = bytes(c.m[0x43A2:0x43E2])
    assert region.count(needle) == 1
    target = 0x43A2 + region.index(needle)
    c.m[target:target+3] = bytes((0x7E, end>>8, end&255))
    c.m[0xA800:end] = token
    c.m[end:end+size] = peek
    assert end + size <= 0xAC00
    allowed = set(range(0xA800,end+size)) | set(range(target,target+3))
    assert all(a in allowed for a in range(65536) if before[a] != c.m[a])
    assert bytes(c.m[0x6800:0x6859]) == before[0x6800:0x6859]
    assert bytes(c.m[0xAC00:]) == before[0xAC00:]
    return dict(token=0xA3, dictionary_bytes=len(token), peek_start=end,
                peek_end=end+size, token_sha256=hashlib.sha256(token).hexdigest())


def main():
    c, _, _, _ = setup()
    # Pre-existing .36 records contain raw DIM. New firmware must still read
    # them; adding a token must not invalidate otherwise compatible records.
    legacy = [(10,'DIM A(1):A(1)=12.5'), (20,'PRINT A(1)')]
    for n, source in legacy:
        c.command(f'{n} {source}')
    before = bytes(c.m[0x20C0:c.word(emu.S['PEND'])+1])
    assert before == pack(legacy)
    layout = install(c)
    c.command('RUN')
    assert c.screen() == '12.5'
    assert bytes(c.m[0x20C0:c.word(emu.S['PEND'])+1]) == before
    c.command('NEW')
    lines = [(10,'DIM A(2,3)'), (20,'A(2,3)=0.125'),
             (30,'PRINT A(2,3)'), (40,'REM DIM in comments'),
             (50,'PRINT "DIM in strings"')]
    for n, source in lines:
        c.command(f'{n} {source}')
    arena = bytes(c.m[0x20C0:c.word(emu.S['PEND'])+1])
    # First record alone changes: DIM becomes A3, record length shrinks by 2.
    expected = bytes((11,0,10,0xA3))+b' A(2,3)'+pack(lines[1:])
    assert arena == expected, (arena, expected)
    assert c.word(0x19FE) == binascii.crc_hqx(arena,0xFFFF)
    c.command('LIST 10')
    assert c.screen().startswith('10 DIM A(2,3)'), c.screen()
    c.command('')  # Finish LIST.
    c.command('RUN')
    assert c.screen() == 'DIM in strings'
    c.command('PRINT A(2,3)')
    assert c.screen() == '0.125'
    # Exercise relocated PEEK and every existing numerical function.
    c.command('PRINT PEEK(8387)+ABS(-1)+INT(2.9)+SGN(-2)')
    assert c.screen() == '165', c.screen()  # 8387=$20C3 contains DIM=$A3.
    c.command('10 DIM A(3,4)')
    c.command('RUN')
    assert c.screen() == 'DIM in strings'
    report = dict(result='PASS', layout=layout, checks=[
        'old raw DIM program remains executable without rewriting',
        'DIM encoded as A3, all old token IDs unchanged',
        'quoted/comment DIM preserved literally', 'retained program CRC',
        'LIST expansion', 'array RUN', 'relocated PEEK', 'edit and rerun'],
        limitation=__doc__)
    (OUT/'tokens-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
