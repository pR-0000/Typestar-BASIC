from i18n import tr
"""Static glyph import, deliberately not a BASIC evaluator."""
import re

def number(text):
    text=text.strip().upper()
    if re.fullmatch(r'%[01]+',text):return int(text[1:],2)
    if re.fullmatch(r'&H[0-9A-F]+',text):return int(text[2:],16)
    if re.fullmatch(r'[0-9]+',text):return int(text)
    raise ValueError(tr('Valeur constante attendue (décimal, %binaire ou &Hhexadécimal).'))

def import_glyphs(source):
    assets=[];arrays={}
    for raw in source.splitlines():
        body=re.sub(r'^\s*\d+\s+','',raw).strip()
        # Quotes protect colons in PRINT strings; their contents are never evaluated.
        for part in re.split(r':(?=(?:[^"\n]*"[^"\n]*")*[^"\n]*$)',body):
            part=part.strip().upper()
            if part.startswith('REM'):break
            if part.startswith('LCDCHAR '):
                values=[number(v) for v in part[8:].split(',')]
                if len(values)!=9 or not 1<=values[0]<=32 or any(v>31 for v in values[1:]):
                    raise ValueError(tr('LCDCHAR attendu : position, sept rangées, triangle (0..31).'))
                assets.append(dict(kind='LCD',position=values[0],triangle=values[8],lower=0,
                    pixels=[[(v>>(4-x))&1 for x in range(5)] for v in values[1:8]]))
            elif part.startswith('LCDLINE '):
                pos,value=map(number,part[8:].split(','))
                if value>31:raise ValueError(tr('LCDLINE : masque 0..31 attendu.'))
                for asset in reversed(assets):
                    if asset['kind']=='LCD' and asset['position']==pos:asset['lower']=value;break
            elif match:=re.fullmatch(r'DIM ([A-Z])\(([^)]+)\)',part):
                dims=[number(v)+1 for v in match[2].split(',')]
                if len(dims) not in (1,2) or dims[0]>16 or (len(dims)==2 and dims[1]>31):
                    raise ValueError(tr('DIM de glyphe : au plus 16 rangées et 31 colonnes.'))
                arrays[match[1]]=(dims,{})
            elif match:=re.fullmatch(r'(?:LET )?([A-Z])\(([^)]+)\)\s*=\s*(.+)',part):
                name=match[1]
                if name not in arrays:raise ValueError(tr('DIM constant requis avant les pixels.'))
                indices=tuple(number(v) for v in match[2].split(','));dims,data=arrays[name]
                if len(indices)!=len(dims) or any(i>=d for i,d in zip(indices,dims)):raise ValueError(tr('Indice hors matrice.'))
                data[indices]=number(match[3])
            elif part.startswith('GLYPH '):
                match=re.fullmatch(r'GLYPH ([A-Z])\((0(?:,0)?)\),([^,]+),([^,]+),([^,]+)',part)
                if not match or match[1] not in arrays:raise ValueError(tr('GLYPH constant attendu après DIM et affectations ; sélectionner le bloc complet.'))
                w,h,zoom=map(number,(match[3],match[4],match[5]));dims,data=arrays[match[1]]
                if not 1<=w<=31 or not 1<=h<=16 or zoom not in (1,2,3) or dims[0]<h:raise ValueError(tr('Dimensions GLYPH invalides.'))
                if len(dims)==1:
                    if w>16 or match[2]!='0' or any(v>=1<<w for v in data.values()):raise ValueError(tr('Rangées hors largeur GLYPH.'))
                    pixels=[[(data.get((y,),0)>>(w-1-x))&1 for x in range(w)] for y in range(h)]
                else:
                    if match[2]!='0,0' or dims[1]<w or any(v not in (0,1) for v in data.values()):raise ValueError(tr('Matrice de pixels 0/1 attendue.'))
                    pixels=[[data.get((y,x),0) for x in range(w)] for y in range(h)]
                assets.append(dict(kind='Papier',pixels=pixels,zoom=zoom,array=match[1]))
            elif part and not part.startswith(('PRINT ','CLS','CURSOR ','LOCATE ')):
                # Do not pretend a dynamic/control-flow program was evaluated.
                raise ValueError(tr('Sélectionner uniquement un bloc de glyphe constant. Instruction non prise en charge : ')+part[:45])
    if not assets:raise ValueError(tr('Aucun LCDCHAR ou GLYPH constant trouvé.'))
    return assets
