"""Export the actual Quest LCD sprites as editable rows, BASIC and a pixel sheet."""
from pathlib import Path
import json
import unicodedata
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'examples/graphics'
ASSET=DEST/'s70-quest-sprites.json'


def main():
    DEST.mkdir(exist_ok=True)
    if not ASSET.exists():
        old=json.loads(Path(__file__).with_name('s70-quest-assets.json').read_text())
        names=[('Joueur','Player'),('Slime','Slime'),('Fantôme','Ghost'),
               ('Araignée','Spider'),('Bandit','Bandit'),('Squelette','Skeleton'),
               ('Démon','Demon'),('Sorcier','Sorcerer')]
        values=[[14,10,4,27,4,10,17]]+[[ord(c)-64 for c in rows] for rows in old['lcd']]
        ASSET.write_text(json.dumps(dict(width=5,height=7,sprites=[
            dict(name_fr=fr,name_en=en,rows=[f'{v:05b}' for v in data])
            for (fr,en),data in zip(names,values)]),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    data=json.loads(ASSET.read_text(encoding='utf-8'))
    sprites=data['sprites']
    assert len(sprites)==8
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',17)
    image=Image.new('RGB',(880,520),'white');draw=ImageDraw.Draw(image)
    draw.text((20,12),'CANON S-70 QUEST — LCD 5 × 7',font=font,fill='black')
    for t,s in enumerate(sprites):
        assert len(s['rows'])==7 and all(len(r)==5 and set(r)<=set('01') for r in s['rows'])
        x=40+220*(t%4);y=72+225*(t//4)
        draw.text((x-20,y-25),s['name_fr']+' / '+s['name_en'],font=font,fill='black')
        for v,row in enumerate(s['rows']):
            for u,bit in enumerate(row):
                draw.rectangle((x+23*u,y+23*v,x+23*u+22,y+23*v+22),fill='black' if bit=='1' else '#f2f2f2',outline='#b8b8b8')
    image.save(DEST/'s70-quest-sprites.png')
    for lang in ('fr','en'):
        rows=['10 REM S-70 QUEST - LCD 5X7','20 CLS:DIM G(6)',
              '30 FOR T=0 TO 7:FOR I=0 TO 6:READ G(I):NEXT I',
              '40 LCDCHAR 2+4*T,G(0),G(1),G(2),G(3),G(4),G(5),G(6),0',
              '50 NEXT T','60 IF INKEY(0)=0 THEN 60','70 END']
        for t,s in enumerate(sprites):
            n=100+100*t
            label=unicodedata.normalize('NFKD',s['name_'+lang]).encode('ascii','ignore').decode().upper()
            rows.append(f'{n} REM '+label)
            rows.extend(f'{n+10+10*i} DATA %{row}' for i,row in enumerate(s['rows']))
        (DEST/f's70-quest-sprites-{lang}.bas').write_text('\n'.join(rows)+'\n',encoding='utf-8')


if __name__=='__main__':main()
