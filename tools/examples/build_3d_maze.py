"""Generate the bilingual LCD maze for Typestar BASIC 0.4.100-dev.

Treasure/exit idea: Labyrinthe by François Rapenne, Sharp PC-1500,
Hebdogiciel issue 41, 20 July 1984, page 14. Movement and rendering are new.

A stackless depth-first generator carves a connected, random 10 x 10 maze.
Runtime raycasts select three triplets from small drawing strings.
Seven fixed LCDCHAR patterns plus native dash, equals and space form a
tiny tile set. PRINT draws nine cells from this set;
their CGRAM pixels are loaded only once, before play. Slot 7 switches
between a closed wall tile and three distance-scaled monster sprites.
A numeric array holds the generated map; stored source stays unchanged.
Optional map fragments reuse that array for fast paper tiles, with the
world saved in the existing view strings and restored before play resumes.
"""
from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'studio/internal'))
from core import analyze

# Physical LCD columns, including the one-pixel gap between 5-pixel cells.
PLANES=[(0,52,0,6),(10,42,1,5),(17,35,2,4),(22,30,3,3)]
LEFT_BRACKET=(0,31,16,16,16,31,0)
RIGHT_BRACKET=(0,31,1,1,1,31,0)
WALL_TILE=(0,31,17,17,17,31,0)
MONSTERS={1:(14,31,21,31,31,21,21),
          2:(0,4,14,10,14,10,0),
          3:(0,0,4,4,4,0,0)}

def half_view(stop,bits):
    """Four left cells of a nine-cell view, with LCD gaps accounted for."""
    pix=[[0]*53 for _ in range(7)]
    def line(x0,y0,x1,y1):
        dx=abs(x1-x0);sx=1 if x0<x1 else -1
        dy=-abs(y1-y0);sy=1 if y0<y1 else -1;err=dx+dy
        while True:
            pix[y0][x0]=1
            if (x0,y0)==(x1,y1):break
            e=2*err
            if e>=dy:err+=dy;x0+=sx
            if e<=dx:err+=dx;y0+=sy
    for depth in range(3):
        l,r,t,b=PLANES[depth];ll,rr,tt,bb=PLANES[depth+1]
        if bits&(1<<depth):
            line(l,t,ll,tt);line(l,b,ll,bb)
        else:
            line(l,tt,ll,tt);line(l,bb,ll,bb);line(l,tt,l,bb)
        line(ll,tt,ll,bb)
        if stop==depth:
            line(ll,tt,rr,tt);line(ll,bb,rr,bb)
            break
    return tuple(tuple(sum(pix[y][cell*6+x]<<(4-x) for x in range(5))
                       for y in range(7)) for cell in range(4))

# All possible corridor shapes, independent of the generated map. The outer
# three cells depend only on the first two side walls. The middle triplet
# depends on the stop depth and the two farthest side walls. This replaces
# the old 400-state table with three groups (6, 10, 6 triplets). The two
# outer groups share one 36-byte BASIC string; the centre uses 30 bytes.
NATIVE_GLYPHS={45:(0,0,0,31,0,0,0),61:(0,0,31,0,31,0,0),32:(0,)*7}
SHAPES=[]
for stop in range(4):
    for left in range(2**min(stop+1,3)):
        for right in range(2**min(stop+1,3)):
            a=half_view(stop,left)
            b=tuple(tuple(int(f'{v:05b}'[::-1],2) for v in cell)
                    for cell in reversed(half_view(stop,right)))
            center=WALL_TILE if stop==0 else a[3] if stop==1 else (
                NATIVE_GLYPHS[45] if stop==2 else NATIVE_GLYPHS[32])
            if stop==0:
                a=a[:2]+(LEFT_BRACKET,RIGHT_BRACKET)
                b=(LEFT_BRACKET,RIGHT_BRACKET)+b[2:]
            SHAPES.append((stop,left,right,a+(center,)+b))
GLYPHS=sorted({g for _,_,_,cells in SHAPES for g in cells}
              -set(NATIVE_GLYPHS.values())-{WALL_TILE})
assert len(GLYPHS)==7
NATIVE_CODES=(45,61,32)
BANK=GLYPHS+[WALL_TILE]+[NATIVE_GLYPHS[c] for c in NATIVE_CODES]
TRIPLES=[[None]*n for n in (6,10,6)]
for stop,left,right,cells in SHAPES:
    indices=(left if stop==0 else 2+(left&3),
             0 if stop==0 else 1 if stop==1 else 2+4*(stop-2)+(left>>2)+2*(right>>2),
             right if stop==0 else 2+(right&3))
    for b,i in enumerate(indices):
        value=''.join(chr(35+BANK.index(g)) for g in cells[b*3:b*3+3])
        assert TRIPLES[b][i] in (None,value)
        TRIPLES[b][i]=value
assert all(None not in t for t in TRIPLES)

# The numeric array V(0)..V(99) holds the generated cells. Low nibble:
# open N/E/S/W passages. High nibble: parent direction + 1. Walking reverses
# the edge of this tree, keeping it rooted at the player. Hunting then
# needs one parent lookup, but only within three actual passage steps.
# Bit 7 marks a hidden paper fragment. V(100) selects paper; V(101) counts
# discoveries. They remain outside the 100 map cells saved during printing.
# The stored BASIC program remains unchanged, including its retention CRC.
# The player spawns at a junction recorded while carving. Its parent chain is
# reversed to make it the player's root. The monster begins in a far corner;
# it wanders beyond its three-step hearing range.
# Advance RND while awaiting the initial key: host BASIC adapters need not
# model the MCU's free-running counter for successive games to differ.
BODY={
# Parent directions double as the DFS return path. A cell is visited iff
# V(cell)>0; the entrance bit marks the root. No second map/stack needed.
20:'V(0)=8:C=0:B=0:M=0',
22:'S=INT(RND(1)*4):A=0',
24:'P=C+ASC(MID$("(3<1",S+1,1))-50',
26:'IF P<0 OR P>99 THEN 44',
28:'IF ABS(P MOD 10-C MOD 10)>1 THEN 44',
30:'IF V(P)>0 THEN 44',
32:'Q=(S+2) MOD 4:J=2^Q',
34:'V(P)=16*(Q+1)+J',
36:'V(C)=V(C)+2^S:W=V(C) AND 15',
37:'IF W=7 OR W=11 OR W>12 THEN M=C',
38:'C=P:B=B+1',
40:'IF B<99 THEN 22',
42:'GOTO 50',
44:'A=A+1:S=(S+1) MOD 4:IF A<4 THEN 24',
46:'S=INT(V(C)/16)-1',
48:'C=C+ASC(MID$("(3<1",S+1,1))-50:GOTO 22',
60:'FOR A=0 TO 1:FOR B=0 TO 1',
62:'J=10*(1+4*A+INT(RND(1)*4))',
64:'J=J+1+5*B+INT(RND(1)*4)',
# Random positions start at column 1 or 6 within each sector. If a candidate
# equals the starting cell, shift it left once, staying in the same sector.
66:'J=J+(J=C):V(J)=V(J)+128',
# Every candidate has at least three internal passages. Cell 0 cannot be the
# selected root because M=0 triggers regeneration. The outside opening in 99
# is added only after selection, so neither outside passage counts as a road.
# A rare single winding corridor is discarded before starting the game.
50:'IF M=0 THEN FOR C=0 TO 99:V(C)=0:NEXT C:GOTO 20',
52:'C=M:A=C:Q=0:V(99)=V(99)+4',
54:'S=INT(V(A)/16)-1:V(A)=(V(A) AND 15)+Q',
56:'IF S<0 THEN 60',
58:'Q=16*(1+(S+2) MOD 4)',
59:'A=A+ASC(MID$("(3<1",S+1,1))-50:GOTO 54',
70:'NEXT B:NEXT A:V(101)=0:RETURN',
100:'T=1+INT(RND(1)*8):U=1+INT(RND(1)*8)',
110:'X=C MOD 10:Y=INT(C/10):F=0:N=0:O=-1',
120:'D=1-(V(C) AND 1):R=-99*(C<50):M=3',
140:'CLS:PRINT @TREASURE@;CHR$(65+T);U+1;',
150:'PRINT @EXITSTART@;:SOUND 0,1200:CLS:GOTO 400',
200:'GOSUB 1100',
210:'IF K=18 THEN D=(D+3) MOD 4:GOTO 400',
220:'IF K=19 THEN D=(D+1) MOD 4:GOTO 400',
230:'IF K=8 THEN D=(D+2) MOD 4:GOTO 400',
240:'IF K=32 THEN GOSUB 600:GOSUB 700:GOTO 200',
250:'IF K=81 OR K=113 THEN 950',
260:'IF K<>13 THEN 200',
280:'IF H=0 THEN C$=@WALL@:GOTO 370',
290:'A=C+ASC(MID$("(3<1",D+1,1))-50',
300:'IF A<0 THEN C$=@ENTRANCE@:GOTO 370',
310:'IF A>99 THEN 850',
325:'V(C)=(V(C) AND 143)+16*(D+1)',
330:'C=A:X=C MOD 10:Y=INT(C/10):V(C)=V(C) AND 143',
335:'N=N+1:IF F=0 AND X=T AND Y=U THEN GOSUB 800',
342:'IF R=C THEN GOSUB 1600',
344:'IF N MOD 2=0 THEN GOSUB 1300',
346:'IF R=C THEN GOSUB 1600',
348:'IF V(C)>127 THEN GOSUB 2250',
350:'GOTO 400',
370:'GOSUB 1200:SOUND 120,40:SOUND 0,300:GOSUB 700:GOTO 200',
400:'A=C:H=0:P=0:S=0:Q=1:E=0',
401:'J=2^D:W=2^((D+3) MOD 4):L=2^((D+1) MOD 4)',
404:'B=V(A)',
406:'IF (B AND W)=0 THEN P=P+Q',
408:'IF (B AND L)=0 THEN S=S+Q',
410:'IF (B AND J)=0 THEN 430',
412:'A=A+ASC(MID$("(3<1",D+1,1))-50:H=H+1',
414:'IF A<0 OR A>99 THEN 430',
# Positive E: monster distance. Negative E: fragment distance. The first
# visible entity wins; a monster on a fragment has priority at that cell.
416:'IF E=0 AND A=R THEN E=H',
417:'IF E=0 AND H<3 AND V(A)>127 THEN E=-H',
418:'Q=2*Q:IF H<3 THEN 404',
430:'L=64*H+8*S+P:W=E:IF H=0 THEN W=4',
431:'IF E>0 AND G<=0 THEN SOUND 120,60',
432:'IF W<1 OR W=I THEN 440',
434:'LOCATE 1,1:FOR B=0 TO 6:PRINT CHR$(B);:NEXT B',
436:'GOSUB 1690+10*W:I=W:O=-1',
440:'IF L=O AND E=G THEN GOSUB 700:GOTO 200',
442:'A=2+(P AND 3):B=2+(S AND 3):W=1',
444:'IF H=0 THEN A=P:B=S:W=0',
446:'IF H>1 THEN W=4*H-6+INT(P/4)+2*INT(S/4)',
448:'LOCATE 1,1:PRINT MID$(A$,3*A+1,3);',
450:'PRINT MID$(B$,3*W+1,3);MID$(A$,3*B+19,3);',
470:'IF E>0 THEN LOCATE 1,5:PRINT CHR$(7);',
472:'IF E<0 THEN LOCATE 1,5:PRINT CHR$(46-151*(E=-1));',
520:'O=L:G=E:GOSUB 700:GOTO 200',
600:'C$=@HELP1@:GOSUB 1200:GOSUB 1100',
610:'C$=@HELP2@:GOSUB 1200:GOSUB 1100',
620:'C$=@TREASURE@+CHR$(65+T)+STR$(U+1)+@EXITHELP@',
630:'IF F=1 THEN C$=@EXITONLY@',
640:'GOSUB 1200:GOSUB 1100:RETURN',
700:'C$="":GOSUB 1200',
710:'PRINT CHR$(65+X);Y+1;',
720:'LOCATE 1,15:PRINT MID$(@COMPASS@,5*D+1,5);',
730:'PRINT " T";MID$("-+",F+1,1);@MAPCOUNT@;V(101);"/4";',
740:'PRINT @LIVES@;M;:RETURN',
800:'F=1:C$=@FOUND@:GOSUB 1200',
810:'SOUND 5500,90:SOUND 6000,130:SOUND 0,700:RETURN',
850:'IF F=1 THEN 900 ELSE C$=@NEEDTREASURE@:GOTO 370',
900:'CLS:PRINT @WON@;',
910:'SOUND 5500,90:SOUND 6000,90:SOUND 6500,180',
920:'SOUND 0,900:CLS:PRINT @WINSCORE@;N+1;@STEPSEND@;',
930:'GOSUB 1100',
950:'CLS:CURSOR 0:END',
1100:'IF INKEY(0)<>0 THEN 1100',
1110:'K=INKEY(0):IF K=0 THEN 1110 ELSE RETURN',
1200:'LOCATE 1,11:PRINT "                      ";',
1210:'LOCATE 1,11:PRINT LEFT$(C$,22);:RETURN',
# Hearing follows the real corridor, including corners, for at most three
# cells. Looking away never makes the player invisible. Beyond that range
# the monster chooses an open direction without knowing the player's route.
1300:'A=R:FOR B=1 TO 3:W=INT(V(A)/16) AND 7',
# The leading "2" encodes delta zero at the root: three parent lookups
# therefore stop at the player even when the distance is only one or two.
1304:'A=A+ASC(MID$("2(3<1",W+1,1))-50:NEXT B',
1308:'W=INT(RND(1)*4)',
1320:'IF A=C THEN W=(INT(V(R)/16) AND 7)-1',
1330:'A=R+ASC(MID$("(3<1",W+1,1))-50',
1330:'A=R+ASC(MID$("(3<1",W+1,1))-50',
# An unseen pursuer can reach an adjacent cell around a bend, but waits
# there instead of delivering an invisible hit. G is the previous view's E.
1332:'IF A<0 OR A>99 OR (V(R) AND 2^W)=0 THEN RETURN',
1334:'IF A=C AND G<1 THEN RETURN',
1336:'R=A:RETURN',
1600:'M=M-1:C$=@HIT@:GOSUB 1200:SOUND 120,100',
1610:'SOUND 0,500',
1620:'IF M=0 THEN 1800',
1630:'R=-99*(C<50):RETURN',
1800:'CLS:PRINT @LOST@;:SOUND 120,180',
1810:'GOSUB 1100:GOTO 950',
2000:'REM 3D 0.9',
2010:'DIM V(101):CURSOR 4:RANDOMIZE PEEK(9)*255+PEEK(10)+1',
2012:'CLS:PRINT @PAPER@;',
2013:'IF INKEY(0)<>0 THEN 2013',
2014:'R=RND(1):K=INKEY(0):IF K=0 THEN 2014',
2015:'IF K<>13 AND K<>8 THEN 2014',
2016:'V(100)=(K=13):CLS:PRINT @LOADING@;',
2050:'GOSUB 20:GOSUB 2400:GOSUB 2150:GOSUB 1730:I=4:GOTO 100',
2160:'B$="":FOR B=1 TO LEN(C$)',
2162:'A=ASC(MID$(C$,B,1))-35',
2164:'IF A>7 THEN A=ASC(MID$("-= ",A-7,1))',
2166:'B$=B$+CHR$(A):NEXT B:RETURN',
2250:'V(C)=V(C)-128:V(101)=V(101)+1',
2252:'C$=@FRAGMENT@+STR$(V(101))+"/4":GOSUB 1200',
2253:'IF V(100)=0 THEN SOUND 5500,100:RETURN',
2254:'IF V(101)>1 THEN ORIGIN 0,224:FEED -224',
2256:'LSPACING 2:J=5*INT(X/5):L=5*INT(Y/5)',
2260:'LPRINT @MAP@;V(101);"/4 - ";CHR$(65+X);Y+1',
# A cell is two Courier pitches wide and two 56-unit bands high. The grid
# starts at X=40; letters start at 48+32*i and numbers at Y=28+112*j.
# Set spacing before LLOCATE: it uses the current text pitch.
2262:'LPRINT"   ";MID$("A B C D E F G H I J",2*J+1,9)',
2263:'LSPACING 1:FEED 28:FOR G=0 TO 4:LLOCATE 2*G+1,1',
2264:'LPRINT RIGHT$(" "+STR$(L+G+1),2);:NEXT G',
2265:'LLOCATE 1,3:ORIGIN 0,28:FEED -28:HEAD 8',
2266:'A$="":B$="":FOR P=0 TO 49',
2267:'A$=A$+CHR$(V(P)):B$=B$+CHR$(V(P+50)):NEXT P',
# V(0..63): sixteen 8x8 wall tiles, four row-pair words per tile.
# Four such tiles form a 16x16 cell. For each quadrant, force its two
# internal edges open (OR 6,12,3,9); preserve only the cell's outer walls.
# V(64..73): the ten tile IDs in the current half-row of five cells.
2268:'FOR H=0 TO 15:P=0:IF (H AND 8)=0 THEN P=128',
2272:'IF (H AND 2)=0 THEN P=P+1',
2274:'S=P:W=P:IF (H AND 1)=0 THEN S=255',
2276:'IF (H AND 4)=0 THEN W=255',
2278:'Q=4*H:V(Q)=256*S+P:V(Q+1)=257*P',
2280:'V(Q+2)=257*P:V(Q+3)=256*P+W:NEXT H',
2282:'FOR G=0 TO 9:FOR H=0 TO 9',
2284:'E=10*(L+INT(G/2))+J+INT(H/2):P=E+1:C$=A$',
2286:'IF E>49 THEN C$=B$:P=E-49',
2288:'Q=ASC(MID$("6<39",1+2*(G MOD 2)+H MOD 2,1))-48',
2290:'V(64+H)=(ASC(MID$(C$,P,1)) AND 15) OR Q',
2292:'NEXT H:GLYPH V(0),10,8,5:NEXT G',
# Restore every map byte, including parent and undiscovered-fragment bits.
# Rebuild the LCD strings only after their saved map contents are consumed.
2294:'FOR P=0 TO 49:V(P)=ASC(MID$(A$,P+1,1))',
2296:'V(P+50)=ASC(MID$(B$,P+1,1)):NEXT P',
2298:'GOSUB 2400:ORIGIN 40,0:HEAD -40:FEED 280:O=-1:RETURN',
2400:'RESTORE:READ C$:GOSUB 2160:A$=B$:READ C$:GOSUB 2160:RETURN',
}
WORDS={
'fr':dict(LOADING='GÉNÉRATION',TITLE='LABYRINTHE 3D 0.9',
 PAPER='CARTES PAPIER? ENT:OUI RET:NON',FRAGMENT='FRAGMENT ',MAP='CARTE ',
 TREASURE='TRÉSOR ',EXITSTART=' / J10 S',
 STARTKEYS='ENT:AVANCE FLECHES:TOURNER ESP:?',WALL='MUR !',
 ENTRANCE='ENTRÉE',HELP1='ENT:AVANCE G/D:TOURNER',
 HELP2='RET:DEMI-TOUR Q:FIN',EXITHELP=' / J10 S',
 EXITONLY='J10 SUD',COMPASS='NORD EST  SUD  OUEST',
 MAPCOUNT=' C',STEPS=' P',LIVES=' PV',HIT='TOUCHÉ !',
 LOST='PERDU !',
 FOUND='TRÉSOR !',NEEDTREASURE="TRÉSOR D'ABORD",
 WON='BRAVO !',WINSCORE='GAGNÉ EN ',
 STEPSEND=' PAS',QUIT='FIN : '),
'en':dict(LOADING='GENERATING',TITLE='3D MAZE 0.9',
 PAPER='PRINT MAPS? ENTER:YES BS:NO',FRAGMENT='FRAGMENT ',MAP='MAP ',
 TREASURE='TREASURE ',EXITSTART=' / J10 S',
 STARTKEYS='ENT:WALK ARROWS:TURN SPACE:HELP',WALL='WALL!',
 ENTRANCE='ENTRANCE',HELP1='ENTER:WALK ARROWS:TURN',
 HELP2='BS:TURN BACK Q:QUIT',EXITHELP=' / J10 S',
 EXITONLY='J10 SOUTH',COMPASS='NORTHEAST SOUTHWEST ',
 MAPCOUNT=' M',STEPS=' S',LIVES=' HP',HIT='HIT!',
 LOST='CAUGHT!',
 FOUND='TREASURE!',NEEDTREASURE='TREASURE FIRST',
 WON='YOU ESCAPED!',WINSCORE='WON IN ',
 STEPSEND=' STEPS',QUIT='END: ')}

LEXEMES=re.compile(r'"[^"]*"|[A-Za-z][A-Za-z0-9$]*|[0-9]+(?:\.[0-9]+)?|[^ \t]')

# Short line references save scarce program RAM without changing statements.
# The generator retains spaced labels above for maintaining the routines.
LINE_MAP={n:i+1 for i,n in enumerate(sorted({1,2,3,*BODY,
    *range(2150,2158),1700,1710,1720,1730}))}

def renumber(body):
    pieces=re.split(r'("[^"]*")',body)
    for i in range(0,len(pieces),2):
        def target(match):
            kind,label=match.groups();label=int(label)
            if label==1690:
                return kind+' '+str(LINE_MAP[1700]-1)
            return kind+' '+str(LINE_MAP[label])
        pieces[i]=re.sub(r'\b(GOTO|GOSUB|THEN)\s+(\d+)',target,pieces[i])
        pieces[i]=pieces[i].replace(str(LINE_MAP[1700]-1)+'+10*W',str(LINE_MAP[1700]-1)+'+W')
    return ''.join(pieces)

def compact(body):
    """Keep word boundaries and quoted text; remove optional whitespace."""
    if body.startswith('REM '):return body
    words=LEXEMES.findall(body);i=0;quoted=False
    while i<len(body):
        if body[i]=='"':quoted=not quoted
        if body[i]==' ' and not quoted:
            candidate=body[:i]+body[i+1:]
            if LEXEMES.findall(candidate)==words:body=candidate;continue
        i+=1
    return body

def source(language):
    values=WORDS[language]
    rows={1:'GOTO 2000'}
    for number,original in BODY.items():
        body=original
        for key,value in values.items():body=body.replace('@'+key+'@','"'+value+'"')
        assert '@' not in body,(number,body)
        rows[number]=body
    for n,triples in enumerate((TRIPLES[0]+TRIPLES[2],TRIPLES[1]),2):
        rows[n]='DATA "'+''.join(triples)+'"'
    for i,bitmap in enumerate(GLYPHS):
        rows[2150+i]='LCDCHAR '+str(i+1)+','+','.join(map(str,bitmap))+',0'
    rows[2157]='RETURN'
    for style,bitmap in {**MONSTERS,4:WALL_TILE}.items():
        rows[1690+10*style]='LCDCHAR 8,'+','.join(map(str,bitmap))+',0:RETURN'
    result=''.join(f'{LINE_MAP[n]} {compact(renumber(body))}\n' for n,body in sorted(rows.items()))
    analysis=analyze(result)
    if analysis.issues:raise ValueError(analysis.issues)
    return result,analysis

def main():
    for lang,name in (('fr','labyrinthe-3d-fr'),('en','3d-maze-en')):
        text,a=source(lang)
        (ROOT/'examples/games'/f'{name}.bas').write_text(text,encoding='utf-8',newline='\n')
        print(f'{name}: {a.used} bytes, {a.free} before variables')
    print(f'{len(GLYPHS)} fixed bitmaps; {len(SHAPES)} corridor shapes; random depth-first map')

if __name__=='__main__':main()
