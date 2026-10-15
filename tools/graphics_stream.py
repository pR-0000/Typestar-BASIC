"""Offline TPG1 graphics stream prototype. No serial transmission or motors.

31x16 tiles use the paper-validated Canon row order and 62-byte format-0
payload. The firmware receiver/print transaction is not yet implemented.
"""
import argparse
import binascii
from pathlib import Path
from pattern_codec import SCAN_ROW_BITS, encode_columns

def frame(body):
    data=body.encode('ascii')
    return data+b'*'+f'{binascii.crc_hqx(data,0xFFFF):04X}'.encode()+b'\n'

def encode(pixels):
    height=len(pixels);width=len(pixels[0]) if height else 0
    if not 1<=width<=4096 or not 1<=height<=65535 or any(len(r)!=width for r in pixels):
        raise ValueError('Rectangular image required, width 1..4096, height 1..65535')
    yield frame(f'TPG1:{width:04X}:{height:04X}')
    seq=0
    for top in range(0,height,16):
        for left in range(0,width,31):
            columns=[0]*31
            for y in range(top,min(top+16,height)):
                for x in range(left,min(left+31,width)):
                    if pixels[y][x]:columns[x-left]|=1<<SCAN_ROW_BITS[y-top]
            payload=encode_columns(columns,0,31)
            yield frame(f'D:{seq:08X}:{top//16:04X}:{left//31:04X}:{payload.hex().upper()}')
            seq+=1
    yield frame(f'E:{seq:08X}')

def decode(stream):
    """Strict offline validator/reconstruction, not a print-side ACK model."""
    bodies=[]
    for line in stream.splitlines():
        body,sep,checksum=line.rpartition(b'*')
        if not sep or len(checksum)!=4 or binascii.crc_hqx(body,0xFFFF)!=int(checksum,16):
            raise ValueError('Invalid frame CRC')
        bodies.append(body.decode('ascii').split(':'))
    if not bodies or len(bodies[0])!=3 or bodies[0][0]!='TPG1':raise ValueError('Missing TPG1 header')
    w,h=(int(s,16) for s in bodies[0][1:])
    if not 1<=w<=4096 or not 1<=h<=65535:raise ValueError('Invalid dimensions')
    nx=(w+30)//31;count=nx*((h+15)//16)
    if len(bodies)!=count+2 or bodies[-1]!=['E',f'{count:08X}']:raise ValueError('Incomplete stream')
    result=[[False]*w for _ in range(h)]
    for seq,f in enumerate(bodies[1:-1]):
        row,col=divmod(seq,nx)
        if len(f)!=5 or f[:4]!=['D',f'{seq:08X}',f'{row:04X}',f'{col:04X}']:
            raise ValueError('Unexpected tile sequence/position')
        payload=bytes.fromhex(f[4])
        if len(payload)!=62:raise ValueError('Invalid tile size')
        for x in range(31):
            word=int.from_bytes(payload[2*x:2*x+2],'big')
            for y,bit in enumerate(SCAN_ROW_BITS):
                value=bool(word&(1<<bit));px,py=col*31+x,row*16+y
                if px<w and py<h:result[py][px]=value
                elif value:raise ValueError('Nonwhite padding')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--threshold',type=int,default=128)
    parser.add_argument('--dither',action='store_true')
    args=parser.parse_args()
    if not 0<=args.threshold<=255:parser.error('threshold must be 0..255')
    from PIL import Image,ImageOps
    with Image.open(args.image) as source:
        rgba=ImageOps.exif_transpose(source).convert('RGBA')
        white=Image.new('RGBA',rgba.size,'white');white.alpha_composite(rgba)
        gray=white.convert('L')
        if args.dither:gray=gray.convert('1',dither=Image.Dither.FLOYDSTEINBERG)
        pixels=[[gray.getpixel((x,y))<args.threshold for x in range(gray.width)] for y in range(gray.height)]
    stream=b''.join(encode(pixels))
    assert decode(stream)==pixels
    args.output.write_bytes(stream)
    print(f'OFFLINE ONLY: {gray.width}x{gray.height}, {len(stream)} bytes; no data sent to Canon.')

if __name__=='__main__':main()
