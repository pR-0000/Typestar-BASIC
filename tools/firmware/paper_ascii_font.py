"""ASCII corrections for the regional NH7 table; original trace stays intact.

Native triplets are preserved for 85 characters. '[' and ']' are remapped
from Canon slots 5D/5E. Backslash mirrors the original slash in X. Other
punctuation is constructed explicitly, in the same 31-column native format.
The row order below follows the continuous original slash (20 active rows).
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
ROWS = [(0,b) for b in range(2,8)]+[(1,b) for b in range(8)]+[(2,b) for b in range(6)]

def corrected(trace):
    glyphs={g['char']:bytes(v for u in g['units'] for v in u['lanes']) for g in trace['glyphs']}
    fixes={'[':glyphs[']'], ']':glyphs['^'],
           '\\':b''.join(glyphs['/'][x*3:x*3+3] for x in range(30,-1,-1))}
    def bitmap(points):
        buf=bytearray(93)
        for x,y in points:
            lane,bit=ROWS[y];buf[x*3+lane]|=1<<bit
        return bytes(buf)
    def line(x0,y0,x1,y1):
        n=max(abs(x1-x0),abs(y1-y0))
        return {(round(x0+(x1-x0)*i/n),round(y0+(y1-y0)*i/n)) for i in range(n+1)}
    def strokes(*segments):
        p=set().union(*(line(*v) for v in segments))
        return bitmap(p|{(x+1,y) for x,y in p})
    fixes['|']=bitmap({(x,y) for x in (14,15) for y in range(20)})
    fixes['_']=bitmap({(x,y) for x in range(3,28) for y in (18,19)})
    fixes['^']=strokes((7,7,14,1),(14,1,21,7))
    fixes['`']=strokes((11,1,16,5))
    fixes['~']=strokes((5,9,9,6),(9,6,13,6),(13,6,18,10),(18,10,22,10),(22,10,25,7))
    # Keep the compact braces within the existing shared Huffman alphabet.
    xs=(18,15,13,12,12,12,11,9,11,12,12,12,12,13,15,18)
    fixes['{']=bitmap({(x+d,y+3) for y,x in enumerate(xs) for d in (0,1)})
    fixes['}']=b''.join(fixes['{'][x*3:x*3+3] for x in range(30,-1,-1))
    return glyphs|fixes, fixes
