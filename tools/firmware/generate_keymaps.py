"""Generate ASCII keymaps from traced Canon outputs, with explicit BASIC keys."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parents[1] / 'ROMReader/analysis/hd6301_typestar/keyboard/translation_table.csv'


def main():
    rows = list(csv.DictReader(SOURCE.open()))
    assembly = ('; Canon ASCII subset, punctuation mode 0; raw 25 reserved for BASIC =/+.\n'
                '; Non-ASCII/two-byte outputs become no event (0). See keymaps.json.\n'
                'KEYTABLES FDB '+','.join(f'KEYMAP{i}' for i in range(10))+'\n')
    maps = []
    for locale in range(10):
        values = []
        for modifier in range(2):
            for key in range(44):
                row = next(r for r in rows if int(r['locale_index']) == locale and
                           int(r['mode_1805']) == 0 and int(r['modifier']) == modifier and
                           int(r['matrix_code'], 16) == key)
                a, b = int(row['primary_FB'], 16), int(row['secondary_FC'], 16)
                value = a if 32 <= a <= 126 and b == 0 else 0
                # Explicit custom mapping, not a claim about the printed legend.
                if key == 0x25:
                    value = ord('+' if modifier else '=')
                values.append(value)
        maps.append(values)
        assembly += f'KEYMAP{locale}\n'
        for i in range(0, 88, 11):
            assembly += '        FCB '+','.join(f'${v:02X}' for v in values[i:i+11])+'\n'
    (ROOT / 'src/keymaps.inc').write_text(assembly, encoding='ascii')
    (ROOT / '_local/development/docs/keymaps.json').write_text(json.dumps({
        'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'index': 'layout 0..9; each array = 44 unshifted then 44 shifted raw matrix codes',
        'override': 'raw 0x25 -> = ; shifted -> + ; physical key legend unverified',
        'maps': maps}, indent=2)+'\n')

    # Canon-start profile: retain both original I/II sets, without the
    # provisional raw-25 override. Layout, mode, shift, then raw position.
    assembly = '; Original Canon ASCII mappings: I/II, no punctuation override.\n'
    assembly += 'KEYTABLES FDB '+','.join(f'KEYMAP{i}' for i in range(10))+'\n'
    for locale in range(10):
        assembly += f'KEYMAP{locale}\n'
        for mode in range(2):
            for modifier in range(2):
                values = []
                for key in range(44):
                    row = next(r for r in rows if int(r['locale_index']) == locale and
                               int(r['mode_1805']) == mode and int(r['modifier']) == modifier and
                               int(r['matrix_code'],16) == key)
                    a,b = int(row['primary_FB'],16),int(row['secondary_FC'],16)
                    values.append(a if 32 <= a <= 126 and b == 0 else 0)
                for i in range(0,44,11):
                    assembly += '        FCB '+','.join(f'${v:02X}' for v in values[i:i+11])+'\n'
    (ROOT/'src/keymaps-canon.inc').write_text(assembly,encoding='ascii')


if __name__ == '__main__':
    main()
