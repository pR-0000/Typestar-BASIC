"""Generate Vol radar 0.5: seeded paper terrain and deliberate LCD flight steps.

Inspired by Charles Caron's PC-1500 simulator, Hebdogiciel 37 (1984).
The S-70 generates its 24x20 terrain from a map number. Printing and flight
checks call the same row routine; DATA contains five reusable mountain
profiles and the compact 8x8 tile palette.
No PC helper, extra firmware command or external asset is needed at runtime.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'studio/internal'))
from core import analyze, codec
from native_text import LCD_TO_UNICODE, encode_source
from update_paper_games import compact

ASSET_PATH = Path(__file__).with_name('flight-simulator-assets.json')
MAP_X = 96
MAP_Y = 224
VIEW_Y = 1792
INITIAL_FUEL = 99
BORDER_FUEL = 2
MOTION_ICONS = chr(0xe000+170)+'='+chr(0xe000+169)
DX = '12221000'
DY = '00122210'
MOUNTAIN_ROWS = ('FGHIJHGF','FGHHHHGF','FFGGGGFF','AFFGGFFA','AAFFFFAA')
# INKEY translates arrows and margins but ignores several Canon function keys.
# KHELD is the BASIC 0.4.100 debounced matrix byte, FF when released. Poll INKEY
# first to drive the actual scanner, then fall back only for ignored keys.
# A translated event may become pending between INKEY and PEEK: let the next
# INKEY consume it rather than treating a raw margin/arrow as its ASCII code.
# REPEAT (2E) and RELOC (33) both call radar.
KHELD = 0x1999
assert list(zip((int(c)-1 for c in DX),(int(c)-1 for c in DY))) == [
    (0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]

# X/Y: aircraft quarter-cell coordinates; D: eight compass headings, north=0.
# H: altitude; V: speed; P: climb/level/descent; F: fuel; N: elapsed steps.
# T: remaining storm steps; W: calm countdown; R: radar cooldown; Z: outcome.
# B/C retain physical paper Y/X. G/K are the next paper X/Y targets.
# S is the map number. M: requested altitude (0=radar), J: remaining steps,
# O: completed tower requests. These reuse the former map/printing scalars.
# G(64), no longer a row ID after printing, tracks the high-wind band.
# A/E/I/J/L/Q/U are temporary scalars. A$ is UI/pattern text, M$ a map row.
BODY = {
1:'GOTO 8000',
50:'A=G-C:IF A=0 THEN 54',
51:'IF ABS(A)>128 THEN A=SGN(A)*128',
52:'IF A<0 THEN ORIGIN 128,0 ELSE ORIGIN',
53:'HEAD A:C=C+A:GOTO 50',
54:'A=K-B:IF A=0 THEN 58',
55:'IF ABS(A)>448 THEN A=SGN(A)*448',
56:'IF A<0 THEN ORIGIN 0,448 ELSE ORIGIN',
57:'FEED A:B=B+A:GOTO 54',
58:'ORIGIN:RETURN',
100:f'IF INKEY(0)<>0 OR PEEK({KHELD})<>255 THEN 100',
110:'E=INKEY(0):IF E<>0 THEN 120',
115:f'E=PEEK({KHELD}):IF E=46 OR E=60 THEN 120',
116:'IF E<51 OR E>53 THEN 110',
120:'RETURN',
200:'GOSUB 1000:GOSUB 100',
210:'IF E=18 OR E=19 THEN D=(D+2*E-29)MOD 8',
230:'IF E=52 OR E=53 THEN P=105-2*E',
235:'IF E=60 THEN P=0',
240:'IF E=21 AND V<160 THEN V=V+20',
250:'IF E=20 AND V>0 THEN V=V-20',
260:'IF E=46 OR E=51 THEN GOSUB 5000:GOTO 200',
270:'IF E=32 THEN GOSUB 7000:GOTO 200',
280:'IF E=8 THEN GOSUB 4000:GOTO 200',
290:'IF E<>13 THEN 200',
300:'N=N+1:F=F-1-INT(V/120)',
310:'IF P=1 THEN F=F-1',
320:'IF R>0 THEN R=R-1',
330:'E=T:IF T>0 THEN T=T-1',
340:'IF E=0 AND W>0 THEN W=W-1',
350:'H=H+50*P:IF H<0 THEN H=0',
360:'IF H>500 THEN H=500',
370:'IF H>0 AND V<80 THEN H=H-150:IF H<=0 THEN Z=5',
380:'IF Z=5 THEN H=0:GOTO 9000',
385:'IF E=0 AND W=0 AND H>0 THEN GOSUB 1800',
390:'U=INT(V/40)',
400:'IF D MOD 2=1 THEN U=INT((U+1)*.7)',
410:f'X=X+U*(ASC(MID$("{DX}",D+1,1))-49)',
420:f'Y=Y+U*(ASC(MID$("{DY}",D+1,1))-49)',
430:'IF T>0 AND H>0 THEN X=X+1',
440:'GOSUB 1200:IF Z>0 THEN 9000',
442:'U=G(64):G(64)=0',
443:'IF Q>=10 THEN 445',
444:'G(64)=-(X<16 OR X>79 OR Y<16 OR Y>63)',
445:f'F=F-{BORDER_FUEL}*G(64)',
450:'IF F<1 THEN F=0:Z=3:GOTO 9000',
460:'IF E=0 AND T>0 THEN A$="ORAGE: radio coupée":GOSUB 900',
470:'IF E>0 AND T=0 THEN W=3+INT(RND(1)*4):GOSUB 1850',
475:'IF U=0 AND G(64)>0 THEN A$="VENTS FORTS CONSO+2":GOSUB 900',
480:'GOSUB 2000:GOTO 200',
900:'CLS:PRINT A$;:GOSUB 100:RETURN',
1000:'U=2-2*(T>0)',
1010:'A=U*INT(X/(4*U)):I=U*INT(Y/(4*U))+1',
1020:'CLS:PRINT CHR$(65+A);I;"~ C";45*D;',
1040:'PRINT " H";H;" V";V;" F";F;" ";',
1070:f'PRINT MID$("{MOTION_ICONS}",P+2,1);',
1100:'IF T>0 THEN PRINT " ORG";:RETURN',
1105:'IF J>0 THEN GOSUB 2150:PRINT " ";A$;:RETURN',
1107:'IF G(64)>0 THEN PRINT " VENT+";:RETURN',
1110:'IF R>0 THEN PRINT " R";R; ELSE PRINT " RAD";',
1120:'RETURN',
1200:'IF X<0 OR X>95 OR Y<0 OR Y>79 THEN Z=4:RETURN',
1210:'GOSUB 1300:IF H>0 THEN 1280',
1220:'IF Q<10 OR Q>13 OR V>100 THEN Z=2:RETURN',
1230:'IF Q=10 OR Q=12 THEN IF D<>0 AND D<>4 THEN Z=2',
1240:'IF Q=11 OR Q=13 THEN IF D<>2 AND D<>6 THEN Z=2',
1250:'IF Z>0 THEN RETURN',
1260:'IF INT(Y/4)=2 AND V>=60 THEN Z=1',
1270:'RETURN',
1280:'IF H<=L THEN Z=2',
1285:'IF Q>=3 AND Q<=4 AND H<=150 THEN F=F-1',
1290:'RETURN',
1300:'I=INT(Y/4):GOSUB 1400',
1310:'Q=ASC(MID$(M$,INT(X/4)+1,1))-65',
1320:'L=50*(ASC(MID$("00011468::0000",Q+1,1))-48)',
1330:'RETURN',
# Whole-row spans avoid interpreting all regional rules 480 separate times.
# Overlay bounds are guaranteed by each span's centre and maximum radius.
1400:'M$="AAAAAAAAAAAAAAAAAAAAAAAA"',
1410:'IF I=2 THEN M$="AANLLNAAAAAAAAAAAAAAAAAA":RETURN',
1420:'IF I<4 OR I>16 THEN 1580',
1430:'L=4-ABS(I-6):IF L<0 THEN 1460',
1440:'A$=LEFT$("BBBBBBBBB",2*L+1)',
1450:'A=8+INT(S/30)MOD 4-L:GOSUB 1900',
1460:'L=2-INT(ABS(I-14)/2):IF L<0 THEN 1490',
1470:'A$=MID$("DEDEDE",1+S MOD 2,2*L+1)',
1480:'A=6+INT(S/120)MOD 6-L:GOSUB 1900',
1490:'L=2-ABS(I-6-S MOD 2):IF L<0 THEN 1520',
1500:'A$=LEFT$("EDEDE",2*L+1)',
1510:'A=18-L:GOSUB 1900',
1520:'L=ABS(I-8-INT(S/6)MOD 5):IF L>4 THEN 1580',
1530:'A$="'+''.join(MOUNTAIN_ROWS)+'"',
1531:'A$=MID$(A$,8*L+1,8)',
1540:'A=7+S MOD 6:GOSUB 1900',
1580:'IF I<15 OR I>18 THEN 1600',
1590:'M$=LEFT$(M$,21)+"KAA"',
1595:'IF I=15 OR I=18 THEN M$=LEFT$(M$,21)+"MAA"',
1600:'RETURN',
# Comparisons return -1 for true: water raises the chance from 10% to 30%.
# Q is the starting cell; the flight collision check refreshes it each step.
1800:'IF RND(1)>=.1-.2*(Q=1) THEN RETURN',
1810:'T=2+INT(RND(1)*4):RETURN',
1850:'A$="Radio rétablie":GOTO 900',
1900:'U=LEN(A$)',
1910:'M$=LEFT$(M$,A)+A$+MID$(M$,A+U+1,24):RETURN',
2000:'IF T>0 THEN RETURN',
2010:'IF J=0 THEN 2050',
2020:'IF M>0 AND H>=M THEN 2120',
2030:'J=J-1:IF J>0 THEN RETURN',
2040:'A$="TOUR: délai écoulé":GOTO 900',
2050:'IF N MOD 8<>0 OR H<150 OR Y<20 OR R>0 THEN RETURN',
2060:'IF RND(1)>.5 THEN RETURN',
2070:'J=6:M=0',
2080:'IF H<400 AND RND(1)<.5 THEN M=300-100*(H>=300)',
2090:'GOSUB 2150:A$="TOUR: "+A$+" PAS":GOTO 900',
2120:'O=O+1:J=0:A$="Consigne +20":GOTO 900',
2150:'A$="RAD":IF M>0 THEN A$="H"+STR$(M)',
2160:'A$=A$+"/"+STR$(J):RETURN',
4000:f'CLS:PRINT "Pas ";N;" F";F;"/{INITIAL_FUEL} RET:fin";',
4020:'GOSUB 100:IF E=8 THEN END',
4050:'RETURN',
5000:'IF T>0 THEN A$="Radio coupée":GOTO 900',
5005:'GOSUB 1300',
5006:'IF Q=1 AND H<150 THEN A$="EAU: radar dès H150":GOTO 900',
5010:'IF R=0 THEN 5040',
5020:'A$="RAD: attendre "+STR$(R):GOTO 900',
5040:'CLS:PRINT "RADAR ENT:oui RET:non";',
5050:'GOSUB 100:IF E=8 THEN RETURN',
5060:'IF E<>13 THEN 5050',
5070:'IF F<2 THEN A$="Carburant bas":GOTO 900',
5080:'F=F-1:R=4:CLS:PRINT "RELEVÉ RADAR";',
5085:'IF J>0 AND M=0 THEN O=O+1:J=0',
5090:f'G={MAP_X}+4*X-6:K={MAP_Y}+14*Y-21:GOSUB 50',
5100:'GLYPH G(56),8,8,4:B=K+56:C=G',
5110:'GOSUB 6110',
5120:'A$="TOUR: "+CHR$(65+INT(X/4))',
5130:'A$=A$+STR$(INT(Y/4)+1)+" OK":SOUND 600,60',
5140:'GOTO 900',
6000:'LPRINT "VOL RADAR CARTE ";S:B=56:C=0',
6010:f'G={MAP_X}:K=112:GOSUB 50',
6020:'LPRINT "ABCDEFGHIJKLMNOPQRSTUVWX";:C=480',
6030:'FOR I=0 TO 19:GOSUB 1400',
6040:'CLS:PRINT "IMPRESSION CARTE ";I+1;"/20";',
6050:f'G=40*(I MOD 2):K={MAP_Y}+56*I:GOSUB 50',
6060:'LPRINT RIGHT$(" "+STR$(I+1),2);:C=G+32',
6070:'FOR J=0 TO 23',
6080:'G(64+J)=ASC(MID$(M$,J+1,1))-65:NEXT J',
6090:f'G={MAP_X}:GOSUB 50',
6100:'GLYPH G(0),24,8,5:B=K+56:C=G:NEXT I',
6110:f'G=0:K={VIEW_Y}:GOTO 50',
7000:'A$="CAP:flèches V:marges T+/-:H":GOSUB 900',
7010:'A$="TEXT:= ENT:vol RET:bilan":GOSUB 900',
7020:'A$="RELOC/REPEAT:RAD H0 V60-100":GOTO 900',
8000:'CLEAR:CLS:CURSOR 4',
8010:'PRINT "VOL RADAR 0.5 ENT:vol ESP:?";',
# Advance the PRNG while waiting for the menu key. This adds human timing even
# in Studio's functional CPU, whose free-running timer registers stay fixed.
8020:'A=RND(1):E=INKEY(0):IF E=0 THEN 8020',
8021:'IF E=8 THEN END',
8030:'IF E=32 THEN GOSUB 7000:GOTO 8000',
8040:'IF E<>13 THEN 8020',
8041:'INPUT "CARTE 0=HASARD";S',
8042:'IF S<0 OR S>999 OR S<>INT(S) THEN 8041',
8043:'IF S=0 THEN S=1+INT(RND(1)*999)',
8044:'M=0:O=0',
8050:'CLS:PRINT "IMPRESSION CARTE";:LSPACING 1',
8060:'DIM G(87):B=0:C=0:RESTORE',
8080:'FOR I=4 TO 55:IF (I-4)MOD 26=0 THEN READ A$',
8081:'J=2*((I-4)MOD 26)+1',
8082:'U=(480-ASC(MID$(A$,J,1)))MOD 256',
8083:'G(I)=256*U+(480-ASC(MID$(A$,J+1,1)))MOD 256',
8084:'NEXT I:GOSUB 6000',
8090:'FOR I=56 TO 62:G(I)=16:NEXT I',
8095:'G(59)=254',
8096:'G(64)=0:J=0',
8100:f'X=86:Y=74:D=0:V=0:H=0:P=0:F={INITIAL_FUEL}',
8110:'N=0:T=0:R=0:Z=0',
8120:'RANDOMIZE S',
8130:'W=5:Q=10',
8140:'A$="V19>C3-F3 V100 T+ ENT":GOSUB 900',
8160:'GOTO 200',
9000:'IF Z=1 THEN A$="POSÉ ! SCORE "+STR$(100+5*F-N+20*O)',
9010:'IF Z=2 THEN A$="CRASH: terrain"',
9020:'IF Z=3 THEN A$="Panne sèche"',
9030:'IF Z=4 THEN A$="Hors de la carte"',
9040:'IF Z=5 THEN A$="Décrochage !"',
9050:'IF Z=1 THEN SOUND 440,70:SOUND 660,120',
9060:'IF Z<>1 THEN SOUND 120,180',
9070:'GOSUB 900:CLS:PRINT "ENT:rejouer RET:fin";',
9080:'GOSUB 100:IF E=13 THEN 8000',
9090:'END',
}

TRANSLATE = {
 'VOL RADAR 0.5 ENT:vol ESP:?':'RADAR FLIGHT 0.5 ENT:go SPC:?',
 'VENTS FORTS CONSO+2':'WIND: EXTRA FUEL +2',
 ' VENT+':' WIND+',
 'TOUR: délai écoulé':'TOWER: time expired',
 'Consigne +20':'Request +20',
 ' PAS':' STEPS',
 'POSÉ ! SCORE ':'LANDED! SCORE ',
 'CARTE 0=HASARD':'MAP 0=RANDOM',
 'ORAGE: radio coupée':'STORM: radio lost',
 'Radio rétablie':'Radio restored',
 ' ORG':' STM',
 'Pas ':'Step ', ' F':' F',
 '/99 RET:fin':'/99 BS:quit',
 'Radio coupée':'Radio lost',
 'EAU: radar dès H150':'WATER: radar from H150',
 'RAD: attendre ':'RAD: wait ',
 'RADAR ENT:oui RET:non':'RADAR ENT:yes BS:no',
 'Carburant bas':'Low fuel',
 'RELEVÉ RADAR':'RADAR FIX',
 'TOUR: ':'TOWER: ', ' OK':' OK',
 'VOL RADAR CARTE ':'RADAR FLIGHT MAP ',
 'IMPRESSION CARTE ':'PRINTING MAP ', 'IMPRESSION CARTE':'PRINTING MAP',
 'CAP:flèches V:marges T+/-:H':'HDG:arrows V:margins T+/-:H',
 'TEXT:= ENT:vol RET:bilan':'TEXT:= ENT:fly BS:status',
 'RELOC/REPEAT:RAD H0 V60-100':'RELOC/REPEAT:RAD H0 V60-100',
 'CRASH: terrain':'CRASH: terrain',
 'Panne sèche':'Out of fuel', 'Hors de la carte':'Outside the map',
 'Décrochage !':'Stall!', 'ENT:rejouer RET:fin':'ENT:replay BS:quit',
}


def terrain_row(seed,y):
    """Host rendering oracle; the standalone game executes its own BASIC copy."""
    assert 1 <= seed <= 999 and 0 <= y < 20
    row = list('A'*24)
    def place(x,text):
        assert 4 <= x and x+len(text) <= 21,(seed,y,x,text)
        row[x:x+len(text)] = text
    if y == 2:
        row[2:6] = 'NLLN'
    if 4 <= y <= 16:
        radius = 4-abs(y-6)
        if radius >= 0:place(8+(seed//30)%4-radius,'B'*(2*radius+1))
        radius = 2-abs(y-14)//2
        if radius >= 0:place(6+(seed//120)%6-radius,('DEDEDE')[seed%2:seed%2+2*radius+1])
        radius = 2-abs(y-6-seed%2)
        if radius >= 0:place(18-radius,('EDEDE')[:2*radius+1])
        distance = abs(y-(8+(seed//6)%5))
        if distance <= 4:place(7+seed%6,MOUNTAIN_ROWS[distance])
    if 15 <= y <= 18:row[21] = 'M' if y in (15,18) else 'K'
    assert len(row) == 24
    return [ord(c)-65 for c in row]


def terrain_cell(seed,x,y):
    assert 0 <= x < 24
    return terrain_row(seed,y)[x]


def terrain_map(seed):
    return [terrain_row(seed,y) for y in range(20)]


def source(language='fr', *, labels=False):
    assets = json.loads(ASSET_PATH.read_text(encoding='utf-8'))
    lines = dict(BODY)
    # The five mountain silhouettes are sliced from one inline 40-byte atlas.
    # Offset 224 keeps every byte printable and quote-free for this palette.
    # Editable pixel rows remain explicit in flight-simulator-assets.json.
    # The BASIC row routine positions terrain spans once for each printed row.
    palette = []
    for tile in assets['tiles']:
        rows = tile['rows']
        assert len(rows) == 8 and all(0 <= b < 256 for b in rows)
        # DIM zero-fills the blank tile and the two spare slots (0,14,15).
        if tile['id'] in (0,14,15):
            assert not any(rows)
            continue
        raw = bytes((224-b)&255 for b in rows)
        assert all(b >= 32 and b not in (34,127) for b in raw)
        literal = ''.join(chr(b) if b < 127 else LCD_TO_UNICODE.get(b,chr(0xe000+b)) for b in raw)
        assert encode_source('"'+literal+'"')[1:-1] == raw
        palette.append(literal)
    packed = ''.join(palette)
    for i in range(0,len(packed),52):
        lines[600+i//52] = 'DATA"'+packed[i:i+52]+'"'
    if language == 'en':
        for n, line in lines.items():
            lines[n] = re.sub(r'"([^\"]*)"', lambda m:'"'+TRANSLATE.get(m[1],m[1])+'"',line)
    lines = compact(lines, merge_before=65536)
    # Dense public line numbers save about 100 bytes of branch operands.
    # The generator retains spaced logical labels for maintaining routines.
    public = {n:i+1 for i,n in enumerate(sorted(lines))}
    def branch_numbers(line):
        parts = re.split(r'("[^"]*")',line)
        for i in range(0,len(parts),2):
            parts[i] = re.sub(r'\b(GOTO|GOSUB|THEN|ELSE)\s+(\d+)',
                lambda m:m[1]+' '+str(public[int(m[2])]),parts[i])
        return ''.join(parts)
    text = ''.join(f'{public[n]} {branch_numbers(line)}\n' for n,line in sorted(lines.items()))
    result = analyze(text)
    assert not result.issues, result.issues
    return (text,result,public) if labels else (text,result)


def main():
    for lang, name in [('fr','simulateur-de-vol'),('en','flight-simulator')]:
        text, result = source(lang)
        path = ROOT/'examples/games'/f'{name}-{lang}.bas'
        path.write_text(text, encoding='utf-8', newline='\n')
        print(path.name, result.used, 'tokenized bytes', len(result.records), 'lines')
    render_tiles()
    render_maps()


def render_tiles():
    from PIL import Image, ImageDraw, ImageFont
    assets = json.loads(ASSET_PATH.read_text(encoding='utf-8'))
    im = Image.new('RGB', (640, 660), 'white')
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(str(ROOT/'docs/user-manual/fonts/Lato-Bold.ttf'), 20)
    draw.text((20, 8), '8 × 8 — GLYPH 0–15', font=font, fill='black')
    for tile in assets['tiles']:
        i = tile['id']
        x, y = 24+156*(i%4), 62+148*(i//4)
        draw.text((x, y-24), str(i), font=font, fill='black')
        native = Image.new('1', (8,8), 1)
        for yy, row in enumerate(tile['rows']):
            for xx in range(8):
                native.putpixel((xx,yy),0 if row&(128>>xx) else 1)
        im.paste(native.convert('RGB').resize((112,112),Image.Resampling.NEAREST),(x,y))
        for line in range(9):
            draw.line((x+line*14,y,x+line*14,y+112),fill='#cccccc')
            draw.line((x,y+line*14,x+112,y+line*14),fill='#cccccc')
    im.save(ROOT/'examples/guides/images/flight-tileset.png')


def render_maps():
    """Exact 8x8 palette pixels; actual printer captures are tested separately."""
    from PIL import Image, ImageDraw, ImageFont
    assets = json.loads(ASSET_PATH.read_text(encoding='utf-8'))
    tiles = []
    for tile in assets['tiles']:
        image = Image.new('1',(8,8),1)
        for y,row in enumerate(tile['rows']):
            for x in range(8):
                image.putpixel((x,y),0 if row&(128>>x) else 1)
        tiles.append(image)
    image = Image.new('RGB',(24*8*3*3+80,20*8*3+90),'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(ROOT/'docs/user-manual/fonts/Lato-Bold.ttf'),20)
    for index,seed in enumerate((1,42,999)):
        draw.text((20+index*596,12),f'{seed:03d}',font=font,fill='black')
        native = Image.new('1',(192,160),1)
        for y,row in enumerate(terrain_map(seed)):
            for x,tile in enumerate(row):
                native.paste(tiles[tile],(8*x,8*y))
        image.paste(native.convert('RGB').resize((576,480),Image.Resampling.NEAREST),(20+index*596,60))
    image.save(ROOT/'examples/guides/images/flight-procedural-maps.png')


if __name__ == '__main__':
    main()
