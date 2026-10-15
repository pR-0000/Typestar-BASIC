"""Draw a schematic top view of a DIP28 ROM with its notch to the left."""
from pathlib import Path

import reportlab
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent


def render(language='fr'):
    import json
    labels=json.loads((HERE/'en/diagram-labels.json').read_text(encoding='utf8')) if language=='en' else {}
    def tr(text):return labels.get(text,text)
    font_dir = Path(reportlab.__file__).parent / 'fonts'
    normal = ImageFont.truetype(str(font_dir / 'Vera.ttf'), 36)
    bold = ImageFont.truetype(str(font_dir / 'VeraBd.ttf'), 40)
    image = Image.new('RGB', (1800, 720), 'white')
    draw = ImageDraw.Draw(image)
    black = '#222222'
    blue = '#184ed0'
    draw.text((900, 45), tr('ARRIÈRE : support papier'), font=bold, fill=black, anchor='mt')
    draw.text((900, 644), tr('DEVANT : clavier vers vous'), font=bold, fill=black, anchor='mt')
    # With the notch facing left, pin 1 is bottom-left in top view.
    for i in range(14):
        x = 365 + i * 78
        draw.rectangle((x, 177, x+28, 244), fill='white', outline=black, width=4)
        draw.rectangle((x, 456, x+28, 523), fill='white', outline=black, width=4)
    draw.rectangle((330, 240, 1430, 460), fill='white', outline=black, width=5)
    draw.ellipse((292, 312, 368, 388), fill='white')
    draw.arc((292, 312, 368, 388), 270, 90, fill=black, width=5)
    draw.text((900, 350), tr('ROM IC8 - vue de dessus'), font=bold, fill=black, anchor='mm')
    draw.text((75, 305), tr('Encoche'), font=normal, fill=black)
    draw.text((75, 350), tr('à gauche'), font=normal, fill=black)
    draw.line((230, 350, 320, 350), fill=black, width=4)
    draw.polygon(((320,350),(301,339),(301,361)), fill=black)
    draw.ellipse((356, 423, 377, 444), fill=blue)
    draw.line((188, 595, 361, 447), fill=blue, width=4)
    draw.polygon(((361,447),(354,470),(336,451)), fill=blue)
    draw.text((55, 598), tr('Broche 1'), font=bold, fill=blue)
    draw.text((379, 539), '1', font=normal, fill=black, anchor='mt')
    draw.text((1393, 539), '14', font=normal, fill=black, anchor='mt')
    draw.text((379, 130), '28', font=normal, fill=black, anchor='mt')
    draw.text((1393, 130), '15', font=normal, fill=black, anchor='mt')
    output = HERE / ('en/images' if language=='en' else 'images') / 'installation-sens-rom.png'
    image.save(output)
    return output


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--language',default='fr',choices=['fr','en'])
    print(render(parser.parse_args().language))
