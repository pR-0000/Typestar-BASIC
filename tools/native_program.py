"""Firmware .83 codec: extended bytes are raw data inside quoted strings."""
from transfer_array_basic import codec as legacy
from native_text import encode_source,decode_source
import re
WORDS=legacy.WORDS
ENCODE=legacy.ENCODE
DECODE=legacy.DECODE
read_source=legacy.read_source

def tokenize(source):
    raw=encode_source(source)
    if len(raw)>63:raise ValueError('Source exceeds 63 native bytes')
    text=raw.decode('latin1');out=bytearray();i=0
    while i<len(text):
        if text[i]=='"':
            end=text.find('"',i+1);end=len(text) if end<0 else end+1
            out.extend(raw[i:end]);i=end;continue
        match=legacy.IDENT.match(text,i)
        if match:
            word=match.group();token=ENCODE.get(word.upper())
            out.extend(bytes((token,)) if token is not None else word.encode('ascii'))
            i=match.end()
            if word.upper()=='REM':out.extend(raw[i:]);break
        else:out.append(raw[i]);i+=1
    return bytes(out)

def detokenize(payload):
    out=bytearray();quoted=False;rem=False
    for b in payload:
        if b==34 and not rem:quoted=not quoted
        if not quoted and not rem and b in DECODE:
            word=DECODE[b];out.extend(word.encode());rem=word=='REM'
        elif 32<=b<=126 or (quoted and b>=128):out.append(b)
        else:raise ValueError('Invalid token/native byte')
    source=decode_source(out)
    if len(out)>63 or tokenize(source)!=payload:raise ValueError('Noncanonical token stream')
    return source

def pack(lines,capacity=5952):
    records={}
    for number,source in lines:
        if not 1<=number<=65535 or number in records:raise ValueError('Invalid/duplicate line number')
        if not source.strip():raise ValueError('Empty stored statement')
        payload=tokenize(source);records[number]=bytes((len(payload)+3,))+number.to_bytes(2,'big')+payload
    arena=b''.join(records[n] for n in sorted(records))+b'\0'
    if len(arena)>capacity:raise ValueError('Program RAM full')
    return arena

def unpack(arena):
    pos=0;previous=0;lines=[]
    while pos<len(arena):
        length=arena[pos]
        if not length:
            if pos!=len(arena)-1:raise ValueError('Bytes after sentinel')
            return lines
        if not 4<=length<=66 or pos+length>=len(arena):raise ValueError('Invalid record length')
        number=int.from_bytes(arena[pos+1:pos+3],'big')
        if number<=previous:raise ValueError('Unsorted line number')
        source=detokenize(arena[pos+3:pos+length])
        if not source.strip():raise ValueError('Empty statement')
        lines.append((number,source));previous=number;pos+=length
    raise ValueError('Missing sentinel')
