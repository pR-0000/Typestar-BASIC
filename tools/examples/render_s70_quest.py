"""Guide images from the portable tile assets and actual emulated combat."""
from pathlib import Path
import json,os,sys
os.environ['QT_QPA_PLATFORM']='offscreen'
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools/diagnostics')]
from PIL import Image,ImageDraw,ImageFont
from PySide6.QtWidgets import QApplication
from lcd_glass import render_glass
from validate_quest_rules import Game,LINES

def main():
    a=json.loads(Path(__file__).with_name('s70-quest-assets.json').read_text())
    tiles=[bytearray.fromhex(v) for v in a['tiles']]
    for t in (0,1):
        tiles[t][0]|=0x55
        for y in (2,4,6):tiles[t][y]|=1
    im=Image.new('RGB',(1052,592),'white');d=ImageDraw.Draw(im)
    try:font=ImageFont.truetype('DejaVuSansMono.ttf',16)
    except OSError:font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16)
    for x in range(30):d.text((65+32*x,10),str(x+1).rjust(2),font=font,fill='black')
    for y,row in enumerate(a['map']):
        d.text((16,51+32*y),str(y+1).rjust(2),font=font,fill='black')
        for x,tile in enumerate(row):
            for v,byte in enumerate(tiles[ord(tile)-65]):
                for u in range(8):
                    if byte&(128>>u):
                        p,q=64+32*x+4*u,48+32*y+4*v
                        d.rectangle((p,q,p+3,q+3),fill='black')
    d.text((64,565),'CANON S-70 QUEST 0.9',font=font,fill='black')
    dest=ROOT/'examples/guides/images';im.save(dest/'s70-quest-carte.png')
    app=QApplication.instance() or QApplication([])
    native={int(k,16):v for k,v in json.loads((ROOT/'studio/internal/assets/lcd-font.json').read_text())['rows'].items()}
    for lang in ('fr','en'):
        g=Game('N=30000:GOTO '+str(LINES[200]),lang);g.key()
        out=render_glass(1600,168,g.c.snapshot(False),native,spaced=True,blink=False)
        assert out.save(str(dest/f's70-quest-exploration-{lang}.png'),'PNG')
        g.key(8)
        assert g.screen().startswith('1/3 ') and 'POT0' in g.screen(),g.screen()
        out=render_glass(1600,168,g.c.snapshot(False),native,spaced=True,blink=False)
        assert out.save(str(dest/f's70-quest-inventory-{lang}.png'),'PNG')
        g=Game('T=4:Z=1:GOSUB '+str(LINES[2000])+':GOTO '+str(LINES[200]),lang)
        g.key();g.key();assert g.menu(),g.screen()
        state=g.c.snapshot(False)
        out=render_glass(1600,168,state,native,spaced=True,blink=False)
        assert out.save(str(dest/f's70-quest-combat-{lang}.png'),'PNG')
        print(lang,g.screen(),flush=True)
        g.c.held_key=13
        for _ in range(100):
            if g.c.pc==0x8ef0:g.c.step();break
            g.c.step()
        else:raise AssertionError('key injection')
        g.c.held_key=0
        for _ in range(2000000):
            if g.c.word(g.c.symbols['RLINE'])==LINES[3330] and g.c.pc==g.c.symbols['BASICSOUND']:break
            g.c.step()
        else:raise AssertionError('damage display')
        out=render_glass(1600,168,g.c.snapshot(False),native,spaced=True,blink=False)
        assert out.save(str(dest/f's70-quest-combat-damage-{lang}.png'),'PNG')
        g=Game('T=0:Z=0:GOSUB '+str(LINES[2000])+':GOTO '+str(LINES[200]),lang)
        g.key();g.key()
        for _ in range(10):
            if g.screen().startswith(('Victoire!','Victory!')):break
            assert g.menu(),g.screen()
            g.key()
        else:raise AssertionError('victory display')
        out=render_glass(1600,168,g.c.snapshot(False),native,spaced=True,blink=False)
        assert out.save(str(dest/f's70-quest-rewards-{lang}.png'),'PNG')

if __name__=='__main__':main()
