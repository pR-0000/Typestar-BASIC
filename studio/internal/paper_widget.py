from i18n import tr
"""Scrollable virtual paper and local image/PDF export."""
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QImage,QPixmap,QPainter,QPdfWriter,QPageSize
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QScrollArea,QComboBox,QPushButton,QFileDialog,QMessageBox,QCheckBox
from paper import PaperRaster

def qimage(image):
    gray=image.convert('L');data=gray.tobytes()
    return QImage(data,gray.width,gray.height,gray.width,QImage.Format.Format_Grayscale8).copy()

class PaperPanel(QWidget):
    def __init__(self):
        super().__init__();self.raster=PaperRaster();layout=QVBoxLayout(self)
        layout.setContentsMargins(4,4,4,4);layout.setSpacing(3)
        row=QHBoxLayout();self.zoom=QComboBox();self.zoom.addItems(['25 %','50 %','100 %','200 %'])
        row.setSpacing(4)
        self.zoom.currentIndexChanged.connect(self.refresh);row.addWidget(self.zoom)
        self.follow=QCheckBox(tr('Suivre l’impression'));self.follow.setChecked(True);row.addWidget(self.follow)
        for title,fn in [(tr('Effacer l’aperçu'),self.clear),('PNG…',self.save_png),('PDF…',self.save_pdf)]:
            button=QPushButton(title);button.clicked.connect(fn);row.addWidget(button)
        layout.addLayout(row)
        self.status=QLabel();layout.addWidget(self.status)
        self.scroll=QScrollArea();self.sheet=QLabel();self.scroll.setWidget(self.sheet)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.scroll,1);self.refresh()
    def clear(self):
        self.raster.clear();self.refresh()
    def add(self,events):
        self.raster.add(events)
        if self.isVisible():self.refresh()
    def showEvent(self,event):
        super().showEvent(event);self.refresh()
    def refresh(self,*_):
        y=self.scroll.verticalScrollBar().value();x=self.scroll.horizontalScrollBar().value()
        scale=(.25,.5,1,2)[self.zoom.currentIndex()]
        image=qimage(self.raster.output())
        pix=QPixmap.fromImage(image).scaled(round(image.width()*scale),round(image.height()*scale),Qt.AspectRatioMode.IgnoreAspectRatio,Qt.TransformationMode.FastTransformation)
        self.sheet.setPixmap(pix);self.sheet.resize(pix.size())
        self.scroll.horizontalScrollBar().setValue(x)
        if self.follow.isChecked():
            self.scroll.verticalScrollBar().setValue(max(0,round(self.raster.bottom*scale)-self.scroll.viewport().height()+40))
        else:self.scroll.verticalScrollBar().setValue(y)
        self.status.setText((f'{self.raster.columns}' + tr(' colonnes marquées'))+((' — ' + f'{self.raster.clipped}' + tr(' hors aperçu (limite 2560 × 12000)')) if self.raster.clipped else ''))
    def save_png(self):
        name,_=QFileDialog.getSaveFileName(self,tr('Exporter le papier'),'typestar-paper.png','PNG (*.png)')
        if name:
            try:self.raster.output().save(name,format='PNG')
            except OSError as exc:QMessageBox.warning(self,'Export',str(exc))
    def export_pdf(self,name):
        writer=QPdfWriter(name);writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4));writer.setResolution(150)
        painter=QPainter()
        if not painter.begin(writer):raise OSError(tr('Impossible de créer le PDF.'))
        try:
            source=self.raster.output();width=writer.width();height=writer.height()
            band=max(1,int(height*source.width/width))
            for top in range(0,source.height,band):
                if top and not writer.newPage():raise OSError(tr('Impossible d’ajouter une page PDF.'))
                image=qimage(source.crop((0,top,source.width,min(source.height,top+band))))
                painter.drawImage(QRectF(0,0,width,image.height()*width/source.width),image)
        finally:painter.end()
    def save_pdf(self):
        name,_=QFileDialog.getSaveFileName(self,tr('Exporter le papier'),'typestar-paper.pdf','PDF (*.pdf)')
        if name:
            try:self.export_pdf(name)
            except OSError as exc:QMessageBox.warning(self,'Export',str(exc))
