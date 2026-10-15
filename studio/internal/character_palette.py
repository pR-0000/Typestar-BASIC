from pathlib import Path
from i18n import tr
"""Native LCD palette: insert explicit CHR$ expressions, not guessed Unicode."""
import json
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QImage,QPainter,QColor,QPixmap,QIcon
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QListWidget,QListWidgetItem,QPushButton
from core import ROOT

class CharacterPalette(QWidget):
    def __init__(self,insert):
        super().__init__();layout=QVBoxLayout(self)
        layout.addWidget(QLabel(tr('Police LCD Canon — sélectionner puis insérer CHR$(code).')))
        self.list=QListWidget();self.list.setViewMode(QListWidget.ViewMode.IconMode)
        self.list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list.setGridSize(QSize(72,85));self.list.setIconSize(QSize(40,56))
        rows=json.loads((Path(__file__).parent/'assets/lcd-font.json').read_text(encoding='utf-8'))['rows']
        for code in range(256):
            image=QImage(40,56,QImage.Format.Format_RGB32);image.fill(QColor('#c9d2aa'))
            painter=QPainter(image)
            for y,value in enumerate(rows.get(f'{code:02X}',[0]*7)[:7]):
                for x in range(5):
                    if value&(1<<(4-x)):painter.fillRect(x*8,y*8,7,7,QColor('#34443a'))
            painter.end()
            item=QListWidgetItem(QIcon(QPixmap.fromImage(image)),f'{code} / ${code:02X}')
            item.setData(Qt.ItemDataRole.UserRole,code)
            item.setToolTip(tr('CGRAM : motif variable') if code<16 else tr('Vide/réservé') if code<32 else f'CHR$({code})')
            self.list.addItem(item)
        layout.addWidget(self.list)
        def choose():
            item=self.list.currentItem()
            if item:insert(f"CHR$({item.data(Qt.ItemDataRole.UserRole)})")
        button=QPushButton(tr('Insérer l’expression au curseur'));button.clicked.connect(choose)
        layout.addWidget(button);self.list.itemDoubleClicked.connect(lambda _:choose())
        layout.addWidget(QLabel(tr('0–15 : glyphes personnalisés/alias. Insérer hors des guillemets, par exemple PRINT CHR$(160).')))
