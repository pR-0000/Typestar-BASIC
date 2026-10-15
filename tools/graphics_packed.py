"""TPG2: printable 6-bit packing or byte runs, unchanged thermal tile data.

B payload: 62 bytes packed MSB-first into 83 symbols (value+48), final two
bits zero. R payload: uppercase count/value hex pairs, counts 1..62. The
shorter representation wins. CRC and sequence/coordinates remain explicit.
"""
from itertools import groupby
from graphics_stream import encode as encode_v1,frame

def pack(data):
    if len(data)!=62:raise ValueError('Expected 62 bytes')
    number=int.from_bytes(data,'big')<<2
    return ''.join(chr(48+((number>>shift)&63)) for shift in range(492,-1,-6))

def unpack(body):
    if len(body)!=83 or any(not 48<=ord(c)<=111 for c in body):raise ValueError('Invalid packed tile')
    value=0
    for c in body:value=(value<<6)|(ord(c)-48)
    if value&3:raise ValueError('Nonzero padding')
    return (value>>2).to_bytes(62,'big')

def runs(data):
    return ''.join(f'{len(list(group)):02X}{value:02X}' for value,group in groupby(data))

def unruns(body):
    if len(body)%4 or any(c not in '0123456789ABCDEF' for c in body):raise ValueError('Invalid runs')
    result=bytearray()
    for i in range(0,len(body),4):
        count=int(body[i:i+2],16)
        if not 1<=count<=62 or len(result)+count>62:raise ValueError('Invalid run count')
        result.extend(bytes((int(body[i+2:i+4],16),))*count)
    if len(result)!=62:raise ValueError('Wrong decoded size')
    return bytes(result)

def encode(pixels):
    for original in encode_v1(pixels):
        body=original.split(b'*')[0].decode()
        if body.startswith('TPG1:'):body='TPG2:'+body[5:]
        elif body.startswith('D:'):
            prefix,payload=body.rsplit(':',1);data=bytes.fromhex(payload)
            packed=pack(data);rle=runs(data)
            kind,text=('R',rle) if len(rle)<len(packed) else ('B',packed)
            assert (unruns(text) if kind=='R' else unpack(text))==data
            body=kind+prefix[1:]+':'+text
        yield frame(body)
