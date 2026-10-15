"""Draw the validated USB-TTL wiring as a bilingual, editable diagram."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
def render(language):
    en=language=='en';out=HERE/('en/images' if en else 'images');out.mkdir(exist_ok=True)
    im=Image.new('RGB',(2000,1050),'white');d=ImageDraw.Draw(im)
    ink='#24211d';rust='#905733';pale='#f6eee4'
    def font(n,bold=False):return ImageFont.truetype(str(HERE/'fonts'/('Lato-Bold.ttf' if bold else 'Lato-Regular.ttf')),n)
    d.rounded_rectangle((35,30,865,900),18,fill=pale,outline=rust,width=4)
    d.rounded_rectangle((1185,30,1965,700),18,fill=pale,outline=rust,width=4)
    d.text((450,60),'CANON CN7 / DE-9',font=font(45,True),fill=ink,anchor='mt')
    d.text((1575,60),'USB / FT232RL - TTL 5 V',font=font(42,True),fill=ink,anchor='mt')
    left=[('1  GND',210),('2  TXD / P24',325),('3  RXD / P23',440),('4  RTS# / P21',555)]
    right=[('GND',210),('RXD',325),('TXD',440),('CTS#',555)]
    for (a,y),(b,_) in zip(left,right):
        d.text((75,y),a,font=font(40),fill=ink,anchor='lm');d.text((1325,y),b,font=font(40),fill=ink,anchor='lm')
        x0,x1=810,1245;d.line((x0,y,x1,y),fill=rust,width=5)
        if a.startswith('3 '):d.polygon([(x0,y),(x0+20,y-12),(x0+20,y+12)],fill=rust)
        elif not a.startswith('1 '):d.polygon([(x1,y),(x1-20,y-12),(x1-20,y+12)],fill=rust)
    for text,y in [('5  IF_ENABLE# / P22',710),('6  IF_PRESENT# / P26',825)]:
        d.text((75,y),text,font=font(36),fill=ink,anchor='lm')
        d.line((660,y,900,y),fill=rust,width=4)
        d.rectangle((900,y-19,1040,y+19),fill='white',outline=rust,width=4)
        d.text((970,y-54),'2.2 kΩ' if en else '2,2 kΩ',font=font(31),fill=ink,anchor='mt')
        d.line((1040,y,1100,y,1100,y+30),fill=rust,width=4)
        for i,w in enumerate([38,25,12]):d.line((1100-w,y+30+9*i,1100+w,y+30+9*i),fill=rust,width=4)
    d.text((1575,640),'CTS# = Canon RTS#',font=font(33),fill=ink,anchor='mt')
    notes=('Canon 7 / 8 / 9: insulated   |   FTDI VCC / RTS#: insulated' if en else 'Canon 7 / 8 / 9 : isolés   |   FTDI VCC / RTS# : isolés')
    d.text((1000,940),notes,font=font(35),fill=ink,anchor='mt')
    d.text((1000,995),'Numbers refer to Canon connector contacts.' if en else 'Les numéros désignent les contacts du connecteur Canon.',font=font(30),fill=ink,anchor='mt')
    im.save(out/'cable-usb-ttl.png')
if __name__=='__main__':
    for language in ['fr','en']:render(language)
