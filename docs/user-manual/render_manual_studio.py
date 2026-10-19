"""Capture Studio widgets and selected games for the French manual.

Run with Studio's Python and explicit, locally owned ROM files. The BASIC
sources are executed unchanged; paper images come from the actual head events.
Qt settings are isolated. No serial device is opened and no ROM is copied.
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

from PySide6.QtCore import QSettings, QRect
from PySide6.QtGui import QFont, QFontDatabase, QTextCursor
from PySide6.QtWidgets import QApplication
from PIL import Image, ImageChops, ImageDraw, ImageFont
from emulator_worker import backend
from lcd_glass import render_glass
from paper import PaperRaster
from debugger import inspect_cpu
from i18n import set_language


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mask-rom', required=True, type=Path)
    parser.add_argument('--firmware-rom', required=True, type=Path)
    parser.add_argument('--ui-only', action='store_true', help='Reuse the verified game snapshots from the previous run')
    parser.add_argument('--ui-demo', action='store_true', help='Capture the interface with Pocket Duel only')
    parser.add_argument('--language',choices=['fr','en'],default='fr')
    args = parser.parse_args()
    english=args.language=='en'
    filemap = {
        'piano-fr.bas': 'piano-en.bas' if english else 'piano-fr.bas',
        'pocket-duel-fr.bas': 'games/pocket-duel-en.bas' if english else 'games/pocket-duel-fr.bas',
        'duel-orbital-fr.bas': 'games/orbital-duel-en.bas' if english else 'games/duel-orbital-fr.bas',
        'duel-balistique-fr.bas': 'games/ballistic-duel-en.bas' if english else 'games/duel-balistique-fr.bas',
    }
    set_language(args.language)
    app = QApplication.instance() or QApplication([])
    font_id = QFontDatabase.addApplicationFont(str(HERE/'fonts/Lato-Regular.ttf'))
    app.setFont(QFont(QFontDatabase.applicationFontFamilies(font_id)[0], 11))
    CPU = backend(mask_path=args.mask_rom.resolve(), firmware_path=args.firmware_rom.resolve())
    native = {int(k,16):v for k,v in json.loads((ROOT/'studio/internal/assets/lcd-font.json').read_text(encoding='utf-8'))['rows'].items()}
    images = HERE/('en/images' if english else 'images')
    images.mkdir(parents=True,exist_ok=True)
    report = dict(generator='Studio widgets, HD6301 backend, LCD glass and PaperRaster',
                  mask_sha256=hashlib.sha256(args.mask_rom.read_bytes()).hexdigest(),
                  firmware_sha256=hashlib.sha256(args.firmware_rom.read_bytes()).hexdigest(),
                  scenes=[], captures=[])
    cpus = {}

    def execute(filename, tick_action, done):
        source = (ROOT/'examples'/filemap.get(filename,filename)).read_text(encoding='utf-8-sig')
        cpu = CPU(source)
        for tick in range(120000000):
            line = cpu.word(cpu.symbols['RLINE'])
            if cpu.pc in (cpu.symbols['SYNTAX'], cpu.symbols['RANGEERROR']):
                raise AssertionError((filename, line, hex(cpu.pc), cpu.screen()))
            tick_action(cpu, line)
            if done(cpu, line):
                break
            cpu.step()
            if tick and tick % 2000000 == 0:
                print(filename, tick, line, cpu.screen(), flush=True)
        else:
            raise RuntimeError(('scene timeout', filename, line, cpu.screen()))
        state = cpu.snapshot(True)
        stem = {'piano-fr.bas':'piano','pocket-duel-fr.bas':'pocket-duel',
                'duel-orbital-fr.bas':'duel-orbital','duel-balistique-fr.bas':'duel-balistique'}[filename]
        assert render_glass(1920,208,state,native,spaced=True,blink=False).save(str(images/f'exemple-{stem}-lcd.png'))
        paper = PaperRaster()
        paper.add(cpu.paper_events)
        assert not paper.clipped, (filename, paper.clipped)
        bounds = None
        if paper.columns:
            image = paper.output().convert('L')
            bounds = ImageChops.invert(image).getbbox()
            assert bounds
            box = (max(0,bounds[0]-24), max(0,bounds[1]-24), min(image.width,bounds[2]+24), min(image.height,bounds[3]+24))
            image.crop(box).save(images/f'exemple-{stem}-papier.png')
        report['scenes'].append(dict(file=filename,source_file=filemap.get(filename,filename),source_sha256=hashlib.sha256((ROOT/'examples'/filemap.get(filename,filename)).read_bytes()).hexdigest(),
                                    steps=tick,line=line,state=state,head_columns=paper.columns,ink_bounds=bounds))
        print('Captured', filename, 'line', line, 'columns', paper.columns, flush=True)
        cpus[stem] = cpu
        return cpu

    def games():
        execute('piano-fr.bas', lambda c,l:None, lambda c,l:l==80 and c.pc==0x8ee6)
        def pocket_keys(c,line):
            if line==200:c.held_key=13
            elif line>=250:c.held_key=0
        pocket = execute('pocket-duel-fr.bas', pocket_keys, lambda c,l:l==300 and c.pc==0x8ee6)

        orbital_inputs = ['A1\r','H\r','A3\r','H\r','A5\r','H\r','B2\r']
        def orbital_keys(c,line):
            c.held_key = 13 if line==40 else 0
            if c.pc==c.symbols['GETC'] and not c.input and orbital_inputs:
                if line in (810,830,230):
                    value=orbital_inputs.pop(0)
                    c.input.extend(value.encode('ascii'))
                    print('Orbital input',line,repr(value),flush=True)
        execute('duel-orbital-fr.bas', orbital_keys,
                lambda c,l:not orbital_inputs and l==230 and c.pc==c.symbols['GETC'] and not c.input)

        ballistic_inputs = ['42\r','2\r','45\r','80\r']
        def ballistic_keys(c,line):
            if c.pc==c.symbols['GETC'] and not c.input and ballistic_inputs and line in (20,40,162,190):
                value=ballistic_inputs.pop(0)
                c.input.extend(value.encode('ascii'))
                print('Ballistic input',line,repr(value),flush=True)
        execute('duel-balistique-fr.bas',ballistic_keys,
                lambda c,l:not ballistic_inputs and l==165 and c.pc==c.symbols['GETC'] and not c.input)

        return pocket

    if args.ui_only:
        cached=ROOT/'build/user-manual'/('studio-illustrations-en.json' if english else 'studio-illustrations.json')
        if not cached.exists():cached=cached.with_name('studio-ui-preview.json')
        previous=json.loads(cached.read_text(encoding='utf-8'))
        for key in ('mask_sha256','firmware_sha256'):
            assert previous[key]==report[key], 'Cached snapshots use different ROM files'
        report=previous
        report['captures']=[]
        for scene in report['scenes']:
            assert scene['source_sha256']==hashlib.sha256((ROOT/'examples'/scene.get('source_file',scene['file'])).read_bytes()).hexdigest()
        pocket_state=next(s['state'] for s in report['scenes'] if s['file']=='pocket-duel-fr.bas')
        dbg=report['debug_snapshot']
    elif args.ui_demo:
        def demo_keys(c,line):
            if line==200:c.held_key=13
            elif line>=250:c.held_key=0
        pocket=execute('pocket-duel-fr.bas',demo_keys,lambda c,l:l==300 and c.pc==0x8ee6)
        pocket_state=pocket.snapshot(True)
        dbg=inspect_cpu(pocket,pocket.symbols,pocket.symbols['PROGRAM'])
    else:
        pocket=games()
        pocket_state=pocket.snapshot(True)
        dbg=inspect_cpu(pocket,pocket.symbols,pocket.symbols['PROGRAM'])

    from app import Studio
    with tempfile.TemporaryDirectory(prefix='typestar-manual-studio-') as temporary:
        settings_path = Path(temporary)/'capture.ini'
        settings=QSettings(str(settings_path),QSettings.Format.IniFormat)
        for key,value in [('appearance/language',args.language),('appearance/theme','light'),('emulator/sound','false')]:
            settings.setValue(key,value)
        settings.sync()
        window=Studio(settings_path=str(settings_path))
        window.resize(1560,940)
        window.show()
        window.path=ROOT/'examples'/filemap.get('pocket-duel-fr.bas','pocket-duel-fr.bas')
        window.editor.setPlainText(window.path.read_text(encoding='utf-8'))
        window.editor.document().setModified(False)
        window.editor.setTextCursor(QTextCursor(window.editor.document()))
        window.check();window.update_title()
        # No selected device, no pending transfer, no user settings read.
        window.port.clear()
        emu=window.emulator
        emu.set_rom_paths(str(args.mask_rom),str(args.firmware_rom))
        emu.power.blockSignals(True);emu.power.setChecked(True);emu.power.blockSignals(False)
        emu.lcd.state=pocket_state
        emu.lcd.blink_timer.stop();emu.lcd.blink=False
        emu.debug_timer.stop()
        emu.status.setText(('Paused - PC $' if english else 'En pause - PC $')+pocket_state['pc'])
        # These labels describe the genuine snapshot; its ROMs are explicit.
        emu.log.setPlainText('Program: pocket-duel.bas\nFirmware executed, then paused in the keyboard loop.' if english else 'Programme : pocket-duel-fr.bas\nExécution du firmware, puis pause sur la boucle clavier.')
        emu.debug_registers.setText(dbg['registers'])
        if not english:dbg['flags']=dbg['flags'].replace('H: not modeled','H : non modélisé')
        emu.debug_flags.setText(dbg['flags'])
        emu.debug_address.setText(dbg['memory'][:4])
        emu.debug_memory.setPlainText(dbg['memory'])
        emu.debug_code.setPlainText(dbg['assembly'])
        report['debug_snapshot']=dbg

        def capture(widget, name, rect=None):
            app.processEvents()
            pixmap=widget.grab(rect) if rect is not None else widget.grab()
            assert pixmap.save(str(images/name),'PNG')
            report['captures'].append(dict(image=name,width=pixmap.width(),height=pixmap.height()))
            print(name,flush=True)
        capture(window,'studio-vue-ensemble.png')
        capture(window.editor,'studio-editeur.png',QRect(0,0,window.editor.width(),min(410,window.editor.height())))
        capture(emu,'studio-emulateur.png',QRect(0,0,emu.width(),emu.entry.geometry().bottom()+5))
        # Zoom the genuine debugger widget, retaining all twenty code lines.
        # It is restored to the application after the detail captures.
        emu.details.setParent(None)
        emu.details.resize(1100,680)
        emu.details.show()
        emu.details.setCurrentIndex(1)
        debug_layout=emu.details.widget(1).layout()
        debug_layout.setStretch(debug_layout.count()-1,1)
        capture(emu.details,'studio-debogueur.png')
        capture(emu.debug_memory,'studio-memoire.png')
        capture(emu.debug_code,'studio-code-machine.png')
        emu.details.hide()
        emu.layout().addWidget(emu.details,1)
        window.tabs.setCurrentWidget(window.glyph_tab)
        rows=[14,10,4,27,4,10,27]
        window.grid.set_pixels([[(row>>(4-x))&1 for x in range(5)] for row in rows])
        window.first.setValue(1000)
        capture(window.glyph_tab,'studio-glyphes.png')
        palette=window.tabs.widget(2)
        window.tabs.setCurrentWidget(palette)
        palette.list.setCurrentRow(172)
        palette.list.scrollToItem(palette.list.item(171),palette.list.ScrollHint.PositionAtTop)
        capture(palette,'studio-caracteres.png',QRect(0,0,palette.width(),min(450,palette.height())))
        window.tabs.setCurrentWidget(window.tabs.widget(3))
        window.image_path=HERE/'images/printy-salut-v2.png'
        window.image_name.setText(window.image_path.name)
        window.update_image()
        capture(window.tabs.widget(3),'studio-impression-graphique.png')
        window.editor.document().setModified(False);window.asset_dirty=False
        window.close()
    destination=ROOT/'build/user-manual'/('studio-ui-preview.json' if args.ui_demo else ('studio-illustrations-en.json' if english else 'studio-illustrations.json'))
    destination.parent.mkdir(parents=True,exist_ok=True)
    report['scenario_inputs']={'piano':[], 'pocket-duel':['Return at initial wait'],
                              'duel-orbital':['Return','A1','H','A3','H','A5','H','B2'],
                              'duel-balistique':['42','2','45','80']}
    # A separately labelled explanatory drawing, not a retouched screenshot.
    # It shows the program's exact DATA motifs while a difference between
    # staged glyph data and captured output is investigated separately.
    source=(ROOT/'examples/games/duel-orbital-fr.bas').read_text(encoding='utf-8')
    rows=[]
    for line in source.splitlines():
        if 1700<=int(line.split()[0])<=1752:
            rows.extend(int(v.strip()[2:],16) for v in line.split('DATA ')[1].split(','))
    assert len(rows)==48
    drawing=Image.new('RGB',(940,540),'white');pen=ImageDraw.Draw(drawing)
    font=ImageFont.truetype(str(HERE/'fonts/Lato-Regular.ttf'),25)
    title=ImageFont.truetype(str(HERE/'fonts/Lato-Bold.ttf'),31)
    pen.text((470,17),('TYPESTAR - ORBITAL DUEL' if english else 'TYPESTAR - DUEL ORBITAL'),font=title,fill='black',anchor='mt')
    for side,name in enumerate(('YOUR FLEET','YOUR SHOTS') if english else ('VOTRE FLOTTE','VOS TIRS')):
        x=60+450*side;y=150
        pen.text((x+180,78),name,font=font,fill='black',anchor='mt')
        for i in range(7):
            pen.line((x+60*i,y,x+60*i,y+360),fill='black',width=2)
            pen.line((x,y+60*i,x+360,y+60*i),fill='black',width=2)
        for i in range(6):
            pen.text((x+60*i+30,y-34),chr(65+i),font=font,fill='black',anchor='mt')
            pen.text((x-22,y+60*i+30),str(i+1),font=font,fill='black',anchor='mm')
    def motif(side,col,row,offset):
        x=60+450*side+60*col+14;y=150+60*row+14
        for iy,word in enumerate(rows[offset:offset+16]):
            for ix in range(16):
                if word&(1<<(15-ix)):
                    pen.rectangle((x+ix*2,y+iy*2,x+ix*2+1,y+iy*2+1),fill='black')
    for col,row in [(0,0),(1,0),(2,0),(0,2),(1,2),(0,4),(1,4)]:motif(0,col,row,0)
    motif(0,1,3,16);motif(1,1,1,32)
    drawing.save(images/'exemple-duel-orbital-schema.png')
    report['orbital_drawing']=dict(image='exemple-duel-orbital-schema.png',
        kind='explanatory drawing from the exact DATA motifs, not an emulator screenshot',
        layout='A1-A3-A5 horizontal fleet, B2 hit, B4 miss')
    report['result']='PASS' if len(report['scenes'])==4 else 'UI_PREVIEW'
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS:',destination,flush=True)


if __name__=='__main__':
    main()
