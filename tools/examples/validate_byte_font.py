"""Headless Studio checks: legible byte glyphs and untouched source text."""
from pathlib import Path
import hashlib
import json
import os
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools')]
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase,QFont,QRawFont,QTextCursor
from widgets import CodeEditor
from core import analyze,codec


def main():
    app=QApplication([])
    # Windows' offscreen plugin does not enumerate installed desktop fonts.
    for name in ('consola.ttf','consolab.ttf'):
        p=Path('C:/Windows/Fonts')/name
        if p.exists():QFontDatabase.addApplicationFont(str(p))
    e=CodeEditor();font=QRawFont.fromFont(QFont(e.highlighter.byte_font,12))
    assert all(font.supportsCharacter(v) for v in range(0xe080,0xe100))
    results=[]
    for name in ('canon-s70-quest-fr.bas','canon-s70-quest-en.bas','ruines-typestar-fr.bas','typestar-ruins-en.bas'):
        p=ROOT/'examples/games'/name;source=p.read_text(encoding='utf-8')
        e.setPlainText(source);e.document().setModified(False)
        for dark in (False,True):
            e.highlighter.dark=dark;e.highlighter.rehighlight();app.processEvents()
            assert e.toPlainText()==source and not e.document().isModified()
        cursor=e.textCursor();cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.End,QTextCursor.MoveMode.KeepAnchor)
        assert cursor.selectedText().replace('\u2029','\n')==source
        a=analyze(e.toPlainText());assert not a.issues,a.issues
        assert codec.unpack(codec.pack(a.records))==a.records
        results.append(dict(source=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=a.used))
    e.setPlainText((ROOT/'examples/games/canon-s70-quest-fr.bas').read_text(encoding='utf-8'))
    e.resize(1200,310);e.show()
    folder=ROOT/'build/paper-games';folder.mkdir(exist_ok=True)
    for dark in (False,True):
        e.highlighter.dark=dark;e.setStyleSheet('QPlainTextEdit {background:#20242a;color:#e4e6ea;}' if dark else '')
        e.highlighter.rehighlight();app.processEvents()
        e.grab().save(str(folder/('editor-'+('dark' if dark else 'light')+'.png')))
    (folder/'byte-font-validation.json').write_text(json.dumps(dict(result='PASS',glyphs=128,cases=results),indent=2)+'\n')
    print('PASS: 128 byte badges, four packed programs, both themes, source/selection/codec unchanged')


if __name__=='__main__':main()
