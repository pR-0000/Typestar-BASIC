"""Raster of actual decoded head columns at native motor positions.
X: one phase/column. Y: seven paper phases per head row, two X pitches/row.
Geometry follows the firmware's validated 31x16 / 56-unit band convention.
A 2x2 mark approximates the thermal footprint and joins adjacent 31-column bands.
This models marks, not ribbon chemistry, mechanics or physical page sensing.
"""
from PIL import Image, ImageDraw
# Native lanes $66/$67/$68, low bit first. Graphics use rows 4..19.
# Keep their calibrated origin unchanged; extra font rows extend above/below.
ROW_BITS=tuple(range(24))

class PaperRaster:
    WIDTH=2560
    MAX_HEIGHT=12000
    MARGIN=128
    def __init__(self):self.clear()
    def clear(self):
        self.image=Image.new('1',(self.WIDTH,512),1)
        self.bottom=0;self.columns=0;self.clipped=0
    def add(self,events):
        for x,phase_y,word in events:
            if not word:continue
            x+=self.MARGIN
            y=round(phase_y*2/7)+self.MARGIN-8
            if x<0 or x+1>=self.WIDTH or y<0 or y+48>self.MAX_HEIGHT:
                self.clipped+=1;continue
            if y+48>self.image.height:
                grown=Image.new('1',(self.WIDTH,min(self.MAX_HEIGHT,((y+48+511)//512)*512)),1)
                grown.paste(self.image,(0,0));self.image=grown
            draw=ImageDraw.Draw(self.image)
            for row,bit in enumerate(ROW_BITS):
                if word&(1<<bit):
                    draw.rectangle((x,y+2*row,x+1,y+2*row+1),fill=0)
                    self.bottom=max(self.bottom,y+2*row+2)
            self.columns+=1
    def output(self):
        return self.image.crop((0,0,self.WIDTH,min(self.image.height,max(512,self.bottom+64))))
