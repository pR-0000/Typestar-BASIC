"""Unicode/source bridge for the transcribed S-70 LCD (not the paper font).
Unmapped native bytes round-trip through Unicode private-use U+E080..U+E0FF.
Only quoted BASIC literals accept extended characters. No transliteration.
"""
import unicodedata
# Codes transcribed and checked against the Canon LCD; this is a native character table.
UNICODE_TO_LCD = {
    'Ç':160,'ç':161,'ß':188,'Ë':218,'É':219,'Â':224,
    'é':225,'È':226,'Ò':227,'Ù':228,'à':229,'è':230,
    'ì':231,'ò':232,'ù':233,'Ä':234,'Ö':235,'Ü':236,
    'ä':237,'ö':238,'ü':239,'â':240,'ê':241,'î':242,
    'ô':243,'û':244,'ã':245,'Ã':246,'Ï':247,'õ':248,
    'Õ':249,'Ñ':250,'ñ':251,'ë':252,'ï':253,
}

LCD_TO_UNICODE = {v:k for k,v in UNICODE_TO_LCD.items()}

def encode_source(text):
    text=unicodedata.normalize('NFC',text)
    data=bytearray();quoted=False;rem=False;i=0
    while i<len(text):
        ch=text[i];code=ord(ch)
        if not quoted and not rem and (ch.isascii() and ch.isalpha()):
            j=i+1
            while j<len(text) and text[j].isascii() and (text[j].isalnum() or text[j]=='$'):j+=1
            word=text[i:j];data.extend(word.encode('ascii'));rem=word.upper()=='REM';i=j;continue
        if ch=='"' and not rem:quoted=not quoted
        if 32<=code<=126:data.append(code)
        elif quoted and (ch in UNICODE_TO_LCD or 0xE080<=code<=0xE0FF):
            data.append(UNICODE_TO_LCD.get(ch,code-0xE000))
        else:raise ValueError(f'Unsupported source character U+{code:04X}: native LCD characters require a quoted string')
        i+=1
    return bytes(data)

def decode_source(data):
    text=''.join(chr(b) if b<128 else LCD_TO_UNICODE.get(b,chr(0xE000+b)) for b in data)
    if encode_source(text)!=data:raise ValueError('Noncanonical native source')
    return text

def escape_wire(data):
    return b''.join(bytes((27,b&127)) if b>=128 else bytes((b,)) for b in data)
