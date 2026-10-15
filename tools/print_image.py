"""Print a PC image through Typestar BASIC .41+ (CODE+P, default 7E1).

PNG/JPEG/BMP/TIFF and other Pillow formats are composited on white, fitted to
248x256 pixels, then converted to black/white. Thermal paper is recommended.
One job per Canon boot. No automatic retry after an uncertain acknowledgement.
"""
import argparse
import math
from pathlib import Path
import time
from graphics_stream import encode,decode
from graphics_packed import encode as encode_packed
from transfer_basic import read_byte,send_frame,link_status

IDENT=b'TPG1 PRINT 0248 0256\r\n'
BAND_IDENT=b'TPG1 BAND 0248 0256\r\n'
PACK_IDENT=b'TPG2 PACK 0248 0256\r\n'
MAX_WIDTH,MAX_HEIGHT=248,256

def prepare_image(path, width=MAX_WIDTH, height=MAX_HEIGHT, threshold=128, dither=False, pixel_aspect=2.0):
    from PIL import Image,ImageOps
    if not 1<=width<=MAX_WIDTH or not 1<=height<=MAX_HEIGHT:
        raise ValueError('Image bounds must be within 248x256 pixels')
    if not 0<=threshold<=255:raise ValueError('Threshold must be 0..255')
    if not math.isfinite(pixel_aspect) or not 0.25<=pixel_aspect<=8:
        raise ValueError('Pixel aspect (height/width) must be 0.25..8')
    with Image.open(path) as source:
        rgba=ImageOps.exif_transpose(source).convert('RGBA')
        white=Image.new('RGBA',rgba.size,'white');white.alpha_composite(rgba)
        gray=white.convert('L')
        # S-70 scan calibration: one row is approximately twice as tall as a
        # column is wide. Preserve PAPER proportions, not raster proportions.
        # Apply compensation and fit in a single resample before thresholding.
        scale=min(1.0,width/gray.width,height*pixel_aspect/gray.height)
        size=(max(1,min(width,round(gray.width*scale))),
              max(1,min(height,round(gray.height*scale/pixel_aspect))))
        if size!=gray.size:gray=gray.resize(size,Image.Resampling.LANCZOS)
        mono=(gray.convert('1',dither=Image.Dither.FLOYDSTEINBERG) if dither else
              gray.point(lambda value: 0 if value<threshold else 255,mode='1'))
        pixels=[[mono.getpixel((x,y))==0 for x in range(mono.width)] for y in range(mono.height)]
    return mono,pixels

def transfer(port, pixels, report=print, ack_timeout=30):
    height=len(pixels);width=len(pixels[0]) if height else 0
    if not 1<=width<=MAX_WIDTH or not 1<=height<=MAX_HEIGHT:
        raise ValueError('Firmware accepts images up to 248x256 pixels')
    frames=list(encode(pixels))
    deadline=time.monotonic()+60
    identity=bytearray()
    while not identity.endswith(b'\n') and len(identity)<32:
        remaining=deadline-time.monotonic()
        value=read_byte(port,remaining) if remaining>0 else b''
        if not value:break
        identity.extend(value)
    if identity not in (IDENT,BAND_IDENT,PACK_IDENT):
        raise RuntimeError('Expected .41/.42/.43 printer identification. Press CODE+P at the console; no image data sent.')
    buffered=identity in (BAND_IDENT,PACK_IDENT)
    if identity==PACK_IDENT:
        frames=list(encode_packed(pixels))
        report('WARNING: If band RAM is insufficient, this print job performs NEW and deletes the BASIC program and variables. '
               'This happens only after the first valid image block, not merely on CODE+P.')
    report('Canon graphic printer ready; '+link_status(port))
    report(f'Sending {sum(map(len,frames))} bytes at {getattr(port,"baudrate",1200)}/7{getattr(port,"parity","E")}{getattr(port,"stopbits",1)}.')
    total=len(frames)-2
    cleared=False
    for index,data in enumerate(frames):
        send_frame(port,data,f'Image frame {index+1}/{len(frames)}')
        answer=read_byte(port,ack_timeout)
        if answer==b'\x18' and identity==PACK_IDENT and index==1 and not cleared:
            cleared=True
            report('Canon performed NEW to free print RAM: the previous BASIC program and variables have been deleted.')
            answer=read_byte(port,ack_timeout)
        if answer!=b'\x06':
            raise RuntimeError(f'Frame {index+1}/{len(frames)} not acknowledged ({answer.hex() or "timeout"}). '
                               'The page may be partial. NEW may already have occurred on .43 even if its notice was lost. '
                               'Note the LCD message; no automatic retry. '
                               'Restart the Canon before another attempt.')
        if 1<=index<=total:
            nx=(width+30)//31
            if buffered and index%nx:report(f'Buffered block {index}/{total}')
            elif buffered:report(f'Printed band {index//nx}/{(height+15)//16}')
            else:report(f'Printed block {index}/{total}')
    send_frame(port,b'\x06','Final confirmation')
    report('All print operations acknowledged. Canon should display GFX PRINT OK - KEY.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path)
    p.add_argument('--port',help='COM28, /dev/ttyUSB0 or /dev/cu.usbserial-...; omit for preview only')
    from serial_rates import add_baud_argument,bits_per_frame
    add_baud_argument(p)
    p.add_argument('--width',type=int,default=MAX_WIDTH,help='Maximum width, 1..248 (aspect preserved)')
    p.add_argument('--height',type=int,default=MAX_HEIGHT,help='Maximum height, 1..256')
    p.add_argument('--threshold',type=int,default=128,help='Black/white cutoff, 0..255')
    p.add_argument('--dither',action='store_true',help='Floyd-Steinberg dithering, useful for photos')
    p.add_argument('--pixel-aspect',type=float,default=2.0,
                   help='Physical pixel height/width (default 2.0); 1 for an already compensated raw raster')
    p.add_argument('--preview',type=Path,help='Save the exact black/white raster as PNG')
    p.add_argument('--stream',type=Path,help='Also save the encoded TPG1 stream')
    args=p.parse_args()
    mono,pixels=prepare_image(args.image,args.width,args.height,args.threshold,args.dither,args.pixel_aspect)
    stream=b''.join(encode(pixels));assert decode(stream)==pixels
    if args.preview:
        if args.preview.resolve()==args.image.resolve():p.error('Preview must not overwrite the source image')
        mono.save(args.preview,format='PNG')
    if args.stream:
        if args.stream.resolve()==args.image.resolve() or args.preview and args.stream.resolve()==args.preview.resolve():
            p.error('Stream must have a separate output path')
        args.stream.write_bytes(stream)
    count=((mono.width+30)//31)*((mono.height+15)//16)
    print(f'{mono.width}x{mono.height} pixels, {count} blocks, {len(stream)} serial bytes.')
    print(f'Paper pixel aspect compensation: {args.pixel_aspect:g}. Preview shows raw transmitted pixels.')
    packed_size=sum(len(f) for f in encode_packed(pixels))
    frame_bits=bits_per_frame(args.parity,args.stopbits)
    print(f'Serial minimum at {args.baud}/7{args.parity}{args.stopbits}: legacy {len(stream)*frame_bits/args.baud:.1f} s; .43 compact {packed_size*frame_bits/args.baud:.1f} s '
          f'({packed_size} bytes). Motor operation adds time.')
    if not args.port:
        print('Preview only. Add --port COM28 (or the Linux/macOS port) to print.');return
    import serial
    print('Firmware .43 may perform NEW if RAM is insufficient. SAVE any BASIC program you want to keep before starting.',flush=True)
    print(f'Set BAUD {args.baud} and (.46+) SERCFG 7{args.parity}{args.stopbits} on Canon before CODE+P.',flush=True)
    with serial.Serial(args.port,args.baud,bytesize=serial.SEVENBITS,parity=args.parity,
                       stopbits=args.stopbits,timeout=0.1,write_timeout=10,
                       rtscts=True,xonxoff=False,dsrdtr=False) as port:
        port.reset_input_buffer()
        print('Press CODE+P on Canon now (not LOAD). Paper will move.',flush=True)
        transfer(port,pixels,lambda message:print(message,flush=True))

if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError,ValueError,ImportError) as error:
        raise SystemExit('Image printing failed: '+str(error))
