"""Qt widgets without serial or firmware side effects."""
import re
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QColor, QPainter, QTextCharFormat, QSyntaxHighlighter, QFont, QFontDatabase
from PySide6.QtWidgets import QWidget, QPlainTextEdit
from core import KEYWORDS

class BasicHighlighter(QSyntaxHighlighter):
    dark = False
    byte_font = None

    def __init__(self, document):
        super().__init__(document)
        if BasicHighlighter.byte_font is None:
            handle=QFontDatabase.addApplicationFont(str(Path(__file__).parent/'assets/typestar-bytes.ttf'))
            families=QFontDatabase.applicationFontFamilies(handle)
            BasicHighlighter.byte_font=families[0] if families else ''

    def highlightBlock(self, text):
        def style(a, n, color, bold=False):
            fmt = QTextCharFormat()
            colors = {'#748171':'#a1b59a', '#9f4d27':'#edb17f', '#2855ad':'#8cbeff', '#7755a2':'#d1a6ff', '#748595':'#99a7ba'}
            fmt.setForeground(QColor(colors.get(color, color) if self.dark else color))
            if bold:
                fmt.setFontWeight(QFont.Weight.Bold)
            self.setFormat(a, n, fmt)
        # Consume strings and REM as units, so keywords inside them stay literal.
        pattern = r'"[^"\n]*(?:"|$)|[A-Za-z][A-Za-z0-9$]*|%[01]+|&H[0-9A-Fa-f]+|\d+(?:\.\d+)?|[+*/^=<>:-]'
        for m in re.finditer(pattern, text):
            value = m[0]
            if value.upper() == 'REM':
                style(m.start(), len(text)-m.start(), '#748171')
                break
            if value.startswith('"'):
                style(m.start(), len(value), '#9f4d27')
            elif value.upper() in KEYWORDS:
                style(m.start(), len(value), '#2855ad', True)
            elif value[0].isdigit() or value.startswith(('%', '&')):
                style(m.start(), len(value), '#7755a2')
        m = re.match(r'\s*\d+', text)
        if m:
            style(0, m.end(), '#748595')
        # These characters round-trip as single native bytes. Change only
        # their appearance: replacing the document with '\\xNN' would expand
        # DATA strings and break packed maps, offsets and the 63-byte limit.
        for m in re.finditer('[\ue080-\ue0ff]',text):
            fmt=self.format(m.start())
            if self.byte_font:fmt.setFontFamilies([self.byte_font])
            fmt.setFontWeight(QFont.Weight.Normal)
            fmt.setToolTip(f'Byte / octet ${ord(m[0])-0xe000:02X}')
            self.setFormat(m.start(),1,fmt)

class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setFont(QFont('Consolas', 12))
        self.setPlaceholderText('10 PRINT "BONJOUR TYPESTAR"\n20 END')
        self.highlighter = BasicHighlighter(self.document())

class PixelGrid(QWidget):
    changed = Signal()

    def __init__(self, width=5, height=7):
        super().__init__()
        self.pixels = [[0]*width for _ in range(height)]
        self.setMinimumSize(170, 145 if height > 1 else 30)
        self.paint_value = 1
        self.drawing = False

    def set_pixels(self, pixels):
        self.pixels = [list(map(int, r)) for r in pixels]
        self.update()
        self.changed.emit()

    def geometry_grid(self):
        h, w = len(self.pixels), len(self.pixels[0])
        cell = min((self.width()-12)/w, (self.height()-12)/h, 34)
        return cell, (self.width()-cell*w)/2, (self.height()-cell*h)/2

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#e5e9df'))
        cell, left, top = self.geometry_grid()
        p.setPen(QColor('#abb8a4'))
        for y, row in enumerate(self.pixels):
            for x, value in enumerate(row):
                p.setBrush(QColor('#243f37' if value else '#d8e1ca'))
                p.drawRect(QRectF(left+x*cell, top+y*cell, cell, cell))

    def hit(self, pos):
        cell, left, top = self.geometry_grid()
        x, y = int((pos.x()-left)//cell), int((pos.y()-top)//cell)
        if 0 <= y < len(self.pixels) and 0 <= x < len(self.pixels[0]):
            return x, y

    def mark(self, pos):
        point = self.hit(pos)
        if point:
            x, y = point
            if self.pixels[y][x] != self.paint_value:
                self.pixels[y][x] = self.paint_value
                self.update()
                self.changed.emit()

    def mousePressEvent(self, event):
        point = self.hit(event.position())
        if point and event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            x, y = point
            self.paint_value = 0 if event.button() == Qt.MouseButton.RightButton else 1-self.pixels[y][x]
            self.drawing = True
            self.mark(event.position())

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.mark(event.position())

    def mouseReleaseEvent(self, event):
        self.drawing = False

class LcdPreview(QWidget):
    """Preview of a custom glyph only; no claim to emulate the native CGROM."""
    def __init__(self, glyph, triangle, lower):
        super().__init__()
        self.glyph, self.triangle, self.lower = glyph, triangle, lower
        self.setMinimumHeight(95)
        for grid in (glyph, triangle, lower):
            grid.changed.connect(self.update)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#c9d2aa'))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#324738'))
        rows = self.glyph.pixels
        if len(rows) != 7 or len(rows[0]) != 5:
            return
        left, top, size = (self.width()-45)/2, 6, 8
        for y, row in enumerate(rows):
            for x, value in enumerate(row):
                if value:
                    p.drawRect(QRectF(left+x*9, top+y*9, size, size))
        # Triangle columns are distinct from the seven text rows.
        for x, value in enumerate(self.triangle.pixels[0]):
            if value:
                p.drawRect(QRectF(left+x*9, 80-(x+1)*2, size, (x+1)*2))
        for x, value in enumerate(self.lower.pixels[0]):
            if value:
                p.drawRect(QRectF(left+x*9, 85, size, 3))
