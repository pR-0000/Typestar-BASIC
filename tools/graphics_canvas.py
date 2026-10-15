"""Host-side paper canvas, split into Canon 16-channel bands.

Coordinates are logical print columns and head rows, not millimetres.
This is a reference renderer for future BASIC commands, not HD6301 firmware.
Band feed (currently 56 units) is a separate mechanical parameter.
"""
from pattern_codec import SCAN_ROW_BITS, encode_columns

class Canvas:
    def __init__(self, width, height):
        if type(width) is not int or type(height) is not int or not 1 <= width <= 31 or not 1 <= height <= 1024:
            raise ValueError('Canvas must be 1..31 columns by 1..1024 rows')
        self.width, self.height = width, height
        self.pixels = set()

    def _check(self, x, y):
        if type(x) is not int or type(y) is not int or not 0 <= x < self.width or not 0 <= y < self.height:
            raise ValueError('Point outside canvas')

    def pset(self, x, y):
        self._check(x, y)
        self.pixels.add((x, y))

    def line(self, x0, y0, x1, y1):
        # Validate both endpoints before writing any pixels. No silent clipping.
        self._check(x0, y0); self._check(x1, y1)
        dx, dy = abs(x1-x0), -abs(y1-y0)
        sx, sy = (1 if x0<x1 else -1), (1 if y0<y1 else -1)
        err = dx+dy
        while True:
            self.pset(x0, y0)
            if (x0, y0) == (x1, y1): return
            twice = 2*err
            if twice >= dy: err += dy; x0 += sx
            if twice <= dx: err += dx; y0 += sy

    def box(self, x0, y0, x1, y1):
        self._check(x0, y0); self._check(x1, y1)
        self.line(x0,y0,x1,y0); self.line(x1,y0,x1,y1)
        self.line(x1,y1,x0,y1); self.line(x0,y1,x0,y0)

    def bands(self):
        """Return 62-byte buffers. Blank padding never repeats the seam row.

        Always 31 physical columns even for narrower canvases: Canon consumes
        31 units and must never read the metadata after this buffer.
        """
        result=[]
        for top in range(0,self.height,16):
            columns=[0]*31
            for x,y in self.pixels:
                if top <= y < top+16:
                    columns[x] |= 1 << SCAN_ROW_BITS[y-top]
            result.append(encode_columns(columns,0,31))
        return result
