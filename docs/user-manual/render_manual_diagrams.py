"""Original functional and timeline diagrams for the French manual."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap
import json

HERE=Path(__file__).resolve().parent
RUST='#905733'; INK='#24211d'; PALE='#f6eee4'
OUTPUT=HERE/'images'
TRANSLATIONS={}
def font(size,bold=False):
    return ImageFont.truetype(str(HERE/'fonts'/('Lato-Bold.ttf' if bold else 'Lato-Regular.ttf')),size)
def centered(draw,text,box,size=40,bold=False):
    text=TRANSLATIONS.get(text,text)
    if TRANSLATIONS and text.startswith('vers '):text='c. '+text[5:]
    x0,y0,x1,y1=box; f=font(size,bold)
    lines=text.split('\n')
    while max(draw.textlength(line,font=f) for line in lines)>x1-x0-24:
        size-=1;f=font(size,bold)
    step=size*1.25
    y=(y0+y1-step*len(lines))/2
    for line in lines:
        width=draw.textlength(line,font=f)
        draw.text(((x0+x1-width)/2,y),line,font=f,fill=INK)
        y+=step
def arrow(d,points,both=False):
    d.line(points,fill=RUST,width=5)
    def tip(a,b):
        dx=b[0]-a[0];dy=b[1]-a[1];length=(dx*dx+dy*dy)**.5
        if not length:return
        ux,uy=dx/length,dy/length
        d.polygon([b,(b[0]-20*ux+10*uy,b[1]-20*uy-10*ux),
                   (b[0]-20*ux-10*uy,b[1]-20*uy+10*ux)],fill=RUST)
    tip(points[-2],points[-1])
    if both:tip(points[1],points[0])
def functional():
    im=Image.new('RGB',(2200,1400),'white');d=ImageDraw.Draw(im)
    boxes=[((35,100,520,300),'ROM IC8\nTypestar BASIC\n32 Ko'),
           ((35,360,520,540),'RAM de la machine\n8 Ko'),
           ((720,220,1380,830),'HD6301Y0P'),
           ((1660,240,2165,450),'IC5 - MB62H177\nLogique Canon / LCD'),
           ((1660,35,2165,155),'Clavier'),
           ((1540,625,1835,820),'LCD\n32 caractères'),
           ((1890,625,2165,820),'Buzzer'),
           ((690,1060,1270,1340),'Pilotes d’impression\nTête thermique\nMoteur de tête\nMoteur de papier'),
           ((1510,1100,2165,1340),'Buffer, prise DE-9\nCâble USB adapté\nSignaux TTL 5 V'),
           ((35,610,520,800),'IC7 - 128ROM\nROM haute externe\n16 Ko, en mode EXT'),
           ((35,1030,550,1300),'Connecteur CN9\nCartouches Typestyle\nou mémoire RAM\nBus d’adresses / données')]
    for box,text in boxes:
        d.rounded_rectangle(box,radius=12,fill=PALE,outline=RUST,width=4)
        if box!=boxes[2][0]:centered(d,text,box,size=42)
    centered(d,'HD6301Y0P\nProcesseur 8 bits\nMaskROM Canon : 16 Ko\nRAM interne : 256 octets', (740,240,1360,535),43,True)
    d.rounded_rectangle((755,565,1345,775),radius=9,outline=RUST,width=3,fill='white')
    centered(d,'Interface série intégrée\nSCI / UART\nRXD : P23 / TXD : P24',(755,565,1345,775),40)
    arrow(d,[(520,200),(620,200),(620,345),(720,345)],True)
    arrow(d,[(520,450),(720,450)],True)
    arrow(d,[(520,705),(635,705),(635,520),(720,520)])
    arrow(d,[(550,1160),(605,1160),(605,565),(720,565)],True)
    arrow(d,[(1380,345),(1660,345)],True)
    arrow(d,[(1910,155),(1910,240)])
    arrow(d,[(1910,450),(1910,535),(1685,535),(1685,625)])
    arrow(d,[(1910,535),(2025,535),(2025,625)])
    arrow(d,[(980,830),(980,1060)])
    arrow(d,[(1345,690),(1440,690),(1440,1210),(1510,1210)],True)
    centered(d,'Cartouches : polices et mémoire de texte Canon ; extension RAM BASIC envisagée.',(35,1345,2165,1400),30)
    im.save(OUTPUT/'schema-fonctionnel-s70.png')
def timeline():
    """Documentary dates and explicitly qualified estimates, in chronological panels."""
    early=[
        [('1980','CanoWord 55\nLancement Canon','canoword55'),
         ('1982','AP400 / AP500\nLancements Canon','ap400'),
         ('1983','Canon X-07\nCanoWord Mini 5','canon-x07'),
         ('1984','Typestar 5\nPrix de design','typestar5')],
        [('1985','Typestar 6 : prix de design\nTypestar 7 : documentée\nVue de la Typestar 7','typestar7'),
         ('1985','Typemate 10 / S-10\nDocumentée en octobre','typemate-10'),
         ('1986','S-70 en France\n2 990 F dans Tilt\nAnnonce de mai','typestar7'),
         ('vers 1986','Typestar 4\nLettre du manuel :\n17 février 1986','typestar-4')]]
    later=[
        [('1987','Typestar 6-II / S-61\nDocumentée en février','typestar-6-ii'),
         ('vers 1987','Typestar 90 / S-90\nDatation de musée\nAnnonce en mars 1988','typestar90'),
         ('1988','Typestar 5-II\nAnnonce de mars','typestar-5-ii'),
         ('1989','Typestar 3\nManuel © 1989','typestar-3')],
        [('1990','Typestar 110-II / 210\nManuel commun © 1990\nVue de la Typestar 210','typestar210'),
         ('vers 1990–91','Typestar 2\nEstimation provisoire\nAnnonce en novembre 1991','typestar-2'),
         ('1992','Typestar 10\nManuel © 1992','typestar10')]]
    recent=[[('1992','Typestar 220\nManuel © 1992','typestar-220'),
             ('vers 1994','Typestar 10-II\nLettre du manuel :\n3 juin 1994','typestar-10-ii'),
             ('vers 1994','Typestar 220-II\nExemplaire daté\npar son propriétaire','typestar-220-ii')]]
    for filename,groups,dated in [('frise-typestar.png',early,True),
                                  ('frise-typestar-suite.png',later,True),
                                  ('frise-typestar-annees1990.png',recent,True)]:
        im=Image.new('RGBA',(2000,630*len(groups)),(0,0,0,0));d=ImageDraw.Draw(im)
        for row,events in enumerate(groups):
            y=40+row*630;spacing=1850/len(events)
            if dated:arrow(d,[(65,y+80),(1940,y+80)])
            for i,(date,label,name) in enumerate(events):
                x=80+spacing*(i+.5)
                if dated:d.ellipse((x-10,y+70,x+10,y+90),fill=RUST)
                centered(d,date,(x-spacing/2+20,y-20,x+spacing/2-20,y+60),54,True)
                box=(x-spacing/2+20,y+130,x+spacing/2-20,y+550)
                d.rounded_rectangle(box,radius=9,fill=PALE,outline=RUST,width=3)
                path=HERE/'images/history/illustrations'/f'{name}-transparent.png'
                image=Image.open(path).convert('RGBA')
                # Crop the layout to the visible object, without editing the source asset.
                bbox=image.getchannel('A').point(lambda v:255 if v>32 else 0).getbbox()
                if bbox:image=image.crop(bbox)
                image.thumbnail((int(spacing-90),220),Image.Resampling.LANCZOS)
                im.alpha_composite(image,(int(x-image.width/2),int(y+145+(220-image.height)/2)))
                centered(d,label,(box[0],y+365,box[2],box[3]-7),42)
        im.save(OUTPUT/filename)

def interpreter():
    im=Image.new('RGB',(2000,760),'white');d=ImageDraw.Draw(im)
    boxes=[((25,35,505,220),'Votre ligne BASIC\nPRINT 1.5+2.25'),
           ((760,35,1240,220),'Analyse de l’instruction\nTokens et expressions'),
           ((1495,35,1975,220),'Calcul décimal\nAdaptateur + maskROM'),
           ((270,505,770,705),'LCD / clavier\nDialogue avec le programme'),
           ((1250,505,1780,705),'Papier / son / série\nServices et pilotes')]
    for b,t in boxes:
        d.rounded_rectangle(b,12,fill=PALE,outline=RUST,width=4);centered(d,t,b,40)
    arrow(d,[(505,128),(760,128)]);arrow(d,[(1240,128),(1495,128)])
    arrow(d,[(1740,220),(1740,390),(520,390),(520,505)])
    arrow(d,[(1515,390),(1515,505)])
    centered(d,'Le BASIC prépare les commandes destinées aux périphériques.',(450,265,1660,325),35)
    im.save(OUTPUT/'schema-interpreteur.png')

def character_catalogues():
    rows=json.loads((HERE.parents[1]/'studio/internal/assets/lcd-font.json').read_text(encoding='utf8'))['rows']
    for start,name in [(0,'00-7f'),(128,'80-ff')]:
        im=Image.new('RGB',(1920,1440),'white');d=ImageDraw.Draw(im)
        for code in range(start,start+128):
            n=code-start;x=n%16*120;y=n//16*180
            d.rectangle((x+2,y+2,x+116,y+176),outline='#d6c8b8',width=2)
            d.rectangle((x+25,y+17,x+95,y+115),fill='#e1e6d0')
            data=rows.get(f'{code:02X}',[0]*7)
            for yy,value in enumerate(data[:7]):
                for xx in range(5):
                    if value&(16>>xx):d.rectangle((x+25+xx*14,y+17+yy*14,x+36+xx*14,y+28+yy*14),fill='#34443a')
            centered(d,f'{code}\n${code:02X}',(x+3,y+117,x+116,y+175),25)
        im.save(OUTPUT/f'lcd-catalogue-{name}.png')
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--language',choices=['fr','en'],default='fr')
    args=parser.parse_args()
    if args.language=='en':
        TRANSLATIONS=json.loads((HERE/'en/diagram-labels.json').read_text(encoding='utf8'))
        OUTPUT=HERE/'en/images'
    OUTPUT.mkdir(exist_ok=True)
    functional();timeline();interpreter();character_catalogues()
