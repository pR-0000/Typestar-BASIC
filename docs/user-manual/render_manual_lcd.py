"""Authoring helper: execute manual snippets and export Studio LCD renders.

Requires Studio's environment and explicit local ROM paths. No serial port,
ROM copying or changes to the user's Studio settings.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(ROOT/'studio/internal'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, QRect
from PySide6.QtGui import QFont, QFontDatabase
from emulator_worker import backend
from lcd_glass import render_glass

SCENES = [
    ('lcd-calcul.png', '10 PRINT 2+3\n20 END\n', '5'),
    ('lcd-score.png', '10 CLS\n20 PRINT "SCORE: ";\n30 LOCATE 1,8:PRINT 25;\n40 END\n', 'SCORE: 25'),
    ('lcd-personnage.png', '10 CLS:CURSOR 4\n20 LCDCHAR 1,14,17,21,17,21,17,14,0\n30 END\n', None),
    ('lcd-triangle.png', '10 CLS:CURSOR 4\n20 LCDCHAR 1,14,17,21,17,21,17,14,0\n30 LCDTRI 1,%10101\n40 END\n', None),
    ('lcd-ligne.png', '10 CLS\n20 PRINT "BONJOUR";\n30 LCDLINE 1,%11111\n40 LCDLINE 2,%10101\n50 END\n', 'BONJOUR'),
    ('lcd-accents.png', '10 PRINT "Flèches, café, Noël"\n20 END\n', None),
    ('lcd-decimaux.png', '10 PRINT 1.5+2.25\n20 END\n', '3.75'),
    ('lcd-menu.png', '10 CLS:CURSOR 4\n20 PRINT " JOUER    QUITTER";\n30 LOCATE 1,1:PRINT ">";\n40 END\n', '>JOUER    QUITTER'),
    ('lcd-symboles-natifs.png', '10 CLS:CURSOR 4\n20 PRINT "GRILLE ";CHR$(172);"  MINE ";CHR$(192)\n30 END\n', None),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mask-rom', required=True, type=Path)
    parser.add_argument('--firmware-rom', required=True, type=Path)
    parser.add_argument('--ui-font', type=Path, help='Optional readable font for headless Qt controls')
    parser.add_argument('--language',choices=['fr','en'],default='fr')
    args = parser.parse_args()
    english=args.language=='en'
    images=HERE/('en/images' if english else 'images')
    images.mkdir(parents=True,exist_ok=True)
    from i18n import set_language
    set_language(args.language)
    app = QApplication.instance() or QApplication([])
    if args.ui_font:
        font_id=QFontDatabase.addApplicationFont(str(args.ui_font.resolve()))
        families=QFontDatabase.applicationFontFamilies(font_id)
        if not families:
            raise ValueError('Could not load the requested UI font')
        app.setFont(QFont(families[0],11))
    CPU = backend(mask_path=args.mask_rom.resolve(), firmware_path=args.firmware_rom.resolve())
    font_data = json.loads((ROOT/'studio/internal/assets/lcd-font.json').read_text(encoding='utf-8'))
    native = {int(key,16):value for key,value in font_data['rows'].items()}
    records = []
    for filename, source, expected in SCENES:
        if english:
            for old,new in [('BONJOUR','HELLO'),(' JOUER    QUITTER',' PLAY     QUIT'),('>JOUER    QUITTER','>PLAY     QUIT'),('GRILLE','GRID'),('Flèches, café, Noël','Accents: café, Noël')]:
                source=source.replace(old,new)
                if expected is not None:expected=expected.replace(old,new)
        cpu = CPU(source)
        for _ in range(1500000):
            if not cpu.input and cpu.pc == cpu.symbols['GETC']:
                break
            cpu.step()
        else:
            raise RuntimeError(f'No keyboard wait: {filename}, PC={cpu.pc:04X}')
        state = cpu.snapshot(False)
        assert cpu.lcd[0] != ord('?'), (filename,cpu.screen())
        if expected is not None:
            assert cpu.screen() == expected, (filename,cpu.screen())
        if filename.startswith('lcd-personnage') or filename.startswith('lcd-triangle'):
            slot=state['cells'][0]
            assert slot<8
            assert state['cgram'][slot*8:slot*8+7] == [14,17,21,17,21,17,14]
            assert state['cgram'][slot*8+7] == (21 if filename=='lcd-triangle.png' else 0)
        if filename=='lcd-ligne.png':
            assert state['cgram'][state['lower'][0]*8]==31
            assert state['cgram'][state['lower'][1]*8]==21
        image = render_glass(1600,168,state,native,spaced=True,blink=False)
        target = images/filename
        assert image.save(str(target), 'PNG')
        records.append(dict(image=filename,source=source,state=state))
        print(filename,flush=True)
    report = dict(generator='Studio HD6301 backend + lcd_glass.render_glass',
                  profile='S-70 / Typestar BASIC 0.4.87-dev',
                  mask_sha256=hashlib.sha256(args.mask_rom.read_bytes()).hexdigest(),
                  firmware_sha256=hashlib.sha256(args.firmware_rom.read_bytes()).hexdigest(),
                  scenes=records)
    # Native Studio controls, rendered offscreen with isolated settings.
    # No transfer is started and no existing user configuration is read.
    from app import Studio
    with tempfile.TemporaryDirectory(prefix='typestar-manual-ui-') as temporary:
        settings_path=Path(temporary)/'manual.ini'
        settings=QSettings(str(settings_path),QSettings.Format.IniFormat)
        settings.setValue('appearance/language',args.language)
        settings.setValue('appearance/theme','light')
        settings.sync()
        window=Studio(settings_path=str(settings_path))
        window.resize(1500,920)
        window.show()
        app.processEvents()
        parent=window.send_button.parentWidget()
        left=window.send_button.geometry()
        right=window.receive_button.geometry()
        area=QRect(left.left()-4,left.top()-4,right.right()-left.left()+9,max(left.height(),right.height())+8)
        assert parent.grab(area).save(str(images/'studio-transferts.png'),'PNG')
        window.close()
        app.processEvents()
    report['studio_controls']='studio-transferts.png; actual French Studio buttons, isolated offscreen rendering'
    out=ROOT/'build/user-manual'
    out.mkdir(parents=True,exist_ok=True)
    (out/('lcd-illustrations-en.json' if english else 'lcd-illustrations.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
