"""64-row paper-coordinate scene; each Y increment is a 4-unit feed.

The nominal Y/X pitch ratio of 2 is provisional: native head calibration
is not an absolute calibration of paper motion. Never label it millimetres.
"""
from raster16 import ellipse_closed, diamond
from pattern_codec import SCAN_ROW_BITS

def make_rows():
    pixels=set()
    # Same 29-column extent, separated vertically by four blank rows.
    for columns,top in ((ellipse_closed(29,15),0),(diamond(29,15),19)):
        for x,word in enumerate(columns):
            for y in range(15):
                if word & (1<<SCAN_ROW_BITS[y]): pixels.add((x+1,y+top))
    # Crossed long diagonals, 26 rows; symmetric integer nearest rounding.
    for y in range(26):
        x=1+(28*y+12)//25
        pixels.add((x,y+38)); pixels.add((30-x,y+38))
    # Bresenham tie-breaking can select opposite sides of a half-grid point.
    # Include the mirrored samples so the comparison figure is symmetric.
    pixels |= {(30-x,y) for x,y in pixels}
    assert all(0<=x<31 and 0<=y<64 for x,y in pixels)
    assert all((30-x,y) in pixels for x,y in pixels)
    rows=[]
    for y in range(64):
        bits=sum(1<<(31-x) for x in range(31) if (x,y) in pixels)
        rows.append(bits.to_bytes(4,'big'))
    assert len(rows)==64 and all(not(row[-1]&1) for row in rows)
    assert all(rows[y]==bytes(4) for y in (*range(15,19),*range(34,38)))
    return rows
