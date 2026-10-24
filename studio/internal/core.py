from i18n import tr
"""Pure Studio model. The firmware's host codec remains the size authority."""
from dataclasses import dataclass
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import native_program as codec
from native_text import encode_source
import unicodedata
from serial_rates import BAUD_RATES

VERSION = '0.2.40'
KEYWORDS = set('''PRINT LPRINT INPUT LET IF THEN ELSE FOR TO STEP NEXT GOTO
GOSUB RETURN END REM DATA READ RESTORE DIM RUN LIST LLIST NEW CLEAR MEM LOAD SAVE
KEYS CLS LOCATE LLOCATE LSPACING CURSOR LCDCHAR LCDTRI LCDLINE ICON GLYPH
POINT LINE BOX CIRCLE ELLIPSE DRAW INSTANT DEFERRED CANCEL ORIGIN MOVE HEAD
FEED BEEP SOUND POKE BAUD SERCFG SEROUT RANDOMIZE AND OR NOT MOD ABS SGN
INT FIX SQR SIN COS TAN ATN LOG EXP RND FRE PEEK INKEY SERIN VAL LEN ASC
CHR$ STR$ LEFT$ RIGHT$ MID$ PI'''.split())

@dataclass
class Analysis:
    issues: list
    records: list
    used: int | None
    free: int | None

def analyze(text):
    issues, records, seen = [], [], set()
    for row, raw in enumerate(text.splitlines(), 1):
        raw = unicodedata.normalize("NFC", raw)
        if not raw.strip():
            continue
        if len(raw) > 63:
            issues.append((row, (f'{len(raw)}' + tr(' caractères : maximum 63, numéro compris.'))))
        try: encode_source(raw)
        except ValueError as exc: issues.append((row, str(exc)))
        match = re.fullmatch(r'\s*(\d+)\s+(.+)', raw)
        if not match:
            issues.append((row, tr('Numéro de ligne suivi du code attendu.')))
            continue
        number, body = int(match[1]), match[2]
        if not 1 <= number <= 65535:
            issues.append((row, tr('Numéro attendu entre 1 et 65535.')))
        if number in seen:
            issues.append((row, (tr('Numéro ') + f'{number}' + tr(' en double : une ligne serait remplacée.'))))
        seen.add(number)
        records.append((number, body))
    if issues:
        return Analysis(issues, records, None, None)
    try:
        used = len(codec.pack(records)) - 1  # exclude the permanent arena sentinel
        return Analysis([], records, used, 5951 - used)
    except ValueError as exc:
        return Analysis([(0, str(exc))], records, None, None)

def literal(n, base, width):
    if base == 'Binaire':
        return '%' + format(n, f'0{width}b')
    if base == 'Hexadécimal':
        return '&H' + format(n, 'X')
    return str(n)

def export_sprite(pixels, kind, start=10, step=10, position=1,
                  triangle=0, lower=0, array='Z', zoom=1, base='Binaire'):
    h = len(pixels)
    w = len(pixels[0]) if h else 0
    if not h or any(len(row) != w or any(v not in (0, 1) for v in row) for row in pixels):
        raise ValueError(tr('Matrice rectangulaire binaire attendue.'))
    if start < 1 or step < 1:
        raise ValueError(tr('Numéro initial et pas strictement positifs.'))
    words = [sum(int(v) << (w-1-x) for x, v in enumerate(row)) for row in pixels]
    if kind == 'LCD':
        if (w, h) != (5, 7) or not 1 <= position <= 32 or not 0 <= triangle <= 31 or not 0 <= lower <= 31:
            raise ValueError(tr('LCD : 5 × 7 pixels, position 1..32, masques 0..31.'))
        # Decimal rows keep the complete LCDCHAR instruction below 63 bytes.
        # The paper editor offers binary/hex because each row has its own line.
        bodies = [f'LCDCHAR {position},' + ','.join(map(str, words + [triangle])),
                  f'LCDLINE {position},{lower}']
    else:
        if not 1 <= w <= 31 or not 1 <= h <= 16 or zoom not in (1, 2, 3, 4):
            raise ValueError(tr('Papier : 1..31 × 1..16 pixels, mode 1, 2, 3 ou 4.'))
        if not re.fullmatch('[A-Z]', array):
            raise ValueError(tr('Nom de tableau attendu : A..Z.'))
        if w <= 16:
            bodies = [f'DIM {array}({h-1})']
            bodies += [f'{array}({y})={literal(v, base, w)}' for y, v in enumerate(words)]
            bodies.append(f'GLYPH {array}(0),{w},{h},{zoom}')
        else:
            bodies = [f'DIM {array}({h-1},{w-1})']
            # DIM zeroes the matrix; only explicitly set black pixels.
            bodies += [f'{array}({y},{x})=1' for y, row in enumerate(pixels)
                       for x, v in enumerate(row) if v]
            bodies.append(f'GLYPH {array}(0,0),{w},{h},{zoom}')
    if start + (len(bodies)-1)*step > 65535:
        raise ValueError(tr('Les numéros générés dépassent 65535.'))
    result = '\n'.join(f'{start+i*step} {body}' for i, body in enumerate(bodies)) + '\n'
    if max(map(len, result.splitlines())) > 63:
        raise ValueError(tr('Une ligne générée dépasse 63 caractères.'))
    return result

def save_asset(path, pixels, kind, triangle=0, lower=0):
    data = dict(format='typestar-sprite-1', kind=kind, pixels=pixels,
                triangle=triangle, lower=lower)
    # Validate before saving, including limits of each target.
    export_sprite(pixels, kind, triangle=triangle, lower=lower)
    Path(path).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

def load_asset(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('format') != 'typestar-sprite-1' or data.get('kind') not in ('LCD', 'Papier'):
        raise ValueError(tr('Format de sprite inconnu.'))
    export_sprite(data['pixels'], data['kind'], triangle=data.get('triangle', 0), lower=data.get('lower', 0))
    return data
