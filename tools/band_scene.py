"""Four 31-column, sixteen-channel bands, encoded in native Canon format 0."""
from raster16 import ellipse_closed, diamond
from graphics_canvas import Canvas
from pattern_codec import encode_columns, SCAN_ROW_BITS

def make_bands():
    result=[]
    for shape in (ellipse_closed(29,15), diamond(29,15)):
        result.append(encode_columns([0]+shape+[0],0,31))
    # Reference canvas cuts the rectangle at y=15/16 without duplicating pixels.
    canvas=Canvas(31,32)
    canvas.box(3,0,27,31)
    canvas.line(3,0,27,31)
    result.extend(canvas.bands())
    assert len(result)==4 and all(len(b)==62 for b in result)
    return result
