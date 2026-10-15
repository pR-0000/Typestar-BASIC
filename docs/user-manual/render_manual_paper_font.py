"""Render a legible font reference from the selected firmware's actual decoder.

The glyphs are decoded by Studio's HD6301 core, preserving every head-column bit.
The grid is an original manual layout, with integer-sized pixels.
"""
import argparse, hashlib, json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'studio/internal'))
from emulator_worker import backend

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mask-rom',required=True,type=Path)
    p.add_argument('--firmware-rom',required=True,type=Path)
    args=p.parse_args()
    CPU=backend(mask_path=args.mask_rom.resolve(),firmware_path=args.firmware_rom.resolve())
    font=ImageFont.truetype(str(HERE/'fonts/Lato-Regular.ttf'),25)
    image=Image.new('RGB',(16*104,6*145),'white');draw=ImageDraw.Draw(image)
    decoded=[]
    cpu=CPU('')
    for code in range(32,127):
        cpu.a=code;cpu.x=0x1F00;cpu.pc=cpu.symbols['HFDECODE'];cpu.sp=0x1FFF
        cpu.push(0xF0);cpu.push(0xFF)
        for step in range(150000):
            if cpu.pc==0xFFF0:break
            cpu.step()
        else:raise RuntimeError(f'Decoder timeout: {code}')
        assert not cpu.c,(code,cpu.pc)
        data=bytes(cpu.m[0x1F00:0x1F00+93])
        glyph=Image.new('RGB',(62,96),'white');g=ImageDraw.Draw(glyph)
        for x in range(31):
            word=int.from_bytes(data[x*3:x*3+3],'little')
            for y in range(24):
                if word&(1<<y):g.rectangle((x*2,y*4,x*2+1,y*4+3),fill='black')
        index=code-32;ox=index%16*104;oy=index//16*145
        draw.rectangle((ox+1,oy+1,ox+102,oy+143),outline='#d6c8b8',width=1)
        image.paste(glyph,(ox+21,oy+9))
        label=str(code);draw.text((ox+(104-draw.textlength(label,font=font))/2,oy+111),label,font=font,fill='#24211d')
        decoded.append({'code':code,'columns':data.hex()})
    image.save(HERE/'images/lprint-characters.png')
    report={'generator':'Studio HD6301 core / HFDECODE','firmware_sha256':hashlib.sha256(args.firmware_rom.read_bytes()).hexdigest(),'mask_sha256':hashlib.sha256(args.mask_rom.read_bytes()).hexdigest(),'glyphs':decoded}
    target=ROOT/'build/user-manual/paper-font-illustration.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('PASS: 95 firmware glyphs rendered',flush=True)

if __name__=='__main__':main()
