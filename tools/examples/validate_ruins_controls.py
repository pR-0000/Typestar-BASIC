"""Check Ruins' four LCD directions on the selected BASIC firmware."""
from pathlib import Path
import argparse, hashlib, json, os, sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'studio/internal'))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from core import analyze
from emulator_worker import backend


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mask-rom', required=True, type=Path)
    p.add_argument('--firmware-rom', required=True, type=Path)
    args = p.parse_args()
    C = backend(mask_path=args.mask_rom, firmware_path=args.firmware_rom)
    from PySide6.QtWidgets import QApplication
    from lcd_glass import render_glass
    app = QApplication.instance() or QApplication([])
    native = {int(k,16):v for k,v in json.loads((ROOT/'studio/internal/assets/lcd-font.json').read_text())['rows'].items()}

    def wait(c):
        s = c.symbols
        for _ in range(5000000):
            if c.pc == 0x8ef0 and c.word(s['RLINE']) == 910:
                return
            assert c.pc not in (s['SYNTAX'],s['RANGEERROR'],s['PMEMERROR']), (hex(c.pc),c.screen())
            c.step()
        raise AssertionError(('timeout',hex(c.pc),c.screen()))

    def key(c, value):
        c.held_key = value
        assert c.pc == 0x8ef0
        c.step()
        c.held_key = 0
        wait(c)

    report = {'result':'PASS','firmware_sha256':hashlib.sha256(args.firmware_rom.read_bytes()).hexdigest(),
              'scope':'actual game movement and LCD selector; fixed empty map replaces random map preparation', 'cases':[]}
    for lang, name in (('fr','ruines-typestar'),('en','typestar-ruins')):
        path = ROOT/f'examples/games/{name}-{lang}.bas'
        source = path.read_text(encoding='utf-8')
        rows = dict(analyze(source).records)
        # Keep DIM, arrow display, movement, visit marks and the printer driver.
        # A visited clear map avoids random encounters during direction checks.
        rows[80] = 'FOR I=0 TO 79:M(I)=16:NEXT I'
        rows[82] = 'P=44:H=9:R=0:N=0:D=0:B=0:C=0:GOTO 300'
        c = C(''.join(f'{n} {b}\n' for n,b in sorted(rows.items())))
        c.instant_paper = True
        wait(c)
        assert c.snapshot(False)['cells'][12:19:2] == [169,170,201,200]
        for direction, destination in enumerate(('E4','E6','D5','F5')):
            if direction:
                key(c,19)
            state = c.snapshot(False)
            slot = state['lower'][12+2*direction]
            assert slot < 8 and state['cgram'][slot*8] == 31
            # Read P from the actual variable table and restore the start cell.
            heap = c.word(c.symbols['DHEAP'])
            pos = next(i for i in range(heap,0x3800,6) if c.m[i]==ord('P'))
            c.m[pos+1:pos+6] = bytes.fromhex('0000004400')
            key(c,13)
            assert c.screen().startswith(destination+' '), (lang,direction,c.screen())
            report['cases'].append({'language':lang,'direction':direction,'screen':c.screen()})
        key(c,19)  # Wrap from right to up, then back with the left key.
        state = c.snapshot(False)
        assert state['cgram'][state['lower'][12]*8] == 31
        key(c,18)
        state = c.snapshot(False)
        assert state['cgram'][state['lower'][18]*8] == 31
        # Capture B2 with the actual HUD routine and a fresh fixture.
        rows[82] = 'P=11:H=9:R=0:N=0:D=0:B=0:C=0:GOTO 300'
        c = C(''.join(f'{n} {b}\n' for n,b in sorted(rows.items())))
        c.instant_paper = True
        wait(c)
        assert c.screen().startswith('B2 ')
        target = ROOT/'examples/guides/images'/f'ruines-lcd-{lang}.png'
        assert render_glass(1600,168,c.snapshot(False),native,spaced=True,blink=False).save(str(target))
        manual = ROOT/'docs/user-manual'/('en/images' if lang=='en' else 'images')/'exemple-ruines-lcd.png'
        manual.write_bytes(target.read_bytes())
        report[lang] = {'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':analyze(source).used}
    out = ROOT/'build/user-manual/ruins-controls.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True),flush=True)


if __name__ == '__main__':
    main()
