from i18n import tr, set_language, language
"""Typestar BASIC Studio — desktop front end for the existing host tools."""
import json
import os
from pathlib import Path
import sys
import tempfile

from PySide6.QtCore import Qt, QProcess, QProcessEnvironment, QSettings, QStandardPaths, QTimer
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QPixmap, QImage, QTextCursor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QFormLayout, QSplitter, QTabWidget, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QPlainTextEdit,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QProgressBar, QInputDialog)

from core import ROOT, VERSION, BAUD_RATES, analyze, export_sprite, save_asset, load_asset
from widgets import CodeEditor, PixelGrid, LcdPreview
from themes import apply_theme
from emulator import EmulatorPanel, worker_python
from print_image import prepare_image

def button(text, callback):
    b = QPushButton(text)
    b.clicked.connect(lambda: callback())
    return b

def spin(low, high, value):
    s = QSpinBox()
    s.setRange(low, high)
    s.setValue(value)
    return s

def row(*widgets):
    w = QWidget()
    layout = QHBoxLayout(w)
    layout.setContentsMargins(0, 0, 0, 0)
    for widget in widgets:
        layout.addWidget(widget)
    return w

def label(text):
    w = QLabel(text)
    w.setWordWrap(True)
    return w

class Studio(QMainWindow):
    def __init__(self, settings_path=None):
        super().__init__()
        self.path = None
        self.asset_dirty = False
        self.process = None
        self.job_temp = None
        self.cancelled = False
        self.image_path = None
        self.mono = None
        self.receive_path = None
        self.image_signature = None
        settings_path = settings_path or os.environ.get('TYPESTAR_STUDIO_SETTINGS')
        if not settings_path:
            settings_path = str(Path(QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppConfigLocation)) / 'studio.ini')
        Path(settings_path).parent.mkdir(parents=True, exist_ok=True)
        self.settings = QSettings(settings_path, QSettings.Format.IniFormat)
        set_language(str(self.settings.value("appearance/language", "en")))
        self.resize(1380, 920)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(split, 1)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 5, 0)
        self.editor = CodeEditor()
        ll.addWidget(self.editor, 1)
        self.metrics = label('')
        ll.addWidget(self.metrics)
        self.issues = QListWidget()
        self.issues.setMaximumHeight(92)
        self.issues.itemClicked.connect(self.jump_issue)
        ll.addWidget(self.issues)
        split.addWidget(left)
        tabs = self.tabs = QTabWidget()
        self.emulator = EmulatorPanel(self.editor.toPlainText,self.settings)
        tabs.addTab(self.emulator, tr("Émulateur"))
        self.glyph_tab=self.sprite_tab()
        tabs.addTab(self.glyph_tab, tr('Glyphes'))
        from character_palette import CharacterPalette
        tabs.addTab(CharacterPalette(self.insert_character),tr('Caractères'))
        tabs.addTab(self.image_tab(), tr('Impression graphique'))
        help_tab = QWidget()
        hl = QVBoxLayout(help_tab)
        hl.addWidget(label(tr('Premiers pas\n\n1. Ouvrir un exemple ou écrire des lignes numérotées.\n'
            '2. Vérifier les limites puis choisir le port série.\n'
            '3. Envoyer, puis taper LOAD sur la Canon.\n\n'
            'La vérification couvre le format et la taille ; elle ne valide pas toute la syntaxe BASIC. '
            'La mémoire restante devra aussi contenir les variables et les buffers d’impression.\n\n'
            'Le dessin LCD est un aperçu de caractère personnalisé, pas une émulation. '
            'L’onglet Émulateur exécute le firmware BASIC avec des périphériques simulés.')))
        hl.addWidget(button(tr('Ouvrir un exemple…'), lambda: self.open(ROOT/'examples')))
        hl.addWidget(button(tr('Ouvrir le guide du Studio'), self.guide))
        hl.addStretch()
        tabs.addTab(help_tab, 'Guide')
        split.addWidget(tabs)
        split.setSizes([730, 610])
        self.port = QComboBox()
        self.port.setEditable(True)
        self.port.setMinimumWidth(300)
        self.baud = QComboBox()
        self.baud.addItems(list(map(str, BAUD_RATES)))
        self.baud.setCurrentText(str(self.settings.value('serial/baud', '31250')))
        self.parity = QComboBox()
        self.parity.addItems(['E', 'N', 'O'])
        self.parity.setCurrentText(str(self.settings.value('serial/parity', 'E')))
        self.stops = QComboBox()
        self.stops.addItems(['1', '2'])
        self.stops.setCurrentText(str(self.settings.value('serial/stops', '1')))
        self.refresh_ports()
        self.select_port(str(self.settings.value('serial/port', '')))
        self.send_button = button(tr('Envoyer → LOAD'), self.send)
        self.receive_button = button(tr('Recevoir ← SAVE'), self.receive)
        self.stop_button = button(tr('Annuler'), self.cancel)
        self.stop_button.setEnabled(False)
        layout.addWidget(row(QLabel('Port'), self.port, button(tr('Actualiser'), self.refresh_ports),
            QLabel('Baud'), self.baud, QLabel(tr('7 bits / parité')), self.parity,
            QLabel('Stop'), self.stops, self.send_button, self.receive_button, self.stop_button))
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setMaximumHeight(5)
        layout.addWidget(self.progress)
        self.job_status = label(tr('Prêt. Aucun port ouvert. Réglage Canon et PC : mêmes BAUD et SERCFG.'))
        layout.addWidget(self.job_status)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(1000)
        self.log.setMaximumHeight(110)
        layout.addWidget(self.log)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.check)
        self.editor.textChanged.connect(lambda: self.timer.start())
        self.editor.document().modificationChanged.connect(self.update_title)
        self.create_menus()
        self.theme_mode = str(self.settings.value('appearance/theme', 'system'))
        if self.theme_mode not in self.theme_actions:
            self.theme_mode = 'system'
        self.theme_actions[self.theme_mode].setChecked(True)
        self.set_theme(self.theme_mode)
        QApplication.instance().styleHints().colorSchemeChanged.connect(self.system_theme_changed)
        self.editor.setPlainText('10 CLS\n20 PRINT "HELLO TYPESTAR";\n' if language() == 'en' else '10 CLS\n20 PRINT "BONJOUR TYPESTAR";\n')
        self.editor.document().setModified(False)
        self.update_title()
        self.check()
        self.target_controls()
        self.generate()

    def create_menus(self):
        def action(menu, text, fn, shortcut=None):
            a = QAction(text, self)
            if shortcut: a.setShortcut(QKeySequence(shortcut))
            a.triggered.connect(lambda checked=False: fn())
            menu.addAction(a)
            return a
        files = self.menuBar().addMenu(tr('&Fichier'))
        for name, fn, key in [(tr('Nouveau'), self.new, 'Ctrl+N'), (tr('Ouvrir…'), self.open, 'Ctrl+O'),
                             (tr('Enregistrer'), self.save, 'Ctrl+S'),
                             (tr('Enregistrer sous…'), lambda: self.save(True), 'Ctrl+Shift+S')]:
            action(files, name, fn, key)
        files.addSeparator()
        action(files, tr('Quitter'), self.close, 'Ctrl+Q')
        edit = self.menuBar().addMenu(tr('&Édition'))
        # Qt text widgets retain their native Undo/Cut/Copy/Paste shortcuts.
        for name, method in [(tr('Annuler l’action'), 'undo'), (tr('Rétablir'), 'redo'), (tr('Couper'), 'cut'),
                             (tr('Copier'), 'copy'), (tr('Coller'), 'paste'), (tr('Tout sélectionner'), 'selectAll')]:
            action(edit, name, lambda m=method: getattr(QApplication.focusWidget(), m, lambda: None)())
        edit.addSeparator()
        action(edit, tr('Rechercher dans le programme…'), self.find_text, 'Ctrl+F')
        program = self.menuBar().addMenu(tr('&Programme'))
        action(program, tr('Vérifier les limites'), self.check, 'F4')
        action(program, tr('Envoyer à la Canon (LOAD)…'), self.send)
        action(program, tr('Recevoir de la Canon (SAVE)…'), self.receive)
        emu = self.menuBar().addMenu(tr('É&mulation'))
        def run():
            self.tabs.setCurrentWidget(self.emulator)
            self.emulator.run_editor()
        action(emu, tr('Exécuter le programme de l’éditeur'), run, 'F5')
        action(emu, tr('Pause / reprise'), self.emulator.pause, 'F6')
        action(emu, 'BREAK', lambda: self.emulator.send_key(3))
        action(emu, tr('Choisir les ROM…'), self.emulator.choose_roms)
        action(emu, tr('Réinitialiser la machine virtuelle'), self.emulator.reset)
        action(emu, tr('Arrêter (figer)'), self.emulator.stop)
        action(emu, tr('Allumer'), self.emulator.power_on)
        action(emu, tr('Éteindre'), self.emulator.power_off)
        self.sound_action = action(emu, tr('Son du buzzer'), self.toggle_sound)
        self.sound_action.setCheckable(True)
        enabled=str(self.settings.value('emulator/sound','true')).lower()=='true'
        self.sound_action.setChecked(enabled)
        self.emulator.audio.enabled=enabled
        view = self.menuBar().addMenu(tr('&Affichage'))
        themes = view.addMenu(tr('Thème'))
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_actions = {}
        for mode, title in [('system',tr('Suivre le système')), ('light',tr('Clair')), ('dark',tr('Sombre'))]:
            a = action(themes, title, lambda m=mode: self.set_theme(m))
            a.setCheckable(True)
            self.theme_group.addAction(a)
            self.theme_actions[mode] = a
        pixels = view.addMenu(tr('Pixels LCD'))
        self.pixel_group = QActionGroup(self)
        self.pixel_group.setExclusive(True)
        self.pixel_actions = {}
        for mode, title in [('spaced',tr('Légèrement espacés')), ('solid',tr('Jointifs'))]:
            a = action(pixels, title, lambda m=mode: self.set_lcd_pixels(m))
            a.setCheckable(True)
            self.pixel_group.addAction(a)
            self.pixel_actions[mode] = a
        mode = str(self.settings.value('appearance/lcd_pixels','spaced'))
        self.set_lcd_pixels(mode if mode in self.pixel_actions else 'spaced')
        settings_menu = self.menuBar().addMenu(tr('&Paramètres'))
        languages = settings_menu.addMenu(tr('Langue'))
        self.language_group = QActionGroup(self)
        self.language_group.setExclusive(True)
        self.language_actions = {}
        for code, title in [('en', 'English'), ('fr', 'Français')]:
            a = action(languages, title, lambda c=code: self.select_language(c))
            a.setCheckable(True)
            a.setChecked(code == language())
            self.language_group.addAction(a)
            self.language_actions[code] = a
        help_menu = self.menuBar().addMenu(tr('&Aide'))
        action(help_menu, tr('Guide du Studio'), self.guide, 'F1')
        action(help_menu, tr('À propos'), lambda: QMessageBox.about(self, 'Typestar BASIC Studio',
            ('Typestar BASIC Studio ' + f'{VERSION}' + tr('\nPierre Raimbault\nFirmware de référence : 0.4.85-dev'))))

    def select_language(self, code):
        self.settings.setValue('appearance/language', code)
        self.settings.sync()
        self.language_actions[code].setChecked(True)
        if code != language():
            QMessageBox.information(self, 'Language / Langue',
                'Language saved. Restart Studio to apply it.\nLangue enregistrée. Redémarrez Studio pour l’appliquer.')

    def toggle_sound(self):
        enabled=self.sound_action.isChecked()
        self.emulator.audio.enabled=enabled
        if not enabled:self.emulator.audio.stop()
        self.settings.setValue('emulator/sound',str(enabled).lower())

    def set_lcd_pixels(self, mode):
        self.pixel_actions[mode].setChecked(True)
        self.emulator.lcd.set_spaced(mode == 'spaced')
        self.settings.setValue('appearance/lcd_pixels',mode)

    def set_theme(self, mode):
        self.theme_mode = mode
        self.theme_actions[mode].setChecked(True)
        apply_theme(mode, self.editor.highlighter)
        self.settings.setValue('appearance/theme', mode)

    def system_theme_changed(self, *_):
        if self.theme_mode == 'system':
            apply_theme('system', self.editor.highlighter)

    def update_title(self, *_):
        title = f'Typestar BASIC Studio {VERSION}'
        if self.path:
            title = f'{self.path.name} — {title}'
        if self.editor.document().isModified():
            title = '* ' + title
        self.setWindowTitle(title)

    def error(self, exc):
        QMessageBox.warning(self, 'Typestar BASIC Studio', str(exc))

    def confirm_editor(self):
        if not self.editor.document().isModified():
            return True
        result = QMessageBox.question(self, tr('Programme modifié'), tr('Enregistrer les modifications ?'),
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        return self.save() if result == QMessageBox.StandardButton.Save else result == QMessageBox.StandardButton.Discard

    def new(self):
        if self.confirm_editor():
            self.path = None
            self.editor.clear()
            self.editor.document().setModified(False)
            self.update_title()

    def find_text(self):
        text, accepted = QInputDialog.getText(self, tr('Rechercher'), tr('Texte :'))
        if accepted and text and not self.editor.find(text):
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            if not self.editor.find(text):
                self.error(tr('Texte introuvable.'))

    def open(self, directory=None):
        if not self.confirm_editor():
            return
        path, _ = QFileDialog.getOpenFileName(self, tr('Ouvrir un programme'), str(directory or self.path or ROOT/'examples'), tr('BASIC (*.bas);;Tous (*)'))
        if path:
            try:
                text = Path(path).read_text(encoding='utf-8-sig')
                self.editor.setPlainText(text)
                self.path = Path(path)
                self.editor.document().setModified(False)
                self.update_title()
            except (OSError, UnicodeError) as exc:
                self.error(exc)

    def save(self, save_as=False):
        path = self.path
        if save_as or not path:
            name, _ = QFileDialog.getSaveFileName(self, tr('Enregistrer le programme'), str(path or ROOT/'examples/mon-programme.bas'), 'BASIC (*.bas)')
            if not name:
                return False
            path = Path(name)
        try:
            self.atomic_write(path, self.editor.toPlainText().encode('utf-8'))
            self.path = path
            self.editor.document().setModified(False)
            self.update_title()
            return True
        except OSError as exc:
            self.error(exc)
            return False

    @staticmethod
    def atomic_write(path, data):
        path = Path(path)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
            temp = Path(f.name)
            f.write(data)
        try:
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)

    def check(self):
        result = analyze(self.editor.toPlainText())
        self.issues.clear()
        for line, issue in result.issues:
            item = QListWidgetItem((f'{(tr('Ligne éditeur ') + str(line) + ' : ' if line else '')}' + f'{issue}'))
            item.setData(Qt.ItemDataRole.UserRole, line)
            self.issues.addItem(item)
        if result.used is None:
            self.metrics.setText(tr('Format à corriger avant transfert. Cliquer un diagnostic pour rejoindre la ligne.'))
        else:
            self.metrics.setText((f'{len(result.records)}' + tr(' lignes • ') + f'{result.used}' + tr(' octets tokenisés • ') + f'{result.free}' + tr(' octets restent pour les variables et buffers.\nFormat vérifié pour .80 ; syntaxe et comportement à tester sur la Canon.')))
        return result

    def jump_issue(self, item):
        line = item.data(Qt.ItemDataRole.UserRole)
        if line:
            block = self.editor.document().findBlockByNumber(line-1)
            self.editor.setTextCursor(QTextCursor(block))
            self.editor.setFocus()

    def sprite_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.kind = QComboBox()
        for kind in ('LCD', 'Papier'): self.kind.addItem(tr(kind), kind)
        self.preset = QComboBox()
        self.preset.addItems(['16 × 16', '16 × 8', '31 × 16'])
        self.preset.setEnabled(False)
        layout.addWidget(row(QLabel(tr('Cible')), self.kind, QLabel(tr('Papier')), self.preset))
        self.grid = PixelGrid()
        layout.addWidget(self.grid, 1)
        self.triangle, self.lower = PixelGrid(5, 1), PixelGrid(5, 1)
        self.triangle.setMaximumHeight(38)
        self.lower.setMaximumHeight(38)
        self.extras = row(QLabel('Triangle'), self.triangle, QLabel(tr('Ligne basse')), self.lower)
        layout.addWidget(self.extras)
        self.lcd_preview = LcdPreview(self.grid, self.triangle, self.lower)
        layout.addWidget(self.lcd_preview)
        layout.addWidget(row(button(tr('Effacer'), self.clear_grid),
            button(tr('Miroir ↔'), lambda: self.grid.set_pixels([r[::-1] for r in self.grid.pixels])),
            button(tr('Miroir ↕'), lambda: self.grid.set_pixels(self.grid.pixels[::-1])),
            button(tr('Importer image…'), self.import_sprite)))
        layout.addWidget(row(button(tr('Ouvrir sprite…'), self.open_asset), button(tr('Enregistrer sprite…'), self.save_asset),button(tr('Depuis le BASIC'),self.import_basic_glyph)))
        self.position = spin(1, 32, 1)
        self.zoom = spin(1, 3, 3)
        self.zoom.setToolTip(tr("1 : pixels natifs ; 2 : zoom ×2 ; 3 : pixels carrés (largeur ×2)."))
        self.array = QComboBox()
        self.array.addItems(list('ZABCDEFGHIJKLMNOPQRSTUVWXY'))
        self.base = QComboBox()
        for base in ('Binaire', 'Hexadécimal', 'Décimal'): self.base.addItem(tr(base), base)
        self.first, self.increment = spin(1, 65535, 1000), spin(1, 1000, 10)
        layout.addWidget(row(QLabel(tr('LCD position')), self.position, QLabel(tr('Tableau')), self.array, QLabel(tr('Mode papier')), self.zoom))
        layout.addWidget(row(self.base, QLabel(tr('Ligne')), self.first, QLabel(tr('Pas')), self.increment))
        self.generated = QPlainTextEdit()
        self.generated.setReadOnly(True)
        self.generated.setMaximumHeight(130)
        layout.addWidget(self.generated)
        self.sprite_info = label('')
        layout.addWidget(self.sprite_info)
        layout.addWidget(row(button(tr('Copier le BASIC'), self.copy_generated),
            button(tr('Exporter .bas…'), self.save_generated), button(tr('Ajouter au programme'), self.insert_generated)))
        layout.addWidget(label(tr('Glisser pour dessiner ; clic droit pour effacer. LCD : rangées décimales pour tenir en 63 caractères. '
            'Papier : DIM initialise le tableau choisi ; utiliser un nom libre. L’aperçu affiche les pixels, sans simuler leur taille physique.')))
        self.kind.currentTextChanged.connect(self.resize_grid)
        self.preset.currentTextChanged.connect(self.resize_grid)
        for grid in (self.grid, self.triangle, self.lower):
            grid.changed.connect(self.sprite_changed)
        for control in (self.position, self.zoom, self.first, self.increment):
            control.valueChanged.connect(self.generate)
        self.array.currentTextChanged.connect(self.generate)
        self.base.currentTextChanged.connect(self.generate)
        return tab

    def sprite_changed(self):
        self.asset_dirty = True
        self.generate()

    def resize_grid(self, *_):
        lcd = self.kind.currentData() == 'LCD'
        self.target_controls()
        self.preset.setEnabled(not lcd)
        self.extras.setVisible(lcd)
        self.lcd_preview.setVisible(lcd)
        w, h = (5, 7) if lcd else tuple(map(int, self.preset.currentText().split(' × ')))
        # Preserve the overlapping region, including when changing targets.
        old = self.grid.pixels
        self.grid.set_pixels([[old[y][x] if y < len(old) and x < len(old[0]) else 0 for x in range(w)] for y in range(h)])

    def target_controls(self):
        lcd = self.kind.currentData() == 'LCD'
        self.position.setEnabled(lcd)
        for control in (self.zoom, self.array, self.base):
            control.setEnabled(not lcd)

    def clear_grid(self):
        self.grid.set_pixels([[0]*len(self.grid.pixels[0]) for _ in self.grid.pixels])

    @staticmethod
    def mask(grid):
        return sum(v << (4-i) for i, v in enumerate(grid.pixels[0]))

    def generate(self, *_):
        try:
            text = export_sprite(self.grid.pixels, self.kind.currentData(),
                self.first.value(), self.increment.value(), self.position.value(),
                self.mask(self.triangle), self.mask(self.lower), self.array.currentText(),
                self.zoom.value(), self.base.currentData())
            self.generated.setPlainText(text)
            result = analyze(text)
            if result.issues:
                self.sprite_info.setText(tr('Export à réduire : ')+result.issues[0][1])
            else:
                w, h = len(self.grid.pixels[0]), len(self.grid.pixels)
                ram = (9+5*h*(w if w>16 else 1)) if self.kind.currentData() == 'Papier' else 0
                self.sprite_info.setText((tr('Code : ') + f'{result.used}' + tr(' octets ; tableau : ') + f'{ram}' + tr(' octets, hors travail temporaire.')))
        except ValueError as exc:
            self.generated.setPlainText(tr('Erreur : ')+str(exc))
            self.sprite_info.setText(tr('Corriger les paramètres d’export.'))

    def copy_generated(self):
        text = self.generated.toPlainText()
        if not text.startswith(tr('Erreur : ')):
            QApplication.clipboard().setText(text)

    def save_generated(self):
        text = self.generated.toPlainText()
        if text.startswith(tr('Erreur : ')):
            return self.error(text)
        name, _ = QFileDialog.getSaveFileName(self, tr('Exporter le glyphe en BASIC'), 'glyphe.bas', 'BASIC (*.bas)')
        if name:
            try:
                self.atomic_write(name, text.encode('ascii'))
            except OSError as exc:
                self.error(exc)

    def insert_generated(self):
        addition = self.generated.toPlainText()
        if addition.startswith(tr('Erreur : ')):
            return self.error(addition)
        old = self.editor.toPlainText()
        combined = old.rstrip()+'\n'+addition
        result = analyze(combined)
        if result.issues:
            return self.error(tr('Insertion refusée : ')+result.issues[0][1]+tr('\nAjuster le numéro initial des lignes générées.'))
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(('\n' if old and not old.endswith('\n') else '')+addition+'\n')
        self.editor.setTextCursor(cursor)

    def confirm_asset(self):
        if not self.asset_dirty:
            return True
        result = QMessageBox.question(self, tr('Sprite modifié'), tr('Enregistrer le sprite avant de le remplacer ?'),
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        return self.save_asset() if result == QMessageBox.StandardButton.Save else result == QMessageBox.StandardButton.Discard

    def save_asset(self):
        name, _ = QFileDialog.getSaveFileName(self, tr('Enregistrer le sprite'), 'sprite.json', 'Sprite (*.json)')
        if not name:
            return False
        try:
            save_asset(name, self.grid.pixels, self.kind.currentData(), self.mask(self.triangle), self.mask(self.lower))
            self.asset_dirty = False
            return True
        except (OSError, ValueError) as exc:
            self.error(exc)
            return False

    def open_asset(self):
        if not self.confirm_asset():
            return
        name, _ = QFileDialog.getOpenFileName(self, tr('Ouvrir un sprite'), '', 'Sprite (*.json)')
        if not name:
            return
        try:
            data = load_asset(name)
            self.kind.setCurrentIndex(self.kind.findData(data['kind']))
            if data['kind'] == 'Papier':
                size = f"{len(data['pixels'][0])} × {len(data['pixels'])}"
                if self.preset.findText(size) < 0:
                    self.preset.addItem(size)
                self.preset.setCurrentText(size)
            self.grid.set_pixels(data['pixels'])
            for grid, key in [(self.triangle, 'triangle'), (self.lower, 'lower')]:
                grid.set_pixels([[(data.get(key, 0) >> (4-i)) & 1 for i in range(5)]])
            self.asset_dirty = False
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.error(exc)

    def insert_character(self,text):
        self.editor.textCursor().insertText(text)
        self.editor.setFocus()

    def import_basic_glyph(self):
        from glyph_import import import_glyphs
        source=self.editor.textCursor().selectedText().replace('\u2029','\n') or self.editor.toPlainText()
        try:
            assets=import_glyphs(source)
            index=0
            if len(assets)>1:
                options=[f"{i+1} : {tr(a['kind'])} — {len(a['pixels'][0])} × {len(a['pixels'])}" for i,a in enumerate(assets)]
                choice,ok=QInputDialog.getItem(self,tr('Choisir le glyphe'),tr('Glyphe'),options,0,False)
                if not ok:return
                index=options.index(choice)
            if not self.confirm_asset():return
            asset=assets[index];self.kind.setCurrentIndex(self.kind.findData(asset['kind']))
            if asset['kind']=='Papier':
                size=f"{len(asset['pixels'][0])} × {len(asset['pixels'])}"
                if self.preset.findText(size)<0:self.preset.addItem(size)
                self.preset.setCurrentText(size);self.zoom.setValue(asset['zoom']);self.array.setCurrentText(asset['array'])
            else:self.position.setValue(asset['position'])
            self.grid.set_pixels(asset['pixels'])
            for grid,name in [(self.triangle,'triangle'),(self.lower,'lower')]:
                grid.set_pixels([[(asset.get(name,0)>>(4-x))&1 for x in range(5)]])
            self.tabs.setCurrentWidget(self.glyph_tab);self.asset_dirty=True
        except (ValueError,KeyError) as exc:self.error(exc)

    def import_sprite(self):
        if not self.confirm_asset():
            return
        name, _ = QFileDialog.getOpenFileName(self, tr('Importer et ajuster à la grille'), '', 'Images (*.png *.jpg *.jpeg *.bmp *.gif)')
        if not name:
            return
        try:
            from PIL import Image, ImageOps
            with Image.open(name) as image:
                rgba = ImageOps.exif_transpose(image).convert('RGBA')
                white = Image.new('RGBA', rgba.size, 'white')
                white.alpha_composite(rgba)
                size = (len(self.grid.pixels[0]), len(self.grid.pixels))
                gray = ImageOps.pad(white.convert('L'), size, color=255, method=Image.Resampling.LANCZOS)
                self.grid.set_pixels([[int(gray.getpixel((x,y)) < 128) for x in range(size[0])] for y in range(size[1])])
        except (OSError, ValueError) as exc:
            self.error(exc)

    def image_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(button(tr('Ouvrir une image…'), self.open_image))
        self.image_name = label(tr('Aucune image sélectionnée'))
        layout.addWidget(self.image_name)
        self.width_px, self.height_px = spin(1, 248, 248), spin(1, 256, 256)
        self.threshold = spin(0, 255, 128)
        self.aspect = QDoubleSpinBox()
        self.aspect.setRange(0.25, 8)
        self.aspect.setValue(2)
        self.aspect.setSingleStep(0.05)
        self.dither = QCheckBox(tr('Tramage photo'))
        layout.addWidget(row(QLabel(tr('Largeur max.')), self.width_px, QLabel(tr('Hauteur max.')), self.height_px))
        layout.addWidget(row(QLabel(tr('Seuil')), self.threshold, QLabel(tr('Rapport pixel H/L')), self.aspect))
        layout.addWidget(self.dither)
        self.image_preview = QLabel(tr('Aperçu monochrome'))
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(240)
        self.image_preview.setStyleSheet('background:white; border:1px solid #ccd2da;')
        layout.addWidget(self.image_preview, 1)
        self.image_info = label(tr('L’aperçu étire les rangées selon le rapport physique choisi. Les dimensions transmises restent en pixels.'))
        layout.addWidget(self.image_info)
        layout.addWidget(button(tr('Enregistrer le bitmap transmis…'), self.save_preview))
        layout.addWidget(label(tr('Papier thermique conseillé. L’impression peut effectuer NEW si elle manque de RAM : '
            'sauvegarder auparavant le programme de la Canon. Une tâche par démarrage selon le firmware.')))
        self.print_button = button(tr('Imprimer → CODE+P'), self.print_image)
        layout.addWidget(self.print_button)
        for control in (self.width_px, self.height_px, self.threshold, self.aspect):
            control.valueChanged.connect(self.update_image)
        self.dither.toggled.connect(self.update_image)
        return tab

    def open_image(self):
        name, _ = QFileDialog.getOpenFileName(self, tr('Ouvrir une image'), '', 'Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.gif)')
        if name:
            self.image_path = Path(name)
            self.image_name.setText(self.image_path.name)
            self.update_image()

    def update_image(self, *_):
        self.mono = None
        if not self.image_path:
            return
        try:
            self.mono, pixels = prepare_image(self.image_path, self.width_px.value(), self.height_px.value(),
                self.threshold.value(), self.dither.isChecked(), self.aspect.value())
            from PIL.ImageQt import ImageQt
            from PIL import Image
            display = self.mono.convert('RGB').resize((self.mono.width, max(1, round(self.mono.height*self.aspect.value()))), Image.Resampling.NEAREST)
            pix = QPixmap.fromImage(ImageQt(display)).scaled(440, 310, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
            self.image_preview.setPixmap(pix)
            self.image_info.setText((f'{self.mono.width}' + ' × ' + f'{self.mono.height}' + tr(' pixels transmis. Aperçu aux proportions papier approchées ; aucune mesure en mm.')))
        except (OSError, ValueError) as exc:
            self.image_preview.clear()
            self.image_info.setText(tr('Image invalide : ')+str(exc))

    def save_preview(self):
        if self.mono is None:
            return
        name, _ = QFileDialog.getSaveFileName(self, tr('Bitmap transmis (pixels bruts)'), 'typestar-raster.png', 'PNG (*.png)')
        if name:
            try:
                if Path(name).resolve() == self.image_path.resolve():
                    raise ValueError(tr('Choisir un autre nom pour préserver l’image source.'))
                self.mono.save(name, format='PNG')
            except (OSError, ValueError) as exc:
                self.error(exc)

    def port_device(self):
        text = self.port.currentText().strip()
        index = self.port.currentIndex()
        if index >= 0 and text == self.port.itemText(index):
            return self.port.itemData(index) or text
        return text

    def select_port(self, device):
        index = self.port.findData(device)
        if index >= 0:
            self.port.setCurrentIndex(index)
        else:
            self.port.setCurrentText(device)

    def refresh_ports(self):
        from serial.tools.list_ports import comports
        current = self.port_device()
        self.port.clear()
        for port in sorted(comports(), key=lambda p: p.device):
            details = list(dict.fromkeys(v for v in
                (port.name, port.description, port.manufacturer)
                if v and v != 'n/a' and v != port.device))
            label = port.device + (' — ' + ' — '.join(details) if details else '')
            self.port.addItem(label, port.device)
            self.port.setItemData(self.port.count()-1,
                label + '\n' + (port.hwid or ''), Qt.ItemDataRole.ToolTipRole)
        self.select_port(current)

    def serial_args(self):
        return ['--baud', self.baud.currentText(), '--parity', self.parity.currentText(), '--stopbits', self.stops.currentText()]

    def ready(self):
        if self.process:
            return False
        if not self.port_device():
            self.error(tr('Choisir ou saisir un port série.'))
            return False
        return True

    def send(self):
        if not self.ready():
            return
        result = self.check()
        if result.issues or not result.records:
            return self.error(tr('Corriger le programme avant transfert (au moins une ligne).'))
        if QMessageBox.question(self, tr('Envoyer vers la Canon'),
            tr('LOAD remplacera le programme présent sur la Canon. Envoyer le texte actuel de l’éditeur ?')) != QMessageBox.StandardButton.Yes:
            return
        self.job_temp = tempfile.TemporaryDirectory(prefix='typestar-studio-')
        path = Path(self.job_temp.name)/'program.bas'
        path.write_text(self.editor.toPlainText(), encoding='utf-8')
        self.start_job('transfer_native_basic.py', [self.port_device(), 'load', str(path)]+self.serial_args(),
            tr('Taper LOAD puis Return sur la Canon. Le programme de la machine sera remplacé.'))

    def receive(self):
        if not self.ready():
            return
        name, _ = QFileDialog.getSaveFileName(self, tr('Recevoir le programme de la Canon'), 'reception.bas', 'BASIC (*.bas)')
        if not name:
            return
        self.receive_path = Path(name)
        self.job_temp = tempfile.TemporaryDirectory(prefix='typestar-studio-')
        path = Path(self.job_temp.name)/'received.bas'  # CLI requires a nonexistent destination
        self.start_job('transfer_native_basic.py', [self.port_device(), 'save', str(path)]+self.serial_args(),
            tr('Taper SAVE puis Return sur la Canon. Le fichier ne sera écrit qu’après réception complète.'))

    def print_image(self):
        if not self.ready() or self.mono is None:
            return
        if QMessageBox.question(self, tr('Impression papier'),
            tr('Le papier va avancer. Le firmware peut effacer le programme et ses variables (NEW) pour libérer la RAM. '
            'Avez-vous sauvegardé ce qui doit être conservé et souhaitez-vous imprimer cet aperçu ?')) != QMessageBox.StandardButton.Yes:
            return
        self.job_temp = tempfile.TemporaryDirectory(prefix='typestar-studio-')
        path = Path(self.job_temp.name)/'image.png'
        self.mono.save(path)
        # Transmit the prepared raster exactly once: no second aspect correction.
        self.start_job('print_image.py', [str(path), '--port', self.port_device(),
            '--pixel-aspect', '1']+self.serial_args(), tr('Appuyer sur CODE+P sur la Canon ; impression de l’aperçu confirmé.'))

    def start_job(self, script, args, instruction):
        self.cancelled = False
        self.log.clear()
        self.job_status.setText(instruction)
        self.process = QProcess(self)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert('PYTHONUTF8', '1')
        environment.insert('TYPESTAR_STUDIO_LANGUAGE', language())
        self.process.setProcessEnvironment(environment)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.setWorkingDirectory(str(ROOT))
        self.process.readyReadStandardOutput.connect(self.read_log)
        self.process.finished.connect(self.job_finished)
        self.process.errorOccurred.connect(self.job_error)
        self.set_busy(True)
        self.process.start(worker_python(), ['-u', str(ROOT/'tools'/script)]+args)

    def set_busy(self, busy):
        for widget in (self.send_button, self.receive_button, self.print_button, self.port, self.baud, self.parity, self.stops):
            widget.setEnabled(not busy)
        self.stop_button.setEnabled(busy)
        self.progress.setRange(0, 0 if busy else 1)
        self.progress.setValue(0)

    def read_log(self):
        if self.process:
            text = bytes(self.process.readAllStandardOutput()).decode('utf-8', errors='replace')
            cursor = self.log.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(text)
            self.log.setTextCursor(cursor)

    def job_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.log.appendPlainText(self.process.errorString())
            self.job_finished(-1, QProcess.ExitStatus.CrashExit)

    def job_finished(self, code, status):
        if not self.process:
            return
        self.read_log()
        success = code == 0 and status == QProcess.ExitStatus.NormalExit and not self.cancelled
        if success and self.receive_path:
            try:
                data = (Path(self.job_temp.name)/'received.bas').read_bytes()
                if analyze(data.decode('utf-8-sig')).issues:
                    raise ValueError(tr('Programme reçu invalide.'))
                self.atomic_write(self.receive_path, data)
                self.log.appendPlainText(tr('Fichier reçu : ')+str(self.receive_path))
            except (OSError, ValueError) as exc:
                success = False
                self.log.appendPlainText(str(exc))
        self.job_status.setText(tr('Opération acquittée par la Canon. Consulter le journal et son écran.') if success else
            tr('Opération interrompue ou échouée. LOAD/page peuvent être partiels ; vérifier la Canon. Aucun nouvel essai automatique.'))
        self.process.deleteLater()
        self.process = None
        self.receive_path = None
        if self.job_temp:
            self.job_temp.cleanup()
            self.job_temp = None
        self.set_busy(False)

    def cancel(self):
        if self.process:
            self.cancelled = True
            self.job_status.setText(tr('Arrêt de la communication PC. Interrompre aussi la Canon avec BREAK si nécessaire.'))
            self.process.kill()

    def guide(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(ROOT/'studio/README.md')))

    def closeEvent(self, event):
        if self.process:
            self.error(tr('Une communication est en cours. Utiliser Annuler puis fermer la fenêtre.'))
            event.ignore()
            return
        if not self.confirm_editor() or not self.confirm_asset():
            event.ignore()
            return
        for name, widget in [('port', self.port), ('baud', self.baud), ('parity', self.parity), ('stops', self.stops)]:
            self.settings.setValue('serial/'+name, self.port_device() if name == 'port' else widget.currentText())
        self.settings.sync()
        self.emulator.power_off()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName('Typestar')
    app.setApplicationName('BASIC Studio')
    app.setStyle('Fusion')
    window = Studio()
    window.show()
    return app.exec()

if __name__ == '__main__':
    raise SystemExit(main())
