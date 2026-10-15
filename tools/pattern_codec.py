"""Codec for logical 16-channel motifs, plus the paper-validated row order.

Logical bits are numbered as in the original format-0 packed word. Convert
through the three decoded ROM lanes so format-1 glyphs retain their format.
Encoding does not depend on row order. No motor timing or geometry scale
is inferred here; the row permutation was confirmed by the user's v2 test.
"""

# Top-to-bottom order inferred from the user's 2026-09-09 scan, then confirmed
# on v2: v1 letters M..P precede A..L in height. This is an ordinal mapping only;
# dot pitch, phase offsets and equality of row spacing remain uncalibrated.
SCAN_ROW_BITS = (12, 13, 14, 15, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


def lanes_from_word(word):
    if not isinstance(word,int) or not 0 <= word <= 0xFFFF:
        raise ValueError('Pattern word must be an unsigned 16-bit integer')
    p,q=word>>8,word&255
    return p&0xF0,q,p&15


def encode_word(word,fmt):
    a,b,c=lanes_from_word(word)
    if fmt==0:
        return bytes([a|c,b])
    if fmt==1:
        return bytes([c,b,a])
    raise ValueError('This calibration supports original formats 0 and 1 only')


def encode_columns(columns,fmt,capacity):
    if len(columns)>capacity:
        raise ValueError('Pattern would overrun the original glyph span')
    return b''.join(encode_word(word,fmt) for word in columns+[0]*(capacity-len(columns)))
