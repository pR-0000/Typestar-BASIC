"""Build Studio's original hex badges for lossless private-use source bytes.

Build-time dependency: fontTools. Studio only loads the resulting TTF with Qt.
The outlines use the project's own small hexadecimal bitmap alphabet.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'build/authoring-deps'))
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

HEX = ['111101101101111', '010110010010111', '111001111100111',
       '111001111001111', '101101111001001', '111100111001111',
       '111100111101111', '111001010010010', '111101111101111',
       '111101111001111', '010101111101101', '110101110101110',
       '111100100100111', '110101101101110', '111100110100111',
       '111100110100100']


def glyph(byte):
    pen = TTGlyphPen(None)
    def box(x, y, w, h):
        pen.moveTo((x,y)); pen.lineTo((x,y+h))
        pen.lineTo((x+w,y+h)); pen.lineTo((x+w,y)); pen.closePath()
    # Slim brackets distinguish one encoded byte from two source characters.
    for x, side in ((25, 1), (935, -1)):
        box(x,0,30,760)
        box(x if side==1 else x-60,0,90,30)
        box(x if side==1 else x-60,730,90,30)
    for digit, x0 in zip(f'{byte:02X}', (150, 550)):
        bits = HEX[int(digit,16)]
        for y in range(5):
            for x in range(3):
                if bits[3*y+x]=='1': box(x0+100*x,40+136*(4-y),100,136)
    return pen.glyph()


def main():
    names=['.notdef','space']+[f'byte{i:02X}' for i in range(128,256)]
    font=FontBuilder(1000,isTTF=True);font.setupGlyphOrder(names)
    font.setupCharacterMap({32:'space'}|{0xe000+i:f'byte{i:02X}' for i in range(128,256)})
    empty=TTGlyphPen(None).glyph()
    font.setupGlyf({'.notdef':glyph(0),'space':empty}|
                  {f'byte{i:02X}':glyph(i) for i in range(128,256)})
    font.setupHorizontalMetrics({name:(1000,0) for name in names})
    font.setupHorizontalHeader(ascent=850,descent=-150)
    font.setupNameTable(dict(familyName='Typestar Bytes',styleName='Regular',
        uniqueFontIdentifier='Typestar Bytes 1.0',fullName='Typestar Bytes',
        psName='TypestarBytes-Regular',version='Version 1.0',
        copyright='Original outlines for Typestar BASIC Studio; same licence as the project.'))
    font.setupOS2(sTypoAscender=850,sTypoDescender=-150,usWinAscent=850,usWinDescent=150)
    font.setupPost();font.setupMaxp()
    path=ROOT/'studio/internal/assets/typestar-bytes.ttf'
    font.save(path);print(path.name,path.stat().st_size)


if __name__=='__main__':main()
