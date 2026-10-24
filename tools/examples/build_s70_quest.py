"""Self-contained Quest adaptation: strip rendering and short turn-based RPG.

Original assets: https://github.com/pR-0000/Canon_X-07_RPG
The native streaming row cache retains 8x8 tiles throughout each pass.
"""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'studio/internal'))
from core import analyze,codec

# B=0 means no map was printed this run. A printed map has the shared
# reading position below; only that known paper origin permits boss crosses.
PAPER_VIEW_Y=1736

# The five objective names occupy six native characters each for MID$ on the
# 32-cell HUD. Atlas decoding borrows the later A/G/X/Y scalars before CLEAR,
# preserving space for the paper cache while the full program is still in RAM.
# The Oasis is the water cell at displayed 26,6 (zero-based 25,5). Only this
# water cell can be entered; its type 9 selects guardian 4. Type 14 is scenery.
BODY='''50 A=G-C:IF A=0 THEN 54
51 IF ABS(A)>128 THEN A=SGN(A)*128
52 IF A<0 THEN ORIGIN 128,0 ELSE ORIGIN
53 HEAD A:C=C+A:GOTO 50
54 A=K-B:IF A=0 THEN 58
55 IF ABS(A)>448 THEN A=SGN(A)*448
56 IF A<0 THEN ORIGIN 0,448 ELSE ORIGIN
57 FEED A:B=B+A:GOTO 54
58 ORIGIN:RETURN
80 RESTORE:FOR J=0 TO A:READ M$:NEXT:RETURN
82 A=ASC(MID$(M$,INT(Q*.5)+1,1))-35:T=A MOD 15
83 IF Q MOD 2=0 THEN T=INT(A*.06667)
84 RETURN
100 IF INKEY(0)<>0 THEN 100
110 K=INKEY(0):IF K=0 THEN 110
120 RETURN
150 CLS:PRINT A$;:GOSUB 100:RETURN
200 CLS:PRINT X+1;",";Y+1;" PV";H;" NV";L;" >";
202 PRINT MID$("Cimet.Forêt RuinesOasis Tour  ",6*R+1,6);
205 LOCATE 1,25:PRINT"@ARROWS@";:LCDLINE 25+2*D,31
210 GOSUB 100:IF K=18 OR K=19 THEN 400
230 IF K=32 THEN GOSUB 8400:GOTO 200
240 IF K=8 THEN GOSUB 8500:GOTO 200
250 IF K<>13 THEN 210
260 Q=X:V=Y:IF D=0 THEN V=V-1
280 IF D=1 THEN V=V+1
290 IF D=2 THEN Q=Q-1
300 IF D=3 THEN Q=Q+1
310 IF Q<0 OR Q>29 OR V<0 OR V>15 THEN 390
320 A=V:GOSUB 80:GOSUB 82
330 IF T>=9 AND(Q<>25 OR V<>5)THEN 390
340 X=Q:Y=V:GOSUB 1000:IF H<1 THEN 9500
370 IF R=5 THEN 9600
380 GOTO 200
390 SOUND 120,35:GOTO 210
400 LCDLINE 25+2*D,0:D=(D+1)MOD 4
410 IF K=18 THEN D=(D+2)MOD 4
420 LCDLINE 25+2*D,31:GOTO 210
910 CLS:CURSOR 4:PRINT"CARTE: ENT imprimer RET passer";
912 GOSUB 100:IF K=8 THEN 925
914 IF K<>13 THEN 912
916 CLS:PRINT"IMPRESSION CARTE";:LSPACING 1
920 DIM G(93):B=0:C=0:GOSUB 6000
922 CLEAR:DIM G(7):B=@VIEWY@:GOTO 927
925 CLEAR:DIM G(7)
930 X=5:Y=13:D=0:L=1:H=30:F=20:P=0:R=0:E=0:N=0
935 S=0:W=0:C=0
940 RANDOMIZE PEEK(9)*255+PEEK(10)+1
950 A$="Trouvez le sorcier !":GOSUB 150
960 GOTO 200
1000 IF T=2 OR T=3 OR T=4 THEN GOSUB 1400:RETURN
1010 Z=0:IF T=6 THEN Z=1
1030 IF T=7 THEN Z=2
1040 IF T=5 THEN Z=3
1050 IF T=9 THEN Z=4
1060 IF T=8 THEN Z=5
1070 IF Z>R+1 THEN A$="Gardien précédent requis":GOTO 1190
1080 IF Z>0 AND Z<=R THEN RETURN
1085 IF L<2*Z THEN A$="Niveau requis: "+STR$(2*Z):GOTO 1190
1090 IF Z>0 THEN T=4:IF Z=2 THEN T=3
1100 IF Z=3 OR Z=4 THEN T=5
1110 IF Z=5 THEN T=6
1120 IF Z>0 THEN GOSUB 2000:RETURN
1130 IF N>0 THEN N=N-1:RETURN
1140 IF RND(1)>.3 THEN RETURN
1150 T=0:IF X>9 THEN T=1
1160 IF Y<9 THEN T=2:IF X>14 THEN T=3
1170 GOSUB 2000:N=1:RETURN
1190 GOTO 150
1400 CLS:PRINT"1 Repos 2 Potion 3 Épée 4 Armure";
1410 GOSUB 100:IF K=8 THEN RETURN
1420 J=K-49:IF J<0 OR J>3 THEN 1410
1430 Q=4:IF J=1 THEN Q=8
1440 IF J=2 THEN Q=40*(S+1)
1450 IF J=3 THEN Q=40*(W+1)
1460 IF J=2 AND S=2 OR J=3 AND W=2 THEN 1400
1470 CLS:PRINT"@COIN@";F;" PRIX @COIN@";Q;" ENT:OUI RET:NON";
1480 GOSUB 100:IF K=8 THEN 1400
1490 IF K<>13 OR F<Q THEN 1480
1500 F=F-Q:IF J=0 THEN H=24+6*L
1510 IF J=1 THEN P=P+1
1520 IF J=2 THEN S=S+1
1530 IF J=3 THEN W=W+1
1540 SOUND 550,50:GOTO 1400
2000 U=14+8*T+3*R:V=5+3*T+2*R:Q=T+INT(R/2)
2010 IF Z>0 THEN U=24+14*Z:V=7+3*Z:Q=Z+2
2015 GOSUB 2020+10*T:GOTO 2085
2020 A$="SLIME":RETURN
2030 A$="FANTôME":RETURN
2040 A$="ARAIGNÉE":RETURN
2050 A$="BANDIT":RETURN
2060 A$="SQUELETTE":RETURN
2070 A$="DÉMON":RETURN
2080 A$="SORCIER":RETURN
2085 IF Z>0 THEN A$="GARDIEN: "+A$
2090 GOSUB 150:J=0
2100 CLS:GOSUB 3000:GOSUB 3100
2110 LOCATE 1,7:PRINT" ATK DEF POT FUIR    ";
2115 LCDLINE 8+4*J,31
2120 GOSUB 100:IF K=18 OR K=19 THEN 2400
2130 IF K<>13 THEN 2120
2140 IF J=3 THEN 2450
2150 IF J=2 THEN 2800
2160 A=4+L+S-Q+INT(RND(1)*3)
2170 IF J=1 THEN A=2+INT(L/2)
2180 IF A<1 THEN A=1
2185 IF A>U THEN A=U
2190 U=U-A:O=0:IF U=0 THEN GOSUB 3300:GOTO 2500
2200 O=V-L-W:IF O<1 THEN O=1
2210 IF J=1 THEN O=INT((O+1)/2)
2215 IF O>H THEN O=H
2220 H=H-O:GOSUB 3300:IF H=0 THEN RETURN
2230 GOTO 2110
2400 LCDLINE 8+4*J,0:J=(J+1)MOD 4
2410 IF K=18 THEN J=(J+2)MOD 4
2420 LCDLINE 8+4*J,31:GOTO 2120
2450 IF Z>0 THEN SOUND 120,40:GOTO 2120
2460 SOUND 180,50:RETURN
2500 O=2+T:Q=3+2*T:IF Z>0 THEN GOSUB 2700
2510 F=F+Q:E=E+O
2520 A$="Victoire! +"+STR$(O)+" XP +"+STR$(Q)+"@COIN@"
2525 GOSUB 150
2530 IF E<6+4*L OR L=12 THEN RETURN
2540 E=E-6-4*L:L=L+1:H=24+6*L
2550 SOUND 440,60:SOUND 660,100
2560 A$="Niveau "+STR$(L):GOSUB 150
2570 GOTO 2530
2700 Q=Q+8+2*Z:O=O+8+2*Z:R=R+1
2705 IF B=0 THEN RETURN
2710 FOR I=0 TO 7:G(I)=2^I+2^(7-I):NEXT
2720 G=96+16*X:K=280+56*Y:GOSUB 50
2730 GLYPH G(0),8,8,4:B=K+56:C=G
2740 GOTO 6310
2800 IF P=0 THEN SOUND 120,35:GOTO 2120
2810 P=P-1:H=H+18:IF H>24+6*L THEN H=24+6*L
2820 SOUND 660,50:A=0:GOTO 2200
3000 LCDCHAR 1,14,10,4,27,4,10,17,0
3010 FOR I=0 TO 6:G(I)=ASC(MID$(B$,7*T+I+1,1))-64:NEXT
3030 LCDCHAR 32,G(0),G(1),G(2),G(3),G(4),G(5),G(6),0
3040 RETURN
3100 LOCATE 1,3:PRINT RIGHT$("   "+STR$(H),3);
3110 LOCATE 1,28:PRINT RIGHT$("   "+STR$(U),3);:RETURN
3300 LCDLINE 8+4*J,0:GOSUB 3100
3310 LOCATE 1,7:PRINT"                    ";
3320 LOCATE 1,8:PRINT"-";O;:LOCATE 1,22:PRINT"-";A;
3330 SOUND 300,40:SOUND 0,800:RETURN
6000 LPRINT"CANON S-70 QUEST - DEPART 6,14":B=56
6010 RESTORE:FOR X=0 TO 15:READ M$:NEXT
6020 J=0:FOR Y=1 TO 3:READ M$
6022 FOR X=1 TO 40 STEP 2
6024 G=ASC(MID$(M$,X,1)):IF G=33 THEN G=6
6026 G=(240-G)AND 255
6028 A=ASC(MID$(M$,X+1,1)):IF A=33 THEN A=6
6029 G(J)=256*G+((240-A)AND 255):J=J+1:NEXT:NEXT
6030 RESTORE:G=96:K=84:GOSUB 50
6090 LPRINT"         111111111122222222223";:C=576
6100 G=96:K=168:GOSUB 50
6110 LPRINT"123456789012345678901234567890";:C=576
6120 FOR Y=0 TO 15:READ M$
6130 CLS:PRINT"IMPRESSION CARTE ";Y+1;"/16";
6140 G=40*(Y MOD 2):K=280+56*Y:GOSUB 50
6150 LPRINT RIGHT$(" "+STR$(Y+1),2);:C=G+32
6160 FOR X=0 TO 14
6165 A=ASC(MID$(M$,X+1,1))-35
6170 G(64+2*X)=INT(A*.06667):G(65+2*X)=A MOD 15
6180 NEXT:G=96:K=280+56*Y:GOSUB 50
6280 GLYPH G(0),30,8,5:B=K+56:C=G
6290 NEXT
6310 G=0:K=@VIEWY@:GOTO 50
8400 A$="Flèches:cap ENT:pas RET:bilan":GOTO 150
8500 J=0
8510 CLS:IF J=1 THEN 8540
8520 IF J=2 THEN 8550
8530 PRINT"1/3 @COIN@";F;" POT";P;" PV";H;"/";24+6*L;
8531 GOTO 8560
8540 PRINT"2/3 NV";L;" XP";E;"/";6+4*L;
8541 PRINT" ATK";4+L+S;" DEF";L+W;:GOTO 8560
8550 PRINT"3/3 Épée +";S;" Armure +";W;
8560 GOSUB 100:IF K=8 OR K=13 THEN RETURN
8570 IF K=18 THEN J=(J+2)MOD 3:GOTO 8510
8580 IF K=19 THEN J=(J+1)MOD 3:GOTO 8510
8590 GOTO 8560
9500 CLS:PRINT"Aventure terminée";
9510 SOUND 120,180:END
9600 CLS:PRINT"Victoire ! Royaume sauvé !";
9610 SOUND 440,70:SOUND 550,70:SOUND 660,160:END
'''

TRANSLATE={
    'CARTE: ENT imprimer RET passer':'MAP: ENT print BS skip',
    ' ATK DEF POT FUIR    ':' ATK DEF POT FLEE    ',
    'CANON S-70 QUEST - DEPART 6,14':'CANON S-70 QUEST - START 6,14',
    'IMPRESSION CARTE':'PRINTING MAP','IMPRESSION CARTE ':'PRINTING MAP ',
    ' PV':' HP',' NV':' LV','NV':'LV','2/3 NV':'2/3 LV',
    'Cimet.Forêt RuinesOasis Tour  ':'Grave ForestRuins Oasis Tower ',
    'Flèches:cap ENT:pas RET:bilan':'Arrows: turn ENT: step BS: stats',
    'Trouvez le sorcier !':'Find the sorcerer!',
    'Gardien précédent requis':'Defeat the previous guardian',
    'Niveau requis: ':'Level required: ','Repos':'Rest','Potion':'Potion',
    '1 Repos 2 Potion 3 Épée 4 Armure':'1 Rest 2 Potion 3 Sword 4 Armor',
    ' ENT:OUI RET:NON':' ENT:YES BS:NO',
    'Épée +':'Sword +','Armure +':'Armor +','Épée +2 MAX':'Sword +2 MAX',
    'Armure +2 MAX':'Armor +2 MAX','FANTôME':'GHOST',
    'ARAIGNÉE':'SPIDER','SQUELETTE':'SKELETON','DÉMON':'DEMON','SORCIER':'SORCERER',
    'GARDIEN: ':'GUARDIAN: ','ATK DEF POT FUIR':'ATK DEF POT FLEE',
    'Victoire! +':'Victory! +',
    'Niveau ':'Level ','PV':'HP','N':'L',
    ' Armure +':' Armor +',' Potions ':' Potions ','3/3 Épée +':'3/3 Sword +',
    'DÉPART 6,14 - ESPACE: AIDE':'START 6,14 - SPACE: HELP',
    'Aventure terminée':'Adventure over',
    'Victoire ! Royaume sauvé !':'Sorcerer defeated! Realm saved!',
}

def main():
    assets=json.loads(Path(__file__).with_name('s70-quest-assets.json').read_text())
    glyphs=assets['tiles'][:]
    for i in (0,1):
        rows=bytearray.fromhex(glyphs[i]);rows[0]|=0x55
        for y in (2,4,6):rows[y]|=1
        glyphs[i]=rows.hex().upper()
    from native_text import LCD_TO_UNICODE
    packed=[]
    for row in assets['map']:
        values=[35+15*(ord(row[i])-65)+ord(row[i+1])-65 for i in range(0,30,2)]
        assert all(35<=v<=255 and v!=127 for v in values),values
        packed.append(''.join(chr(v) if v<127 else LCD_TO_UNICODE.get(v,chr(0xe000+v)) for v in values))
    raw=bytes(b for tile in glyphs for b in bytes.fromhex(tile))
    encoded=[(240-b)&255 for b in raw]
    assert {v for v in encoded if v<32 or v in (34,127)}=={6}
    assert 33 not in encoded
    encoded=[33 if v==6 else v for v in encoded]
    assert bytes((240-(6 if v==33 else v))&255 for v in encoded)==raw
    def native(values):
        return ''.join(chr(v) if v<127 else LCD_TO_UNICODE.get(v,chr(0xe000+v)) for v in values)
    coin=native([164])
    # Native arrows: north=169, east=200, south=170, west=201.
    arrows=' '.join(native([v]) for v in (169,170,201,200))
    atlas=[native(encoded[i:i+40]) for i in (0,40,80)]
    fields=['"'+v+'"' for v in packed+atlas];data=[]
    for field in fields:
        if not data or len(str(2+len(data)))+7+len(data[-1])+len(field)>63:data.append(field)
        else:data[-1]+=','+field
    sprites=json.loads((ROOT/'examples/graphics/s70-quest-sprites.json').read_text(encoding='utf-8'))['sprites']
    lcd=''.join(chr(64+int(row,2)) for sprite in sprites[1:] for row in sprite['rows'])
    assert len(lcd)==49 and all(64<=ord(c)<=95 for c in lcd)
    hero=','.join(str(int(row,2)) for row in sprites[0]['rows'])
    body=BODY.replace('@VIEWY@',str(PAPER_VIEW_Y)).replace('@COIN@',coin).replace('@ARROWS@',arrows)
    # Both startup paths join here: printing must initialize the same sprite
    # atlas as map reuse, after CLEAR has released the temporary paper array.
    body=body.replace('930 X=',f'927 B$="{lcd}"\n930 X=')
    body=body.replace('LCDCHAR 1,14,10,4,27,4,10,17,0','LCDCHAR 1,'+hero+',0')
    source='1 GOTO 910\n'+''.join(f'{2+i} DATA '+v+'\n' for i,v in enumerate(data))+body
    # Shorten punctuation spacing only when tokenization is identical.
    def normalized(body):
        quote=False;out=bytearray()
        for b in codec.tokenize(body):
            if b==34:quote=not quote
            if b!=32 or quote:out.append(b)
        return bytes(out)
    records=[]
    for raw in source.splitlines():
        number,body=raw.split(' ',1)
        i=0;quote=False
        while i<len(body):
            if body[i]=='"':quote=not quote
            if (body[i]==' ' and not quote and i and i+1<len(body)
                    and not ((body[i-1].isalnum() or body[i-1]=='$') and (body[i+1].isalnum() or body[i+1]=='$'))):
                trial=body[:i]+body[i+1:]
                if normalized(body)==normalized(trial):body=trial;continue
            i+=1
        records.append((int(number),body))
    targets={int(v) for n,body in records for v in re.findall(r'(?:GOTO|GOSUB|THEN|ELSE)\s+(\d+)',body)}
    targets.update(range(2020,2081,10));targets.add(950)
    joined=[]
    for n,body in records:
        if joined and n not in targets and not body.startswith(('DATA','REM')):
            previous=joined[-1][1];code=re.sub(r'"[^"]*"','""',previous)
            if not re.search(r'\b(IF|GOTO|RETURN|END|REM)\b',code) and len(str(joined[-1][0]))+2+len(previous)+len(body)<=63:
                joined[-1]=(joined[-1][0],previous+':'+body);continue
        joined.append((n,body))
    lines={n:i+1 for i,(n,body) in enumerate(joined)}
    rebound=[]
    for n,body in joined:
        parts=re.split(r'("[^"]*")',body)
        for i in range(0,len(parts),2):
            parts[i]=re.sub(r'(GOTO|GOSUB|THEN|ELSE)(\s+)(\d+)',lambda m:m[1]+m[2]+str(lines[int(m[3])]),parts[i])
            for original in (2020,):parts[i]=parts[i].replace('GOSUB '+str(lines[original])+'+10*','GOSUB '+str(lines[original])+'+')
        rebound.append((lines[n],''.join(parts)))
    (ROOT/'build/s70-quest-lines.json').write_text(json.dumps(lines,indent=2)+'\n')
    source=''.join(f'{n} {body}\n' for n,body in rebound)
    for lang in ('fr','en'):
        translations=TRANSLATE|{' PRIX '+coin:' PRICE '+coin}
        text=source if lang=='fr' else re.sub(r'"([^"]*)"',lambda m:'"'+translations.get(m[1],m[1])+'"',source)
        a=analyze(text);print(lang,a.used,a.free,a.issues,flush=True)
        assert not a.issues,a.issues
        assert a.free>=960,(lang,a.free)
        assert codec.unpack(codec.pack(a.records))==a.records
        (ROOT/f'examples/games/canon-s70-quest-{lang}.bas').write_text(text,encoding='utf-8')

if __name__=='__main__':main()
