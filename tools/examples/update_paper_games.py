"""Preserve the supplied 16x16 artwork while batching paper game glyphs.

The asset JSON is the editable, numeric source. Ruins packs its atlas in quoted
native bytes to leave room for a row palette; Studio displays unmapped bytes
with hexadecimal badges. Gameplay and physical cell coordinates are retained.
"""
from pathlib import Path
import json
import sys
import re

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'studio/internal')]
from native_text import LCD_TO_UNICODE, encode_source
from core import analyze
from core import codec


def compact(lines):
    """Join untargeted fall-through lines; preserve literal and token bytes."""
    def signature(body):
        quote=False;result=bytearray()
        for value in codec.tokenize(body):
            if value==34:quote=not quote
            if quote or value!=32:result.append(value)
        return result
    targets={int(v) for b in lines.values() for v in re.findall(r'(?:GOTO|GOSUB|THEN|ELSE)\s+(\d+)',re.sub(r'"[^"]*"','""',b))}
    result={}
    for n,body in sorted(lines.items()):
        parts=re.split(r'("[^"]*")',body)
        for i in range(0,len(parts),2):parts[i]=re.sub(r'\s*([,:()+*/=<>-])\s*',r'\1',parts[i])
        trial=''.join(parts)
        if signature(trial)==signature(body):body=trial
        previous=next(reversed(result)) if result else None
        if previous and n not in targets and n<2000 and not body.startswith(('DATA','REM')):
            code=re.sub(r'"[^"]*"','""',result[previous])
            if not re.search(r'\b(IF|GOTO|RETURN|END|REM)\b',code) and len(str(previous))+2+len(result[previous])+len(body)<=63:
                result[previous]+=':'+body;continue
        result[n]=body
    return result


def native(data):
    return ''.join(chr(v) if v<127 else LCD_TO_UNICODE.get(v,chr(0xe000+v)) for v in data)


def ruins_controls(lines, lang):
    """Use Quest's ordered up/down/left/right selector on the LCD."""
    lines[10] = 'REM ' + ('LES RUINES DE TYPESTAR' if lang == 'fr' else 'TYPESTAR RUINS') + ' 0.6'
    arrows = native(bytes((169,32,170,32,201,32,200)))
    lines[360] = 'Q=P-10:IF D=1 THEN Q=P+10'
    lines[370] = 'IF D=2 THEN Q=P-1'
    lines[380] = 'IF D=3 THEN Q=P+1'
    lines[520] = f'PRINT " R";R;"/3 {arrows} ";48-N;"' + ('p ESP:?";' if lang == 'fr' else 't SPC:?";')


def replace(lines, first, last, block):
    for n in list(lines):
        if first<=n<=last:del lines[n]
    for row in block.strip().splitlines():
        n,body=row.split(' ',1);lines[int(n)]=body


def main():
    assets=json.loads(Path(__file__).with_name('paper-game-assets.json').read_text())
    blobs=[bytes(b for word in tile for b in (word>>8,word&255)) for tile in assets['ruins']]
    bad=set(range(32))|{34,126,127}
    offset=min(range(256),key=lambda k:sum((k-b)&255 in bad for blob in blobs for b in blob))
    packed=[]
    for blob in blobs:
        data=[]
        for b in blob:
            v=(offset-b)&255
            data.extend((126,v+35) if v in bad else (v,))
        packed.append(native(data))
    for lang,name in [('fr','ruines-typestar'),('en','typestar-ruins')]:
        p=ROOT/f'examples/games/{name}-{lang}.bas'
        lines={int(n):b for n,b in (row.split(' ',1) for row in p.read_text(encoding='utf-8').splitlines())}
        ruins_controls(lines, lang)
        lines[20]='CLS:CURSOR 4:PRINT "'+('LES RUINES - CHARGEMENT' if lang=='fr' else 'RUINS - LOADING')+'";:LSPACING 1'
        lines[1]='GOTO 10'
        lines[40]='DIM M(79):DIM G(83):DIM S(20):DIM D(10)'
        title='LES RUINES DE TYPESTAR' if lang=='fr' else 'TYPESTAR RUINS'
        label='IMPRESSION CARTE ' if lang=='fr' else 'PRINTING MAP '
        replace(lines,1180,1199,'''
1180 W=1:L=S(1):FOR V=0 TO 1:Z=8*V
1182 GOSUB 1410:NEXT V
1184 FOR I=16 TO 23:G(I)=0:NEXT I:RETURN
''')
        replace(lines,1200,1261,f'''
1200 LPRINT "{title}":B=56
1202 A=&H20C0
1203 IF PEEK(A+1)*256+PEEK(A+2)>=2000 THEN 1206
1204 A=A+PEEK(A):GOTO 1203
1206 FOR T=1 TO 10:L=A+3
1207 IF PEEK(L)<>34 THEN L=L+1:GOTO 1207
1208 S(T)=L+1:A=A+PEEK(A):NEXT T
1209 FOR T=1 TO 10:READ A$:NEXT T:GOSUB 1180
1210 FOR Y=0 TO 7:CLS:PRINT "{label}";Y+1;"/8";
1214 FOR V=0 TO 1:X=0
1216 FOR I=0 TO 10:D(I)=-1:NEXT I
1218 U=3:Q=0:D(0)=2:D(1)=V
1219 G=16+32*X:K=168+112*Y+56*V:GOSUB 1500
1220 J=10*Y+X:W=M(J):IF J=10 THEN W=7
1222 IF J=11 THEN W=9
1224 IF D(W)>=0 THEN 1240
1226 IF U=8 THEN 1250
1228 D(W)=U:U=U+1
1233 L=S(W+10*V):Z=8*D(W)
1235 GOSUB 1410
1240 G(64+2*Q)=2*D(W):G(65+2*Q)=2*D(W)+1
1242 Q=Q+1:X=X+1:IF X<10 THEN 1220
1250 GLYPH G(0),2*Q,8,5:B=K+56:C=G
1252 IF X<10 THEN 1216
1254 NEXT V:NEXT Y
''')
        lines[1262]='FOR I=0 TO 11:READ G(I):NEXT I'
        lines[1264]='G(16)=6:G(17)=15:G(18)=15:G(19)=6'
        replace(lines,1400,1424,'')
        replace(lines,1410,1419,'''
1410 FOR O=0 TO 3:GOSUB 2:F=256*A
1412 GOSUB 2:E=256*A:GOSUB 2
1414 G(Z+O)=F+A:GOSUB 2
1416 G(Z+4+O)=E+A:NEXT O
1418 IF V=0 THEN S(W+10)=L
1419 RETURN
''')
        replace(lines,2,8,f'''
2 A=PEEK(L):L=L+1
4 IF A=126 THEN A=PEEK(L)-35:L=L+1
6 A={offset}-A:IF A<0 THEN A=A+256
8 RETURN
''')
        replace(lines,2000,9999,'\n'.join(f'{2000+i} DATA "{text}"' for i,text in enumerate(packed))+
                '\n2020 DATA '+','.join(map(str,assets['ruins_cross'][:6]))+
                '\n2021 DATA '+','.join(map(str,assets['ruins_cross'][6:])))
        lines=compact(lines)
        source=''.join(f'{n} {lines[n]}\n' for n in sorted(lines))
        a=analyze(source);assert not a.issues,a.issues
        p.write_text(source,encoding='utf-8');print(p.name,a.used,a.free)

    # Twelve 8x8 quadrants, with palette tile 0 left blank. Each 16x16 sprite
    # retains the same 48 words overall; only the order of bits changes.
    palette=[]
    for tile in assets['orbital']:
        for y0,shift in ((0,8),(0,0),(8,8),(8,0)):
            b=[(tile[y]>>shift)&255 for y in range(y0,y0+8)]
            palette.extend(256*b[i]+b[i+1] for i in range(0,8,2))
    for lang,name in [('fr','duel-orbital'),('en','orbital-duel')]:
        p=ROOT/f'examples/games/{name}-{lang}.bas'
        lines={int(n):b for n,b in (row.split(' ',1) for row in p.read_text(encoding='utf-8').splitlines())}
        lines[10]=('REM TYPESTAR - DUEL ORBITAL 2.0' if lang=='fr' else 'REM TYPESTAR - ORBITAL DUEL 2.0')
        replace(lines,1200,1285,'''
1200 LSPACING 1:B=0:C=0:DIM Q(100)
1210 Q(100)=1
1230 LPRINT "TYPESTAR - DUEL ORBITAL":B=56
1240 G=16:K=224:GOSUB 1500:F=0
1245 FOR T=0 TO 15
1250 FOR I=0 TO 3:A=32896:IF T=15 THEN A=0
1251 IF T=15 AND I=0 THEN A=32768
1252 H=0:IF F=2*I THEN H=256
1253 IF F=2*I+1 THEN H=1
1254 Q(4+I)=A:Q(8+I)=255*H:Q(12+I)=A+127*H:NEXT I
1255 H=0:IF F<8 THEN H=2
1256 FOR I=0 TO 11:Q(64+3*I)=1+H
1257 Q(65+3*I)=H:Q(66+3*I)=H:NEXT I
1258 GLYPH Q(0),37,8,5:B=B+56:C=G
1260 F=F-8:IF F<0 THEN F=F+20
1270 NEXT T:RETURN
1280 GOTO 1286
''')
        if lang=='en':lines[1230]='LPRINT "TYPESTAR - ORBITAL DUEL":B=56'
        lines[35]='DIM Z(72):FOR I=4 TO 51:READ Z(I):NEXT I'
        replace(lines,190,210,'''
190 GOSUB 660:J=P:W=L:IF D=1 THEN W=1
200 GOSUB 1400:T=1:GOSUB 1450
202 IF D=0 THEN 218
204 FOR I=1 TO L-1:J=P+6*I
206 GOSUB 1400:T=1:W=1:GOSUB 1450:NEXT I
218 GOSUB 1600:NEXT S
''')
        lines[440]='V=1:GOSUB 1400:T=1:W=1:GOSUB 1450'
        replace(lines,750,752,'''
750 GOSUB 1400:T=9:IF S=0 THEN T=5
752 W=1:GOSUB 1450
''')
        replace(lines,1450,1469,'''
1450 FOR R=0 TO 1:FOR O=0 TO W-1
1452 Z(64+3*O)=T+2*R:Z(65+3*O)=T+2*R+1
1454 Z(66+3*O)=0:NEXT O
1456 GLYPH Z(0),3*W-1,8,5:B=B+56:C=G
1458 NEXT R:RETURN
''')
        replace(lines,1700,9999,'\n'.join(f'{1700+i} DATA '+','.join(map(str,palette[i:i+8])) for i in range(0,len(palette),8)))
        source=''.join(f'{n} {lines[n]}\n' for n in sorted(lines))
        a=analyze(source);assert not a.issues,a.issues
        p.write_text(source,encoding='utf-8');print(p.name,a.used,a.free)


if __name__=='__main__':main()
