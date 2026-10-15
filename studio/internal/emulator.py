from i18n import tr, language
"""Interactive LCD/keyboard front end to the isolated firmware process."""
import json
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QProcess, QProcessEnvironment, Signal, QRectF, QTimer
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QLineEdit, QPlainTextEdit, QComboBox, QTabWidget, QCheckBox, QSlider, QSplitter, QFileDialog, QDialog, QDialogButtonBox, QMessageBox
from PySide6.QtMultimedia import QMediaDevices
from core import ROOT, analyze, VERSION
from lcd_glass import render_glass
from buzzer_audio import BuzzerAudio
from paper_widget import PaperPanel
from native_keyboard import host_key, BUTTON_KEYS


def worker_python():
    path = Path(sys.executable)
    return str(path.with_name('python.exe') if path.name.lower() == 'pythonw.exe' else path)


class VirtualLCD(QWidget):
    key = Signal(int)
    held = Signal(int)
    matrix = Signal(object, bool, bool)
    code_toggle = Signal()

    def __init__(self):
        super().__init__()
        self.state = dict(cells=[32]*32, cgram=[0]*64, lower=[32]*32)
        atlas = json.loads((Path(__file__).parent/'assets/lcd-font.json').read_text(encoding='utf-8'))
        self.native_rows = {int(k, 16): v for k, v in atlas['rows'].items()}
        self.pressed_keys={}
        self.native_mode=False
        self.native_pressed={}
        self.spaced = True
        self.blink = True
        self.blink_timer = QTimer(self)
        self.blink_timer.setInterval(500)
        self.blink_timer.timeout.connect(self.blink_tick)
        self.blink_timer.start()
        self.setMinimumSize(420, 100)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip(tr('Cliquer ici pour utiliser le clavier : flèches, Return, Backspace, Échap = BREAK.'))

    def set_spaced(self, spaced):
        self.spaced = spaced
        self.update()

    def paintEvent(self, event):
        ratio = self.devicePixelRatioF()
        image = render_glass(round(self.width()*ratio), round(self.height()*ratio),
                             self.state, self.native_rows, self.spaced, self.blink)
        image.setDevicePixelRatio(ratio)
        painter = QPainter(self)
        painter.drawImage(0, 0, image)

    def blink_tick(self):
        self.blink = not self.blink
        if self.state.get('control',12) & 1:
            self.update()

    def keyPressEvent(self, event):
        if event.isAutoRepeat():event.accept();return
        if event.key()==Qt.Key.Key_F7:
            self.code_toggle.emit();event.accept();return
        if self.native_mode or event.key() in (Qt.Key.Key_F8,Qt.Key.Key_F9):
            mapped=host_key(event)
            if mapped is not None:
                self.native_pressed[event.key()]=mapped
                self.emit_native(event.modifiers())
            event.accept();return
        keys = {Qt.Key.Key_Return:13, Qt.Key.Key_Enter:13, Qt.Key.Key_Backspace:8,
                Qt.Key.Key_Left:18, Qt.Key.Key_Right:19, Qt.Key.Key_Escape:3,
                Qt.Key.Key_Up:20, Qt.Key.Key_Down:21}
        value = keys.get(event.key())
        if value is None and len(event.text()) == 1 and 32 <= ord(event.text()) < 127:
            value = ord(event.text())
        if value is not None:
            self.pressed_keys.pop(event.key(),None)
            self.pressed_keys[event.key()]=value
            self.key.emit(value)
            event.accept()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self,event):
        if event.isAutoRepeat():event.accept();return
        if event.key()==Qt.Key.Key_F7:event.accept();return
        if self.native_mode or event.key() in self.native_pressed:
            self.native_pressed.pop(event.key(),None)
            self.emit_native(event.modifiers());event.accept();return
        self.pressed_keys.pop(event.key(),None)
        self.held.emit(next(reversed(self.pressed_keys.values()),0))
        event.accept()

    def emit_native(self, modifiers):
        keys={v[0] for v in self.native_pressed.values()}
        if modifiers & Qt.KeyboardModifier.ControlModifier:keys.add(0x3b)
        shift=any(v[1] for v in self.native_pressed.values())
        self.matrix.emit(sorted(keys),shift,False)

    def focusOutEvent(self,event):
        self.native_pressed.clear()
        self.matrix.emit([],False,False)
        self.pressed_keys.clear();self.held.emit(0)
        super().focusOutEvent(event)


class EmulatorPanel(QWidget):
    def __init__(self, source, settings=None):
        super().__init__()
        self.source = source
        self.settings = settings
        self.mask_path = settings.value('emulator/mask_rom','') if settings else ''
        self.firmware_path = settings.value('emulator/firmware_rom','') if settings else ''
        self.rom_mode = settings.value('emulator/mode','auto') if settings else 'auto'
        self.rom_layout = settings.value('emulator/layout','auto') if settings else 'auto'
        self.cartridge_path = settings.value('emulator/cartridge_rom','') if settings else ''
        self.basic_available = True
        self.audio = BuzzerAudio(self)
        self.audio_warning = None
        self.process = None
        self.worker_ready = False
        self.buffer = bytearray()
        self.pending_source = None
        self.paused = False
        self.last_state = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(3)
        # Keep native/font-based sizing: compact without clipping at high DPI.
        self.setStyleSheet('QPushButton { padding: 2px 6px; } '
                           'QTabBar::tab { padding: 4px 8px; }')
        rom_row=QHBoxLayout()
        rom_row.setSpacing(4)
        rom_button=QPushButton(tr('Choisir les ROM…'));rom_button.clicked.connect(self.choose_roms)
        rom_row.addWidget(rom_button)
        self.rom_label=QLabel();self.rom_label.setWordWrap(True);rom_row.addWidget(self.rom_label,1)
        layout.addLayout(rom_row);self.update_rom_label()
        cart_row=QHBoxLayout()
        cart_row.setSpacing(4)
        cart_button=QPushButton(tr('Cartouche ROM…'));cart_button.clicked.connect(self.choose_cartridge)
        cart_row.addWidget(cart_button)
        self.cart_eject=QPushButton(tr('Retirer'));self.cart_eject.clicked.connect(lambda:self.set_cartridge_path(''))
        cart_row.addWidget(self.cart_eject)
        self.cart_label=QLabel();self.cart_label.setWordWrap(True);cart_row.addWidget(self.cart_label,1)
        layout.addLayout(cart_row);self.update_cartridge_label()
        self.lcd = VirtualLCD()
        self.lcd.code_toggle.connect(lambda:self.write(dict(op="code_toggle")))
        self.lcd.key.connect(self.send_key)
        self.lcd.held.connect(self.release_key)
        self.lcd.matrix.connect(lambda keys,shift,cancel:self.write(dict(op='host_matrix',keys=keys,shift=shift,cancel=cancel)))
        layout.addWidget(self.lcd)
        self.lcd.setToolTip(tr('Pixels à échelle entière. Affichage → Pixels LCD : jointifs ou espacés.\nIndicateurs pilotés par ICON ; raccordement des cinq derniers pictogrammes à confirmer sur machine.'))
        self.key_status = QLabel(tr('Dernière touche INKEY : —'))
        layout.addWidget(self.key_status)
        audio_row=QHBoxLayout()
        audio_row.setSpacing(4)
        self.audio_output=QComboBox()
        self.audio_output.addItem(tr('Audio : sortie système'),None)
        for device in QMediaDevices.audioOutputs():
            self.audio_output.addItem(device.description(),bytes(device.id()))
        self.audio_output.currentIndexChanged.connect(self.change_audio_output)
        audio_row.addWidget(self.audio_output)
        test_audio=QPushButton(tr('Tester le son'))
        test_audio.clicked.connect(self.test_audio)
        audio_row.addWidget(test_audio)
        audio_row.addWidget(QLabel('Volume'))
        self.audio_volume=QSlider(Qt.Orientation.Horizontal)
        self.audio_volume.setRange(0,100);self.audio_volume.setValue(85)
        self.audio_volume.setMaximumWidth(120)
        self.audio_volume.valueChanged.connect(lambda v:self.audio.set_volume(v/100))
        audio_row.addWidget(self.audio_volume)
        self.sound_duration=QComboBox()
        for label,value in [(tr('Durée ×1'),1.),(tr('Durée ×1,5'),1.5),(tr('Durée ×2'),2.),(tr('Durée ×2,5'),2.5),(tr('Durée ×3'),3.)]:self.sound_duration.addItem(label,value)
        self.sound_duration.setToolTip(tr('Ajustement de confort : son et attente BASIC. ×1 respecte la durée nominale.'))
        self.sound_duration.currentIndexChanged.connect(lambda:self.write(dict(op='sound_scale',value=self.sound_duration.currentData())))
        audio_row.addWidget(self.sound_duration)
        layout.addLayout(audio_row)
        self.status = QLabel(tr('OFF — allumer la machine virtuelle avant d’exécuter un programme.'))
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        controls = QHBoxLayout()
        controls.setSpacing(4)
        self.power=QPushButton('ON / OFF')
        self.power.setCheckable(True)
        self.power.setMinimumWidth(100)
        self.power.setToolTip('ON / OFF')
        self.power.setStyleSheet('QPushButton:checked { background-color: #287b45; color: white; font-weight: bold; }')
        self.power.toggled.connect(self.set_power)
        controls.addWidget(self.power)
        for text, fn in [(tr('Exécuter (F5)'), self.run_editor), (tr('Pause / reprise'), self.pause),
                         (tr('Réinitialiser'), self.reset), (tr('Arrêter'), self.stop)]:
            b = QPushButton(text); b.clicked.connect(lambda checked=False, f=fn: f()); controls.addWidget(b)
        layout.addLayout(controls)
        keys=QGridLayout()
        keys.setHorizontalSpacing(4)
        keys.setVerticalSpacing(3)
        self.special_buttons={}
        rows=[[("MARGIN RELEASE/BREAK",0x36),("KB - I/II",0x3a),("LEFT MARGIN",0x38),("RIGHT MARGIN",0x39)],
              [("TEXT",0x3c),("MODE",0x37),("TAB SET",0x34),("TAB CLR",0x35)],
              [("REPEAT",0x2e),("RELOC",0x33),("CODE",0x3b)]]
        for row,items in enumerate(rows):
            for column,(name,code) in enumerate(items):
                b=QPushButton(name);b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                self.special_buttons[code]=b
                shortcut={0x3b:'F7',0x37:'F8',0x3a:'F9'}.get(code,'')
                b.setToolTip(f'${code:02X}'+(f' — {shortcut}' if shortcut else ''))
                if code==0x3b:
                    b.setCheckable(True)
                    b.clicked.connect(self.toggle_code)
                else:
                    b.pressed.connect(lambda code=code:self.special_press(code))
                    b.released.connect(lambda:self.write(dict(op='host_matrix',keys=[])))
                keys.addWidget(b,row,column)
        self.code_button=self.special_buttons[0x3b]
        self.native_buttons=list(self.special_buttons.values())
        arrows=QHBoxLayout()
        arrows.setSpacing(4)
        for name,value in [('←',18),('→',19)]:
            b=QPushButton(name);b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.pressed.connect(lambda v=value:self.send_key(v));b.released.connect(lambda:self.release_key(0))
            arrows.addWidget(b)
        keys.addLayout(arrows,2,3)
        layout.addLayout(keys)
        self.entry = QLineEdit()
        self.entry.setPlaceholderText(tr('Commande BASIC ou réponse à INPUT, puis Return (ASCII)'))
        self.entry.setMaxLength(63)
        self.entry.returnPressed.connect(self.send_line)
        layout.addWidget(self.entry)
        self.matrix_panel = QWidget()
        matrix_row = QHBoxLayout(self.matrix_panel)
        matrix_row.setContentsMargins(0,0,0,0)
        matrix_row.addWidget(QLabel(tr('Touche matrice (hex 00–3F) :')))
        self.matrix_code = QLineEdit('00');self.matrix_code.setMaximumWidth(60)
        matrix_row.addWidget(self.matrix_code)
        self.matrix_shift = QCheckBox('SHIFT');matrix_row.addWidget(self.matrix_shift)
        self.matrix_code_modifier = QCheckBox('CODE ($3B)');matrix_row.addWidget(self.matrix_code_modifier)
        self.matrix_button = QPushButton(tr('Maintenir la touche'))
        self.matrix_button.pressed.connect(self.matrix_press)
        self.matrix_button.released.connect(self.matrix_release)
        matrix_row.addWidget(self.matrix_button)
        matrix_row.addStretch()
        layout.addWidget(self.matrix_panel)
        self.matrix_panel.hide()
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(200)
        self.details=QTabWidget()
        self.details.addTab(self.log,tr('Journal'))
        debug=QWidget();debug_layout=QVBoxLayout(debug)
        row=QHBoxLayout()
        row.addWidget(QLabel(tr('Adresse mémoire (hex) :')))
        self.debug_address=QLineEdit('1900');self.debug_address.setMaxLength(4)
        row.addWidget(self.debug_address)
        refresh=QPushButton(tr('Actualiser'));refresh.clicked.connect(self.request_debug)
        row.addWidget(refresh)
        self.debug_live=QCheckBox(tr('Suivi PC (5 Hz)'));self.debug_live.setChecked(True)
        row.addWidget(self.debug_live)
        self.debug_pending=False
        self.debug_timer=QTimer(self);self.debug_timer.setInterval(200)
        self.debug_timer.timeout.connect(self.refresh_debug_live)
        self.debug_timer.start()
        debug_layout.addLayout(row)
        hint=QLabel(tr('Lecture seule. Pause pour figer la machine. Mémoire brute ; registres périphériques non relus. Désassemblage depuis PC, pas de reconstruction BASIC.'))
        hint.setWordWrap(True);debug_layout.addWidget(hint)
        self.debug_registers=QLabel();debug_layout.addWidget(self.debug_registers)
        self.debug_registers.setWordWrap(True)
        self.debug_flags=QLabel();debug_layout.addWidget(self.debug_flags)
        split=QSplitter(Qt.Orientation.Horizontal)
        font=QFont('Consolas');font.setStyleHint(QFont.StyleHint.Monospace)
        for title,attribute in [(tr('Mémoire (adresse fixe)'),'debug_memory'),(tr('Code désassemblé (PC)'),'debug_code')]:
            panel=QWidget();column=QVBoxLayout(panel);column.addWidget(QLabel(title))
            view=QPlainTextEdit();view.setReadOnly(True);view.setFont(font)
            view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            setattr(self,attribute,view);column.addWidget(view);split.addWidget(panel)
        debug_layout.addWidget(split)
        self.details.addTab(debug,tr('Débogueur'))
        self.paper=PaperPanel();self.details.addTab(self.paper,tr('Papier'))
        self.details.currentChanged.connect(lambda index:self.request_debug() if index==1 else None)
        layout.addWidget(self.details,1)

    def update_rom_label(self):
        self.rom_label.setText('MaskROM : '+(Path(self.mask_path).name if self.mask_path else tr('à choisir'))+
                              '\nIC8 : '+(Path(self.firmware_path).name if self.firmware_path else tr('à choisir')))
        self.rom_label.setToolTip(f'{self.mask_path}\n{self.firmware_path}')

    def update_cartridge_label(self):
        label=Path(self.cartridge_path).name if self.cartridge_path else tr('Aucune cartouche')
        if self.cartridge_path and self.basic_available:label+=' — '+tr('inactive avec le profil BASIC')
        self.cart_label.setText(label);self.cart_label.setToolTip(self.cartridge_path)
        self.cart_eject.setEnabled(bool(self.cartridge_path))

    def set_cartridge_path(self, path):
        from cartridge import load_cartridge
        load_cartridge(path)  # Reject invalid files before changing the running machine.
        if str(path)==self.cartridge_path:return
        self.power_off()
        self.cartridge_path=str(path)
        if self.settings:
            self.settings.setValue('emulator/cartridge_rom',self.cartridge_path);self.settings.sync()
        self.update_cartridge_label()
        self.log.appendPlainText(tr('Cartouche modifiée. Allumer la machine virtuelle pour la détecter.'))

    def choose_cartridge(self):
        path,_=QFileDialog.getOpenFileName(self,tr('Cartouche de police Canon'),self.cartridge_path,
                                         tr('ROM (*.bin *.BIN);;Tous les fichiers (*)'))
        if path:
            try:self.set_cartridge_path(path)
            except (OSError,ValueError) as exc:QMessageBox.warning(self,tr('Cartouche ROM'),tr(str(exc)))

    def set_rom_paths(self, mask, firmware, mode='auto', layout='auto'):
        from rom_images import load_roms
        _,_,_,info=load_roms(mask,firmware,mode,layout)
        self.power_off()
        self.mask_path=str(mask);self.firmware_path=str(firmware)
        self.rom_mode=mode;self.rom_layout=layout
        self.set_machine_mode(info['basic_available'])
        if self.settings:
            self.settings.setValue('emulator/mask_rom',self.mask_path)
            self.settings.setValue('emulator/firmware_rom',self.firmware_path)
            self.settings.setValue('emulator/mode',self.rom_mode)
            self.settings.setValue('emulator/layout',self.rom_layout)
            self.settings.sync()
        self.update_rom_label()

    def choose_roms(self):
        dialog=QDialog(self);dialog.setWindowTitle(tr('ROM de la machine virtuelle'))
        layout=QVBoxLayout(dialog)
        note=QLabel(tr('MaskROM : 16 ko ; ROM externe IC8 : 32 ko.\n'
                    'Auto active les facilités BASIC uniquement pour les ROM reconnues.\n'
                    'Le mode générique démarre au RESET, sans raccourcis BASIC. Mécanique, papier et buzzer simulés avec des temporisations approximatives.'))
        note.setWordWrap(True);layout.addWidget(note)
        fields=[]
        for label,value in [(tr('MaskROM Canon'),self.mask_path),(tr('ROM externe IC8'),self.firmware_path)]:
            row=QHBoxLayout();row.addWidget(QLabel(label));field=QLineEdit(value);fields.append(field)
            row.addWidget(field);button=QPushButton(tr('Parcourir…'));row.addWidget(button)
            def browse(checked=False,field=field,label=label):
                path,_=QFileDialog.getOpenFileName(dialog,label,field.text(),tr('ROM (*.bin *.BIN);;Tous les fichiers (*)'))
                if path:field.setText(path)
            button.clicked.connect(browse);layout.addLayout(row)
        mode=QComboBox()
        for text,value in [(tr('Auto : profil BASIC si reconnu'),'auto'),(tr('ROM générique (expérimental)'),'generic'),(tr('Profil BASIC obligatoire'),'basic')]:mode.addItem(text,value)
        mode.setCurrentIndex(max(0,mode.findData(self.rom_mode)))
        layout.addWidget(mode)
        order=QComboBox()
        for text,value in [(tr('Ordre des octets : automatique'),'auto'),('IC8 / OneROM','socket'),('CPU $4000–$BFFF','cpu')]:order.addItem(text,value)
        order.setCurrentIndex(max(0,order.findData(self.rom_layout)))
        layout.addWidget(order)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons);buttons.rejected.connect(dialog.reject)
        def accept():
            try:self.set_rom_paths(*(field.text().strip() for field in fields),mode=mode.currentData(),layout=order.currentData())
            except (OSError,ValueError) as exc:
                QMessageBox.warning(dialog,'ROM',str(exc));return
            dialog.accept()
        buttons.accepted.connect(accept);dialog.resize(760,230)
        return dialog.exec()==QDialog.DialogCode.Accepted

    def write(self, value):
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.write((json.dumps(value)+'\n').encode('utf-8'))

    def set_power(self, enabled):
        if enabled:self.start()
        else:self.power_off()

    def power_on(self):
        if not self.process:self.start()

    def start(self, source=None):
        if not self.mask_path or not self.firmware_path:
            if not self.choose_roms():
                self.power.blockSignals(True);self.power.setChecked(False);self.power.blockSignals(False)
                return
        try:
            from rom_images import load_roms
            _,_,_,info=load_roms(self.mask_path,self.firmware_path,self.rom_mode,self.rom_layout)
            self.set_machine_mode(info['basic_available'])
            if not self.basic_available:
                from cartridge import load_cartridge
                load_cartridge(self.cartridge_path)
                source=None
        except (OSError,ValueError) as exc:
            self.log.appendPlainText(str(exc));self.status.setText(tr('Vérifier les fichiers ROM sélectionnés.'));self.power_off();return
        self.debug_pending=False
        self.audio.stop()
        self.pending_source = source
        self.power.blockSignals(True);self.power.setChecked(True);self.power.blockSignals(False)
        if self.process:
            if self.worker_ready:self.write({'op':'run', 'source':source} if source is not None else {'op':'reset'})
            return
        self.worker_ready=False
        self.paper.clear()
        self.buffer.clear()
        self.status.setText(tr('Initialisation du moteur et du firmware…'))
        p = self.process = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        env.insert('PYTHONUTF8', '1')
        env.insert('TYPESTAR_STUDIO_LANGUAGE', language())
        p.setProcessEnvironment(env)
        p.readyReadStandardOutput.connect(self.read_output)
        p.readyReadStandardError.connect(lambda: self.log.appendPlainText(bytes(p.readAllStandardError()).decode('utf-8', errors='replace')))
        p.errorOccurred.connect(self.process_error)
        p.finished.connect(self.finished)
        arguments=['-u',str(Path(__file__).with_name('emulator_worker.py')),
                   '--mask-rom',self.mask_path,'--firmware-rom',self.firmware_path,
                   '--mode',self.rom_mode,'--layout',self.rom_layout]
        if self.cartridge_path and not self.basic_available:arguments+=['--cartridge-rom',self.cartridge_path]
        p.start(worker_python(),arguments)

    def run_editor(self):
        if not self.mask_path or not self.firmware_path:
            if not self.choose_roms():return
        # Validate selection before deciding whether F5 means BASIC injection.
        if self.mask_path and self.firmware_path:
            try:
                from rom_images import load_roms
                _,_,_,info=load_roms(self.mask_path,self.firmware_path,self.rom_mode,self.rom_layout)
                self.set_machine_mode(info['basic_available'])
            except (OSError,ValueError) as exc:
                self.log.appendPlainText(str(exc));return
        if not self.basic_available:
            if not self.process:self.start()
            else:self.write({'op':'pause','value':False})
            self.log.appendPlainText(tr('Mode ROM générique : F5 démarre ou reprend la machine sans injecter le programme BASIC.'))
            return
        source = self.source()
        a = analyze(source)
        if a.issues:
            self.log.appendPlainText(tr('Corriger le programme avant exécution : ')+str(a.issues))
            return
        if not self.process:
            self.start(source)
            return
        self.audio.stop()
        self.log.appendPlainText(tr('Chargement du programme de l’éditeur ; pas de redémarrage si le BASIC est déjà prêt.'))
        if self.worker_ready:self.write({'op':'run','source':source})
        else:self.pending_source=source
        self.lcd.setFocus()

    def reset(self):
        if self.process:self.start()

    def read_output(self):
        self.buffer.extend(bytes(self.process.readAllStandardOutput()))
        while b'\n' in self.buffer:
            line, _, self.buffer = self.buffer.partition(b'\n')
            try:
                data = json.loads(line)
            except ValueError:
                self.log.appendPlainText(line.decode('utf-8', errors='replace'))
                continue
            if data['type'] == 'ready':
                self.worker_ready=True
                self.log.appendPlainText((tr('Moteur ') + f'{data.get('version', 'ancien')}' + tr(' ; temporisations sonores : ') + f'{data.get('realtime_sound', False)}'))
                if data.get('roms'):self.set_machine_mode(data['roms']['basic_available'])
                if data.get('roms'):self.log.appendPlainText(json.dumps(data['roms'],ensure_ascii=False,indent=2))
                if data.get('cartridge'):self.log.appendPlainText(json.dumps(data['cartridge'],ensure_ascii=False,indent=2))
                if data.get('version')!=VERSION:
                    self.log.appendPlainText(tr('Versions différentes : fermer puis relancer Studio.'))
                if self.pending_source is not None and self.basic_available:
                    self.write({'op':'run', 'source':self.pending_source})
                self.pending_source = None
                self.write(dict(op='sound_scale',value=self.sound_duration.currentData()))
            elif data['type'] == 'error':
                self.status.setText(tr('Erreur du moteur (voir journal). Réinitialiser ou arrêter.'))
                self.log.appendPlainText(data['message'])
            elif data['type'] == 'paper_reset':self.paper.clear()
            elif data['type'] == 'paper':self.paper.add(data['columns'])
            elif data['type'] == 'debug':
                self.debug_pending=False
                self.debug_registers.setText(data['registers'])
                self.debug_flags.setText(data.get('flags',''))
                self.update_debug_view(self.debug_memory,data['memory'],True)
                self.update_debug_view(self.debug_code,data['assembly'],True)
            elif data['type'] == 'audio':
                if not data.get('stop') and 'gate' not in data:
                    self.log.appendPlainText(f"SOUND : {data['ms']} ms — "+('silence' if data['mode']==2 else f"modulation {data['hz']} Hz"))
                if data.get('stop'):self.audio.stop()
                else:
                    warning=self.audio.play(data)
                    if warning and warning!=self.audio_warning:
                        self.log.appendPlainText(warning);self.audio_warning=warning
            elif data['type'] == 'screen':
                self.last_state = data
                self.code_button.blockSignals(True)
                self.code_button.setChecked(bool(data.get('code_active',False)))
                self.code_button.blockSignals(False)
                key=data.get('last_inkey')
                if key is not None:
                    arrow={18:tr('← gauche'),19:tr('→ droite')}.get(key,str(key))
                    self.key_status.setText((tr('Historique INKEY : ') + f'{arrow}' + ' • ' + f'{data.get('key_count', 0)}' + tr(' entrée(s) • maintenue : ') + f'{data.get('held_key', 0)}' + tr(' • texte en attente : ') + f'{data.get('queued_keys', 0)}'))
                else:
                    self.key_status.setText((tr('Historique INKEY : aucune entrée • maintenue : ') + f'{data.get('held_key', 0)}' + tr(' • texte en attente : ') + f'{data.get('queued_keys', 0)}'))
                if not self.basic_available:self.key_status.setText(tr('Clavier Canon : F7 = CODE, F8 = MODE, F9 = KB - I/II.'))
                self.lcd.state = data
                self.lcd.update()
                self.paused = data['paused']
                self.status.setText((tr('En pause') if self.paused else tr('En exécution / attente clavier'))+
                    (' — PC $' + f'{data['pc']}' + tr(' — travaux papier simulés : ') + f'{data['jobs']}' + tr(' — attente son : ') + f'{data.get('sound_remaining_ms', 0)}' + ' ms'))
                if not self.basic_available:
                    self.status.setText(('PC $'+data['pc']+' — ')+tr(data.get('diagnostic','')))

    def set_machine_mode(self, basic):
        self.basic_available=basic
        self.update_cartridge_label()
        self.lcd.native_mode=not basic
        self.entry.setEnabled(basic)
        self.matrix_panel.setVisible(not basic)
        self.lcd.setToolTip(tr('Cliquer sur le LCD pour taper. F7 = CODE, F8 = MODE, F9 = KB - I/II ; Échap = MARGIN RELEASE/BREAK. Les fonctions des touches dépendent du firmware.'))

    def toggle_code(self):
        self.lcd.setFocus()
        self.write(dict(op="code_toggle"))

    def special_press(self, code):
        self.lcd.setFocus()
        if self.basic_available and code==0x36:self.write(dict(op='break'))
        else:self.write(dict(op='host_matrix',keys=[code]))

    def matrix_press(self):
        try:
            key=int(self.matrix_code.text(),16)
            if not 0<=key<64:raise ValueError()
        except ValueError:
            self.log.appendPlainText(tr('Code matriciel hexadécimal attendu : 00 à 3F.'));return
        keys=[key]
        if self.matrix_code_modifier.isChecked():keys.append(0x3b)
        self.write(dict(op='host_matrix',keys=keys,shift=self.matrix_shift.isChecked()))

    def matrix_release(self):
        self.write(dict(op='host_matrix',keys=[],shift=False))

    @staticmethod
    def update_debug_view(view,text,preserve_scroll):
        if view.toPlainText()==text:return
        vertical=view.verticalScrollBar().value();horizontal=view.horizontalScrollBar().value()
        cursor=view.textCursor();position=cursor.position();anchor=cursor.anchor()
        view.setPlainText(text)
        if preserve_scroll:
            from PySide6.QtGui import QTextCursor
            cursor=view.textCursor();cursor.setPosition(min(anchor,len(text)))
            cursor.setPosition(min(position,len(text)),QTextCursor.MoveMode.KeepAnchor)
            view.setTextCursor(cursor)
            view.verticalScrollBar().setValue(vertical)
            view.horizontalScrollBar().setValue(horizontal)

    def refresh_debug_live(self):
        if self.details.currentIndex()==1 and self.debug_live.isChecked():
            self.request_debug()

    def request_debug(self):
        if self.debug_pending or not self.process or self.process.state()!=QProcess.ProcessState.Running:return
        try:address=int(self.debug_address.text(),16)
        except ValueError:
            self.debug_registers.setText(tr('Adresse hexadécimale attendue : 0000 à FFFF.'));return
        self.debug_pending=True
        self.write(dict(op='debug',address=address))

    def change_audio_output(self):
        self.audio.stop()
        self.audio.device_id=self.audio_output.currentData()

    def test_audio(self):
        if not self.audio.enabled:
            self.log.appendPlainText(tr('Activer Son du buzzer dans le menu Émulation.'))
            return
        warning=self.audio.play(dict(hz=440,ms=800,mode=1))
        self.log.appendPlainText(warning or tr('Test sonore : ')+self.audio_output.currentText())

    def send_key(self, value):
        if not self.basic_available:
            code=BUTTON_KEYS.get(value)
            if code is not None:self.write(dict(op='host_matrix',keys=[code],shift=False))
            self.lcd.setFocus();return
        self.lcd.setFocus()
        if value == 3:self.audio.stop()
        self.write({'op':'break'} if value == 3 else {'op':'key_press', 'value':value})

    def release_key(self, value=0):
        if self.basic_available:self.write(dict(op='held_key',value=value))
        else:self.write(dict(op='host_matrix',keys=[],shift=False))

    def send_line(self):
        if not self.basic_available:return
        text = self.entry.text()
        if any(not 32 <= ord(c) < 127 for c in text):
            self.log.appendPlainText(tr('Le clavier BASIC attend du texte ASCII.'))
            return
        if self.process:
            self.write({'op':'keys', 'values':list((text+'\r').encode('ascii'))})
            self.entry.clear()

    def pause(self):
        self.paused = not self.paused
        self.audio.pause(self.paused)
        self.write({'op':'pause', 'value':self.paused})

    def stop(self):
        # Stop means freeze, preserving CPU/RAM/LCD and the paper preview.
        if self.process:
            self.paused=True;self.audio.pause(True)
            self.write({'op':'pause','value':True})

    def power_off(self):
        self.audio.stop()
        if self.process:
            self.process.kill()
            self.process.waitForFinished(1500)
        else:self.finished()

    def process_error(self, error):
        if self.process:
            self.log.appendPlainText(self.process.errorString())
        if error == QProcess.ProcessError.FailedToStart:
            self.finished()

    def finished(self, *args):
        self.worker_ready=False
        self.code_button.setChecked(False)
        self.lcd.native_pressed.clear()
        self.power.blockSignals(True);self.power.setChecked(False);self.power.blockSignals(False)
        self.debug_pending=False
        self.audio.stop()
        if self.process:
            self.process.deleteLater()
            self.process = None
        self.status.setText(tr('OFF — le programme de l’éditeur et l’aperçu papier sont conservés.'))
        self.lcd.state=dict(cells=[32]*32,cgram=[0]*64,lower=[32]*32,control=0)
        self.lcd.update()
