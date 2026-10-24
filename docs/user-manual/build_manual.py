"""Build the French Markdown manual with converged page references.

No ROMs or serial connection needed. Uses the bundled, OFL-licensed Lato family.
The manifest defines reading order and the complete command/function index.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote

import mistune
import reportlab
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageBreak, PageTemplate, Paragraph,
    Preformatted, Spacer, Table, TableStyle,
)
from reportlab.platypus.xpreformatted import XPreformatted
from source_notes import SourceNotes

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TEAL = colors.HexColor('#905733')
PALE = colors.HexColor('#f6eee4')
GREY = colors.HexColor('#69635d')
MD = mistune.create_markdown(renderer='ast', plugins=['table'])
NOTES = None


def normalized(text):
    # The bundled Lato faces include all four directional arrows.
    return text.replace('\u2014', '-').replace('\u2013', '-').replace('\u2011', '-')


def code_flow(text, style):
    # Preserve the original byte characters in PDF listings as in Studio.
    # Markup changes only the font; copy/paste still contains the native byte.
    if re.search('[\ue080-\ue0ff]',text):
        markup=re.sub('[\ue080-\ue0ff]',lambda m:'<font name="Byte">'+m[0]+'</font>',html.escape(text))
        return XPreformatted(markup,style)
    return Preformatted(text,style)


def slug(text):
    ascii_text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', ascii_text.lower()).strip('-')


def plain(tokens):
    return ''.join(t.get('raw', '') if 'children' not in t else plain(t['children']) for t in tokens)


def anchors(token):
    found = re.findall(r'<a id="([^"]+)"', token.get('raw', ''))
    for child in token.get('children', []):
        found.extend(anchors(child))
    return found


def destination(url, source):
    if re.match(r'https?://', url):
        return None
    path, _, anchor = url.partition('#')
    name = Path(path).name if path else source.name
    if not name.endswith('.md'):
        return None
    return name + '#' + anchor


def setup_styles():
    font_dir = HERE / 'fonts'
    for name, filename in [('Body', 'Lato-Regular.ttf'), ('BodyBold', 'Lato-Bold.ttf'),
                           ('BodyItalic', 'Lato-Italic.ttf'), ('BodyBoldItalic','Lato-BoldItalic.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    pdfmetrics.registerFont(pdfmetrics.Font('Code', 'Courier', 'WinAnsiEncoding'))
    pdfmetrics.registerFont(TTFont('Byte', str(ROOT/'studio/internal/assets/typestar-bytes.ttf')))
    pdfmetrics.registerFontFamily('Code', normal='Code', bold='Code', italic='Code', boldItalic='Code')
    pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold',
                                 italic='BodyItalic', boldItalic='BodyBoldItalic')
    body = ParagraphStyle('body', fontName='Body', fontSize=11.5, leading=16.5,
                          spaceAfter=9, textColor=colors.HexColor('#24211d'),
                          allowWidows=0, allowOrphans=0)
    return {
        'body': body,
        'h1': ParagraphStyle('h1', parent=body, fontName='BodyBold', fontSize=23,
                             leading=29, spaceAfter=20, textColor=TEAL, keepWithNext=True),
        'h2': ParagraphStyle('h2', parent=body, fontName='BodyBold', fontSize=14.5,
                             leading=19, spaceBefore=17, spaceAfter=9, keepWithNext=True),
        'h3': ParagraphStyle('h3', parent=body, fontName='BodyBold', fontSize=12.5,
                             leading=17, spaceBefore=11, spaceAfter=7, keepWithNext=True),
        'small': ParagraphStyle('small', parent=body, fontSize=9.8, leading=13.1),
        'caption': ParagraphStyle('caption', parent=body, fontName='BodyItalic',
                                  fontSize=9.5, leading=13.1, textColor=GREY),
        'code': ParagraphStyle('code', fontName='Code', fontSize=9.7, leading=13.2),
        'quote': ParagraphStyle('quote', parent=body, leftIndent=12,
                               borderColor=TEAL, borderWidth=0.6, borderPadding=9, backColor=PALE,
                               spaceBefore=6, spaceAfter=12),
        'cover': ParagraphStyle('cover', parent=body, fontName='BodyBold',
                               fontSize=34, leading=43, textColor=TEAL,
                               alignment=TA_CENTER),
        'subtitle': ParagraphStyle('subtitle', parent=body, fontName='BodyBold',
                                  fontSize=22, leading=29, textColor=TEAL,
                                  alignment=TA_CENTER),
        'toc': ParagraphStyle('toc', parent=body, fontSize=10.2, leading=13.5, spaceAfter=0),
        'index': ParagraphStyle('index', parent=body, fontSize=10, leading=13.1, spaceAfter=0),
    }


def inline(tokens, source, pages, page_refs=False):
    parts = []
    for token in tokens:
        kind = token['type']
        children = token.get('children', [])
        if kind == 'text':
            parts.append(html.escape(normalized(token['raw'])))
        elif kind == 'codespan':
            parts.append('<font name="Code" size="9.7">' + html.escape(normalized(token['raw'])) + '</font>')
        elif kind in ('strong', 'emphasis'):
            tag = 'b' if kind == 'strong' else 'i'
            parts.append(f'<{tag}>' + inline(children, source, pages, page_refs) + f'</{tag}>')
        elif kind == 'link':
            label = inline(children, source, pages)
            url = token['attrs']['url']
            target = destination(url, source)
            raw_label=plain(children)
            if NOTES and raw_label in NOTES.config.get('citation_labels',{}):
                parts.append(NOTES.marker(raw_label,url,source.name))
            elif target in pages:
                parts.append(f'<link href="#{target}" color="#905733">{label}</link>')
                if page_refs:
                    parts.append(f' (p. {pages[target]})')
            elif target is not None:
                parts.append(label)
                if page_refs:
                    parts.append(' (p. ...)')
            elif re.match(r'https?://', url):
                parts.append(label + (NOTES.marker(raw_label,url,source.name) if NOTES else ''))
            else:
                parts.append(label)
        elif kind in ('softbreak', 'linebreak'):
            parts.append(' ' if kind == 'softbreak' else '<br/>')
        elif kind == 'image':
            parts.append(html.escape(plain(children)))
        elif kind == 'inline_html':
            # Only explicit anchors are consumed at the block level.
            pass
        else:
            parts.append(inline(children, source, pages, page_refs))
    return ''.join(parts)


class ManualDoc(BaseDocTemplate):
    def __init__(self, output, config, note_reserves=None):
        super().__init__(str(output), pagesize=(210*mm, 297*mm),
                         leftMargin=22*mm, rightMargin=22*mm,
                         topMargin=23*mm, bottomMargin=22*mm,
                         title=config['title']+' - '+config['subtitle'],
                         author=config['author'])
        self.page_map = {}
        self.total_pages = 0
        self.running_title = config['subtitle']
        self.config = config
        self.note_pages={}
        self.note_reserves=note_reserves or {}
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate('manual', [frame], onPage=self.page_header,
                                           onPageEnd=self.page_notes))

    def record_note(self, canvas, kind, label):
        self.note_pages.setdefault(self.page,set()).add(int(label))

    def page_notes(self, canvas, doc):
        NOTES.draw(canvas,self.note_pages.get(self.page,set()),self.leftMargin,
                   self.bottomMargin,self.width)

    def page_header(self, canvas, doc):
        reserve=self.note_reserves.get(doc.page,0)
        frame=self.pageTemplate.frames[0]
        frame._y1=self.bottomMargin+reserve
        frame._height=self.height-reserve
        frame._geom()
        if hasattr(canvas,'setNamedCB'):
            canvas.setNamedCB('manual_note',self.record_note)
        else:
            canvas.manual_note=self.record_note
        canvas.saveState()
        canvas.setStrokeColor(TEAL)
        canvas.setLineWidth(1.1)
        canvas.setFont('Body', 8)
        canvas.setFillColor(GREY)
        if doc.page > 1:
            canvas.line(self.leftMargin, 281*mm, 188*mm, 281*mm)
            canvas.drawString(self.leftMargin, 285*mm, 'TYPESTAR BASIC')
            canvas.drawRightString(188*mm, 285*mm, "User's manual - EN" if self.config.get('language')=='en' else 'Manuel de l\'utilisateur - FR')
        canvas.drawString(self.leftMargin, 13*mm, ('Reference ' if self.config.get('language')=='en' else 'Référence ')+self.config['version'])
        canvas.drawRightString(188*mm, 13*mm, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        self.total_pages = max(self.total_pages, self.page)
        for key in getattr(flowable, 'manual_keys', []):
            self.page_map[key] = self.page
            self.canv.bookmarkPage(key)
        if hasattr(flowable, 'outline'):
            title, key, level = flowable.outline
            self.canv.addOutlineEntry(title, key, level=level, closed=False)


def figures(items, source, styles, config):
    """Fit complete images; a multi-image paragraph is a framed gallery."""
    gallery = len(items) > 1
    gap = 6*mm
    width = (166*mm-gap*(len(items)-1))/len(items)
    cells = []
    for item in items:
        path = source.parent / unquote(item['attrs']['url'])
        if not path.exists():
            raise FileNotFoundError(path)
        with PILImage.open(path) as img:
            w,h = img.size
        size = config.get('image_layout',{}).get(path.name,{})
        padding = 3*mm if gallery else 0
        scale = min((width-2*padding)/w, size.get('max_width_mm',166)*mm/w,
                    size.get('max_height_mm',76)*mm/h)
        picture = Image(str(path),width=w*scale,height=h*scale,mask='auto')
        if gallery:
            panel = Table([[picture]], colWidths=[width], rowHeights=[82*mm])
            panel.setStyle(TableStyle([
                ('BOX',(0,0),(-1,-1),.45,GREY), ('ALIGN',(0,0),(-1,-1),'CENTER'),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('LEFTPADDING',(0,0),(-1,-1),padding),
                ('RIGHTPADDING',(0,0),(-1,-1),padding),
                ('TOPPADDING',(0,0),(-1,-1),padding),
                ('BOTTOMPADDING',(0,0),(-1,-1),padding)]))
            picture = panel
        caption=html.escape(plain(item['children']))
        ref=config.get('image_sources',{}).get(path.name)
        if ref:caption+=NOTES.marker(ref['label'],ref.get('url',''),source.name)
        cells.append([picture,Spacer(1,5),
                      Paragraph(caption,styles['caption']),Spacer(1,9)])
    row=[]; widths=[]
    for i,cell in enumerate(cells):
        if i:row.append('');widths.append(gap)
        row.append(cell);widths.append(width)
    figure=Table([row],colWidths=widths,hAlign='LEFT')
    figure.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'CENTER'), ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0), ('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    return figure


def chapter(tokens, source, styles, pages, config):
    flow = []
    pending = []
    first_heading = True
    listing_index = 0
    for token_index, token in enumerate(tokens):
        kind = token['type']
        ids = anchors(token)
        if ids:
            pending.extend(source.name+'#'+name for name in ids)
            if kind == 'block_html' or not re.sub(r'<a id="[^"]+"></a>', '', plain(token.get('children', []))).strip():
                continue
        if kind == 'blank_line':
            continue
        if kind == 'block_html':
            if re.fullmatch(r'\s*<!--.*?-->\s*',token['raw'],re.S):
                continue
            raise ValueError(f'Unsupported HTML in {source}: {token["raw"]}')
        elif kind == 'heading':
            level = token['attrs']['level']
            title = normalized(plain(token['children']))
            key = source.name+'#'+slug(title)
            if key in config.get('page_break_before', []):
                flow.append(PageBreak())
            p = Paragraph(inline(token['children'], source, pages), styles['h'+str(min(level, 3))])
            p.manual_keys = pending + [key]
            if first_heading:
                p.manual_keys.append(source.name+'#')
                first_heading = False
            pending = []
            if level <= 2 and not (source.name == '99-lexique.md' and level == 2):
                p.outline = (title, key, level-1)
            flow.append(p)
        elif kind in ('paragraph', 'block_text'):
            images = [t for t in token.get('children', []) if t['type'] == 'image']
            if images:
                flow.append(figures(images,source,styles,config))
            else:
                paragraph = Paragraph(inline(token['children'], source, pages,
                                             page_refs=source.name == '99-lexique.md'), styles['body'])
                following = next((t for t in tokens[token_index+1:] if t['type']!='blank_line'), None)
                if following:
                    next_image = following['type']=='paragraph' and any(t['type']=='image' for t in following.get('children',[]))
                    code_intro = plain(token['children']).rstrip().endswith(':') and following['type']=='block_code'
                    if next_image or code_intro:
                        paragraph.keepWithNext=True
                flow.append(paragraph)
        elif kind == 'block_code':
            raw = normalized(token['raw'].rstrip())
            code_style=styles['code']
            if token.get('attrs',{}).get('info','')!='basic':
                code_style=ParagraphStyle('shell-code',parent=styles['code'],fontSize=9.3)
            # Code examples fit in 63 native bytes; general shell examples can wrap.
            rows = raw.splitlines()
            expanded = []
            for row in rows:
                limit=int(156*mm/pdfmetrics.stringWidth('M','Code',code_style.fontSize))
                while pdfmetrics.stringWidth(row, 'Code', code_style.fontSize) > 156*mm:
                    expanded.append(row[:limit])
                    row = '  '+row[limit:]
                expanded.append(row)
            if source.name == '11-programmes-complets.md' or len(expanded)>20:
                if source.name == '11-programmes-complets.md':
                    label=config['example_programs'][listing_index]['title']+' - listing'
                    listing_index+=1
                else:
                    language=token.get('attrs',{}).get('info','').upper()
                    label='Listing '+language
                listing_code=ParagraphStyle('listing-code',parent=code_style,leading=12.5)
                listing=Table([[Paragraph('<b>'+html.escape(label)+'</b>',styles['small'])]]+
                              [[code_flow(line or ' ',listing_code)] for line in expanded],
                              colWidths=[166*mm],repeatRows=1,hAlign='LEFT',splitByRow=len(expanded)>20)
                listing.setStyle(TableStyle([
                    ('BACKGROUND',(0,0),(-1,0),PALE),
                    ('LINEBELOW',(0,0),(-1,0),.6,TEAL),
                    ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
                    ('TOPPADDING',(0,0),(-1,0),6),('BOTTOMPADDING',(0,0),(-1,0),6),
                    ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8)]))
                # Keep small binary pixel patterns together so their shape
                # stays readable across the DATA rows, including their label.
                start=0
                while start<len(expanded):
                    if not re.fullmatch(r'\d+\s+DATA\s+%[01]{8}',expanded[start]):
                        start+=1
                        continue
                    end=start
                    while end+1<len(expanded) and re.fullmatch(r'\d+\s+DATA\s+%[01]{8}',expanded[end+1]):
                        end+=1
                    if end-start<8:
                        first=start+1
                        if start and re.match(r'\d+\s+REM\b',expanded[start-1]):
                            first=start
                        listing.setStyle(TableStyle([('NOSPLIT',(0,first),(-1,end+1))]))
                    start=end+1
                flow.extend([listing,Spacer(1,12)])
                continue
            code = Table([[code_flow('\n'.join(expanded), code_style)]], colWidths=[166*mm])
            code.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),
                                     ('LEFTPADDING',(0,0),(-1,-1),9),
                                     ('RIGHTPADDING',(0,0),(-1,-1),9),
                                     ('TOPPADDING',(0,0),(-1,-1),8),
                                     ('BOTTOMPADDING',(0,0),(-1,-1),8)]))
            flow.extend([code, Spacer(1, 12)])
        elif kind == 'block_quote':
            text = ' '.join(inline(t.get('children', []), source, pages) for t in token['children'])
            flow.append(Paragraph(text, styles['quote']))
        elif kind == 'list':
            ordered = token['attrs'].get('ordered', False)
            start = token['attrs'].get('start', 1)
            for n, item in enumerate(token['children'], start):
                text = ' '.join(inline(t.get('children', []), source, pages) for t in item['children'] if t['type'] != 'list')
                flow.append(Paragraph(('{}.'.format(n) if ordered else '-')+' '+text, styles['body']))
        elif kind == 'table':
            rows = []
            for part in token['children']:
                table_rows = [part] if part['type'] == 'table_head' else part['children']
                for row in table_rows:
                    rows.append([Paragraph(inline(cell['children'], source, pages), styles['small']) for cell in row['children']])
            count = len(rows[0])
            if count == 2:
                widths = [57*mm, 109*mm]
            elif count == 3:
                widths = [43*mm, 77*mm, 46*mm]
            elif count == 4:
                widths = [24*mm, 51*mm, 59*mm, 32*mm]
            else:
                widths = [166*mm/count]*count
            layout = config.get('table_layout', {}).get(source.name, {})
            custom_widths = layout.get('widths_mm', {}).get(str(count))
            if custom_widths:
                if len(custom_widths) != count or abs(sum(custom_widths)-166) > .01:
                    raise ValueError(f'Invalid table widths in {source.name}')
                widths = [w*mm for w in custom_widths]
            table = Table(rows, colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PALE),
                ('LINEBELOW', (0, 0), (-1, 0), .6, TEAL),
                ('LINEBELOW', (0, 1), (-1, -1), .25, colors.HexColor('#cbd6d0')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 7),
                ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), layout.get('top_padding',6)),
                ('BOTTOMPADDING', (0, 0), (-1, -1), layout.get('bottom_padding',5)),
            ]))
            flow.extend([table, Spacer(1, 9)])
        elif kind == 'thematic_break':
            flow.append(Spacer(1, 10))
        else:
            raise ValueError(f'Unsupported Markdown block {kind} in {source}')
    if pending:
        raise ValueError(f'Anchors without a heading: {pending}')
    return flow


def illustration_assets():
    folder = HERE / 'images'
    folder.mkdir(exist_ok=True)
    rows = [14,17,21,17,21,17,14]
    image = PILImage.new('RGB', (670, 315), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=23)
    for y, row in enumerate(rows):
        for x in range(5):
            p = (20+x*39, 15+y*39)
            draw.rectangle((*p,p[0]+33,p[1]+33), fill='#225651' if row&(16>>x) else '#eef4f2', outline='#aabbb4')
        draw.text((250, 18+y*39), f'%{row:05b}  = {row:2d}', fill='#172621', font=font)
    if not (folder/'lcd-sourire.png').exists():
        image.save(folder/'lcd-sourire.png')
    image = PILImage.new('RGB', (850, 345), 'white')
    draw = ImageDraw.Draw(image)
    for x in range(130, 791, 55):
        draw.line((x,55,x,300),fill='#d6e3df',width=1)
    for y in range(55,301,35):
        draw.line((130,y,790,y),fill='#d6e3df',width=1)
    draw.line((130,55,810,55),fill='#225651',width=3)
    draw.line((130,55,130,320),fill='#225651',width=3)
    draw.polygon([(810,55),(797,49),(797,61)],fill='#225651')
    draw.polygon([(130,320),(124,307),(136,307)],fill='#225651')
    for xy,label in [((40,20),'(0,0)'),((794,15),'X'),((85,310),'Y'),((220,82),'(20,20)')]:
        draw.text(xy,label,font=font,fill='#172621')
    draw.rectangle((240,125,460,265),outline='#225651',width=3)
    draw.ellipse((235,120,245,130),fill='#225651')
    if not (folder/'repere-graphique.png').exists():
        image.save(folder/'repere-graphique.png')


def collect(chapters):
    headings = []
    known = set()
    for path, tokens in chapters:
        known.add(path.name+'#')
        for token in tokens:
            known.update(path.name+'#'+a for a in anchors(token))
            if token['type'] == 'heading':
                level = token['attrs']['level']
                title = normalized(plain(token['children']))
                key = path.name+'#'+slug(title)
                if key in known:
                    raise ValueError(f'Duplicate heading {key}')
                known.add(key)
                if level <= 2 and not (path.name == '99-lexique.md' and level == 2):
                    headings.append((level, title, key))
    return headings, known


def build(config_path, output, pagination_seed=None):
    global NOTES
    config = json.loads(config_path.read_text(encoding='utf-8'))
    english=config.get('language')=='en'
    content_root=HERE/config.get('content_directory','.')
    def translated(fr,en):return en if english else fr
    if config.get('example_programs'):
        from write_selected_programs import write_chapter
        write_chapter(config)
    styles = setup_styles()
    NOTES=SourceNotes(config)
    illustration_assets()
    chapters = [(content_root/name, MD((content_root/name).read_text(encoding='utf-8'))) for name in config['chapters']]
    headings, known = collect(chapters)
    missing = set(config['symbols'].values()) - known
    if missing:
        raise ValueError(f'Unknown index destinations: {sorted(missing)}')
    output.parent.mkdir(parents=True, exist_ok=True)
    pages = {}
    note_reserves={}
    last_note_pages={}
    if pagination_seed is not None:
        seed=json.loads(pagination_seed.read_text(encoding='utf-8'))
        if (seed['version']!=config['version'] or seed['chapters']!=config['chapters']
                or seed.get('language',config.get('language'))!=config.get('language')):
            raise ValueError('Pagination seed must match the edition and firmware version')
        pages=seed['destinations']
        note_reserves={int(p):h for p,h in seed['note_reserves'].items()}
        last_note_pages={int(p):set(notes) for p,notes in seed['notes_by_page'].items()}
    for attempt in range(24):
        cover = HERE/config['cover_image']
        with PILImage.open(cover) as img:
            w,h=img.size
        scale=min(166*mm/w,143*mm/h)
        centered=ParagraphStyle('coverbody',parent=styles['body'],alignment=TA_CENTER)
        story = [Spacer(1, 7*mm), Paragraph(config['title'], styles['cover']),
                 Spacer(1, 4*mm), Paragraph(config['subtitle'], styles['subtitle']),
                 Spacer(1, 4*mm),Paragraph(translated('<b>Firmware non officiel / modification</b><br/>pour Canon Typestar 7 / S-70','<b>Unofficial firmware / modification</b><br/>for Canon Typestar 7 / S-70'),centered),
                 Spacer(1, 6*mm), Image(str(cover),width=w*scale,height=h*scale,mask='auto'),
                 Spacer(1, 6*mm), Paragraph(translated('Installation, programmation et jeux - édition française','Installation, programming and games - English edition'), centered),
                 Paragraph(translated('Version de référence : ','Reference version: ')+config['version'], centered),
                 Paragraph(config['author']+' - '+config['date'], centered),
                 Paragraph(translated('<i>Projet indépendant de Canon. Édition de travail.</i>','<i>Independent project, unaffiliated with Canon. Working edition.</i>'),centered)]
        front=set(config.get('front_chapters',[]))
        for source,tokens in chapters:
            if source.name in front:
                story.append(PageBreak())
                story.extend(chapter(tokens,source,styles,pages,config))
        story.extend([PageBreak(), Paragraph(translated('Sommaire','Contents'), styles['h1']),
                      Paragraph(translated('Commencez par les premiers essais, puis retrouvez une fonction dans l’index en fin de volume. Les numéros et les liens suivent automatiquement cette édition.','Start with the first experiments, then use the index at the back to find a function. Page numbers and links update automatically for this edition.'),styles['body'])])
        for level, title, key in headings:
            if level > config.get('toc_max_level',2):
                continue
            label = ('&nbsp;&nbsp;&nbsp;&nbsp;' if level == 2 else '') + html.escape(title)
            text = f'<link href="#{key}">{label}</link>' if key in pages else label
            t = Table([[Paragraph(text, styles['toc']), str(pages.get(key, '...'))]],
                      colWidths=[155*mm,11*mm])
            t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),
                                  ('RIGHTPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),2),
                                  ('FONTNAME',(0,0),(-1,-1),'Body'),('FONTSIZE',(0,0),(-1,-1),10.2)]))
            story.append(t)
        index_target='index-commandes.md#'
        index_title=translated('Index des commandes et fonctions','Command and function index')
        index_text=f'<link href="#{index_target}">{index_title}</link>' if index_target in pages else index_title
        index_row=Table([[Paragraph(index_text,styles['toc']),str(pages.get(index_target,'...'))]],colWidths=[155*mm,11*mm])
        index_row.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('FONTNAME',(0,0),(-1,-1),'Body'),('FONTSIZE',(0,0),(-1,-1),10.2)]))
        story.append(index_row)
        for source, tokens in chapters:
            if source.name in front:
                continue
            story.append(PageBreak())
            story.extend(chapter(tokens, source, styles, pages, config))
        index_heading=Paragraph(index_title,styles['h1'])
        index_heading.manual_keys=[index_target]
        index_heading.outline=(index_title,index_target,0)
        story.extend([PageBreak(), index_heading,
                      Paragraph(translated('Chaque numéro renvoie à la leçon principale. Les opérateurs et leurs priorités sont expliqués au chapitre 4 ; AND, OR, NOT et MOD sont également présentés au chapitre 5.','Each page number leads to the main lesson. Chapter 4 explains operators and precedence; chapter 5 also introduces AND, OR, NOT and MOD.'), styles['body'])])
        symbols = sorted(config['symbols'].items(), key=lambda item: item[0])
        rows = []
        for i in range(0, len(symbols), 3):
            row = []
            for name, target in symbols[i:i+3]:
                text = f'<b>{html.escape(name)}</b> - {pages.get(target, "...")}'
                if target in pages:
                    text = f'<link href="#{target}">{text}</link>'
                row.append(Paragraph(text, styles['index']))
            rows.append(row+['']*(3-len(row)))
        table = Table(rows, colWidths=[166*mm/3]*3, hAlign='LEFT')
        table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),3),
                                  ('BOTTOMPADDING',(0,0),(-1,-1),3),('ROWBACKGROUNDS',(0,0),(-1,-1),[PALE,colors.white])]))
        story.append(table)
        doc = ManualDoc(output, config, note_reserves)
        doc.build(story)
        new_reserves=dict(note_reserves)
        for page,numbers in doc.note_pages.items():
            new_reserves[page]=max(new_reserves.get(page,0),NOTES.height(numbers,doc.width)+8)
        print(f'Pagination {attempt+1}: {doc.total_pages} pages',flush=True)
        if pages == doc.page_map and last_note_pages == doc.note_pages and new_reserves==note_reserves:
            break
        pages = doc.page_map
        last_note_pages=doc.note_pages
        note_reserves=new_reserves
    else:
        raise RuntimeError('Pagination did not converge')
    report = dict(version=config['version'], language=config.get('language'), pages=doc.total_pages, passes=attempt+1,
                  chapters=config['chapters'], symbols=config['symbols'], destinations=pages,
                  source_notes=NOTES.entries,
                  notes_by_page={str(p):sorted(n) for p,n in doc.note_pages.items()},
                  note_reserves=note_reserves)
    output.with_suffix('.pages.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    index_md = ['# '+index_title, '',
                translated('Liens vers les leçons. Les numéros de page sont calculés dans le PDF, jamais inscrits à la main dans ce fichier.','Links to the lessons. Page numbers are calculated in the PDF rather than entered manually here.'), '',
                translated('| Mot-clé | Leçon |','| Keyword | Lesson |'), '|---|---|']
    index_md += [f'| `{name}` | [{translated("Consulter","Read")}]({target}) |' for name,target in symbols]
    (content_root/'index-commandes.md').write_text('\n'.join(index_md)+'\n',encoding='utf-8')
    print(json.dumps(dict(pdf=str(output), pages=doc.total_pages, passes=attempt+1, indexed_symbols=len(symbols)), ensure_ascii=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=HERE/'manuel-fr.json')
    parser.add_argument('--output', type=Path, default=ROOT/'output/pdf/typestar-basic-manuel-fr.pdf')
    parser.add_argument('--pagination-seed',type=Path,help='Reuse a verified page map for a small copy-edit; all destinations are recalculated')
    args = parser.parse_args()
    build(args.config.resolve(), args.output.resolve(),args.pagination_seed)
