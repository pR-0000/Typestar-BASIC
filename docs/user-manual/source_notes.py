"""Place source references on the page containing their inline callout.

Paragraph onDraw callbacks locate the actual line, including split paragraphs
and split tables. Subsequent pagination passes reserve the measured note area.
"""
import html
import re
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

class SourceNotes:
    def __init__(self, config):
        self.config=config
        self.entries={}
        self.numbers={}
        self.style=ParagraphStyle('source-note',fontName='Body',fontSize=8.1,
                                  leading=10.3,textColor=colors.HexColor('#69635d'))

    def marker(self, label, url='', source=''):
        definition=self.config.get('citation_labels',{}).get(label)
        if definition:
            label=definition['label'];url=definition.get('url','')
        else:
            definition=self.config.get('citation_urls',{}).get(url)
            if definition:label=definition
        key=(label,url)
        if key not in self.numbers:
            number=len(self.numbers)+1
            self.numbers[key]=number
            self.entries[number]={'label':label,'url':url,'source':source}
        n=self.numbers[key]
        return f'<super><font size="7" color="#905733">{n}</font></super><onDraw name="manual_note" label="{n}"/>'

    def paragraphs(self, numbers):
        result=[]
        for n in sorted(numbers):
            entry=self.entries[n];label=html.escape(entry['label'])
            url=entry['url']
            if re.match(r'https?://',url):
                label=f'<link href="{html.escape(url,quote=True)}" color="#69635d">{label}</link>'
            result.append(Paragraph(f'<b>{n}.</b> {label}',self.style))
        return result

    def height(self, numbers, width):
        return 11+sum(p.wrap(width,1000)[1]+2 for p in self.paragraphs(numbers)) if numbers else 0

    def draw(self, canvas, numbers, left, bottom, width):
        if not numbers:return
        canvas.saveState()
        height=self.height(numbers,width)
        y=bottom+height-4
        canvas.setStrokeColor(colors.HexColor('#bca38c'));canvas.setLineWidth(.4)
        canvas.line(left,y,left+width*.4,y);y-=7
        for p in self.paragraphs(numbers):
            _,h=p.wrap(width,1000);y-=h;p.drawOn(canvas,left,y);y-=2
        canvas.restoreState()
