"""S-70 glass rendering, in integer DEVICE pixels (including fractional DPI).

Native bitmaps and measured S-70 glass geometry: Pierre Raimbault.
Five marker positions remain provisional; see the LCD rendering documentation.
"""
from PySide6.QtCore import QRect, QPoint
from PySide6.QtGui import QImage, QPainter, QColor, QPolygon

INK=QColor('#34443a')
GHOST=QColor('#a5af97')
# index, native selector, label, center in character-cell coordinates
INDICATORS=[(0,178,'1',.48),(1,178,'1½',1.45),(2,178,'2',2.42),
 (3,211,'dot',3.55),(4,178,'dash',4.35),
 (5,47,'XX',5.6),(7,178,'XX_',6.8),(8,211,'wide',8),(9,211,'wide_',9.2),
 (11,215,'return',11),(12,215,'auto',12.2),(13,215,'justify',13.4),
 (15,178,'A',15.15),(16,178,'B',16.15),(30,215,'I',30.5),(31,211,'II',31.5),
 # Provisional glass positions; selectors follow maskROM EF07..EF1E.
 (17,178,'CODE',18.6),(20,178,'tab',20.6),(23,215,'align',23.5),
 (26,178,'decimal',26.5),(29,178,'paper',28.8)]
# Tiny glass legends, independent of host fonts (also headless Linux/Qt).
LEGENDS={
 '1':[2,6,2,2,7], '2':[6,1,2,4,7], '½':[16,20,2,5,7],
 'X':[5,5,2,5,5], 'A':[2,5,7,5,5], 'B':[6,5,6,5,6],
 'C':[3,4,4,4,3], 'O':[2,5,5,5,2], 'D':[6,5,5,5,6],
 'E':[7,4,6,4,7], 'I':[7,2,2,2,7],
 'L':[4,4,4,4,7], 'U':[5,5,5,5,7], 'T':[7,2,2,2,2],
 'J':[1,1,1,5,2], 'S':[3,4,2,1,6]}
GROUPS=[(0,2.9),(3.1,4.8),(5,10),(10.3,14.25),(14.55,16.7),(17,29.75),(30,32)]

def geometry(width,height):
    pitch=max(1,min(width//200,height//21))
    return pitch,(width-200*pitch)//2,(height-21*pitch)//2

def triangle_segments(x,bottom,pitch):
    # bit4 is the leftmost, shortest segment; bit0 the rightmost, tallest.
    # All bars share one baseline, unlike the old top-aligned drawing.
    return [QRect(x+i*pitch,bottom-max(1,(i+1)*pitch//3),
                  max(1,pitch-1),max(1,(i+1)*pitch//3)) for i in range(5)]

def rows_for(code,cgram,native):
    if code<16:return cgram[(code&7)*8:(code&7)*8+8]
    if code<32:return [0]*8
    return native.get(code,[0]*7)+[0]

def active_indicators(lower):
    # This models known whole-symbol Canon selections, not an unmeasured
    # pixel-by-pixel wiring of every lower-bank CGRAM bit to each icon.
    return {index for index,code,_,_ in INDICATORS if lower[index]==code}

def render_glass(width,height,state,native,spaced=True,blink=True):
    im=QImage(width,height,QImage.Format.Format_RGB32);im.fill(QColor('#d5d4c8'))
    p=QPainter(im);p.setRenderHint(QPainter.RenderHint.Antialiasing,False)
    q,ox,oy=geometry(width,height)
    p.fillRect(ox,oy,200*q,21*q,QColor('#74796b'))
    p.fillRect(ox+q,oy+q,198*q,19*q,QColor('#bfc9ad'))
    p.fillRect(ox+2*q,oy+2*q,196*q,17*q,QColor('#cbd4b8'))
    x0=ox+4*q;top=oy+3*q
    gap=max(1,q//8) if spaced and q>1 else 0
    control=state.get('control',12);on=bool(control&4)
    address=state.get('address',0)
    lower=state.get('lower',[32]*32);cgram=state.get('cgram',[0]*64)
    for col,code in enumerate(state.get('cells',[32]*32)):
        rows=rows_for(code,cgram,native);triangle=rows[7]&31
        cursor=on and not state.get('cgram_selected',False) and address==col
        if cursor and control&1 and blink:rows=[31]*7+[31];triangle=31
        if cursor and control&2:triangle=31
        x=x0+col*6*q
        if on:
            for y,bits in enumerate(rows[:7]):
                for bit in range(5):
                    if bits&(16>>bit):p.fillRect(x+bit*q,top+y*q,q-gap,q-gap,INK)
            for bit,rect in enumerate(triangle_segments(x,top+9*q,q)):
                if triangle&(16>>bit):p.fillRect(rect,INK)
            bits=rows_for(lower[col],cgram,native)[0]
            for bit in range(5):
                if bits&(16>>bit):p.fillRect(x+bit*q,top+10*q,q-gap,q-gap,INK)
    # The surrounding mode-window outlines are printed on the glass.
    p.setPen(QColor('#7e8c77'))
    for left,right in GROUPS:p.drawRect(QRect(x0+round(left*6*q),top+12*q,round((right-left)*6*q),3*q))
    active=active_indicators(lower) if on else set()
    def icon(label,cx,color):
        x=x0+round(cx*6*q);y=top+13*q+q//2;p.setPen(color)
        left,right=next((a,b) for a,b in GROUPS if a<=cx<=b)
        p.save()
        p.setClipRect(QRect(x0+round(left*6*q)+1,top+12*q+1,
                           round((right-left)*6*q)-2,3*q-1))

        if label=='tab':
            p.setBrush(color)
            p.drawPolygon(QPolygon([QPoint(x-q,y-q),QPoint(x+q,y-q),QPoint(x,y)]))
            p.drawLine(x-2*q,y+q//2,x+2*q,y+q//2);p.drawLine(x,y,x,y+q)
        elif label=='align':
            for n in range(5):
                yy=y-q+n*max(1,q//2)
                p.drawLine(x+q-(2*q if n<2 else q),yy,x+q,yy)
        elif label=='decimal':
            for n in range(3):p.drawLine(x-q,y-q+n*q,x+q,y-q+n*q)
            p.drawLine(x,y-q,x,y+q)
        elif label=='paper':
            p.setBrush(QColor('#cbd4b8'));p.drawRect(x-q,y,2*q,q)
            p.drawLine(x,y-q,x,y+q//2);p.drawLine(x,y-q,x-q//2,y);p.drawLine(x,y-q,x+q//2,y)
        elif label in ('dot','dash'):

            p.fillRect(x-q,y,max(1,q//2) if label=='dot' else 2*q,max(1,q//2),color)
        elif label.startswith('wide'):
            # Leave a real gap below the X; the old underline was clipped
            # against the bottom of its three-pitch frame.
            dy=max(1,round(.65*q));line_y=y+round(1.15*q)
            p.drawLine(x-2*q,y-dy,x+2*q,y+dy)
            p.drawLine(x-2*q,y+dy,x+2*q,y-dy)
            if label.endswith('_'):p.drawLine(x-2*q,line_y,x+2*q,line_y)
        elif label in ('return','auto','justify'):
            yy=y+round(.7*q)
            p.drawPolyline(QPolygon([QPoint(x+q,y),QPoint(x+q,yy),QPoint(x-q,yy)]))
            p.drawLine(x-q,yy,x-q//2,yy-q//2)
            p.drawLine(x-q,yy,x-q//2,yy+q//2)
            if label!='return':
                caption='AUT' if label=='auto' else 'JUS'
                unit=max(1,q//5);left=x-11*unit//2
                for char in caption:
                    for row,bits in enumerate(LEGENDS[char]):
                        for bit in range(3):
                            if bits&(4>>bit):p.fillRect(left+bit*unit,y-q+row*unit,unit,unit,color)
                    left+=4*unit
        else:
            text=label.rstrip('_')
            if text=='1½':
                # Dedicated mixed fraction: full-height 1, raised numerator,
                # diagonal fraction bar and lowered denominator (reference photo).
                bitmap=['......#....#.',
                        '.....##...#..',
                        '.#....#..#...',
                        '##....#.#....',
                        '.#.....#.....',
                        '.#....#..##..',
                        '.#...#.....#.',
                        '.#..#.....#..',
                        '###......###.']
            else:
                bitmap=['.'.join(''.join('#' if bits&(4>>bit) else '.' for bit in range(3))
                                 for bits in (LEGENDS[c][row] for c in text)) for row in range(5)]
                if label.endswith('_'):bitmap+=['.'*len(bitmap[0]),'#'*len(bitmap[0])]
            # Fit and centre each complete symbol, including its underline.
            h=len(bitmap);w=len(bitmap[0]);unit=min(4.6*q/w,2.35*q/h)
            left=x-w*unit/2;upper=y-h*unit/2
            for row,bits in enumerate(bitmap):
                for bit,value in enumerate(bits):
                    if value=='#':
                        xx=round(left+bit*unit);yy=round(upper+row*unit)
                        p.fillRect(xx,yy,max(1,round(left+(bit+1)*unit)-xx),
                                   max(1,round(upper+(row+1)*unit)-yy),color)
        p.restore()
    for index,_,label,cx in INDICATORS:icon(label,cx,INK if index in active else GHOST)
    p.end();return im
