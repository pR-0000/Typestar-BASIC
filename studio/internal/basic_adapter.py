"""Optional conveniences for known Typestar BASIC builds.

Contains symbol/PC-based hooks, program injection, keyboard and sound shortcuts.
The generic machine never imports this module.
"""
import time
from collections import deque
from hd6301 import HD6301CPU
from core import analyze, codec

def basic_backend(realtime_sound=False, mask_path=None, firmware_path=None, cold_start=False, layout='auto'):
    from emulator_cpu import configure, StageCPU
    GameCPU, s = configure(mask_path, firmware_path, layout=layout)
    traced = {0x76e7, s['LCDPUT'], 0x7563, s['GPWAIT'], s['RBJOB'], s['GPPRINT'], s['SNDPREP'], 0x8ee6}

    class InteractiveCPU(GameCPU):
        symbols = s
        basic_available = True
        def __init__(self, source=''):
            self.pending_program = None
            self.auto_run = False
            self.boot_complete = not cold_start
            self.paper_events=[]
            self.matrix_keys=set()
            self.matrix_shift=False
            self.matrix_events=deque()
            self.matrix_ticks=0
            self.matrix_next=0
            self.matrix_scans=0
            self.matrix_scanning=False
            self.matrix_value=0
            self.code_latched=False
            self.logical_raw=False
            self.live = False
            super().__init__()
            from paper_fast import kernels
            self.paper_kernels=kernels(self.m)
            self.paper_fast=True
            self.pc = 0x6829
            if not cold_start:
                self.idle(); self.command(''); self.command('')
            else:
                # Canon startup has executed from the selected reset vector.
                # Carry its register state and actual LCD writes into BASIC.
                from emulator_cpu import boot
                for reg in ('a','b','x','sp','pc','c','z','n','v','i'):
                    setattr(self,reg,getattr(boot,reg))
                self.lcd[:] = boot.lcd
                self.cgram[:] = boot.cgram
                self.lcd_address = boot.lcd_address
                self.lcd_control = boot.lcd_control
                self.cgram_selected = boot.cgram_selected
            self.live = True
            self.break_requested = False
            self.sound_until = 0.0
            self.sound_scale = 1.0
            self.audio_events = []
            self.last_inkey = None
            self.key_count = 0
            self.held_key = 0
            self.accepting_text = True
            self.pending_program = source if cold_start and source else None
            if source and not cold_start:
                self.install_program(source)

        def install_program(self, source):
            analysis = analyze(source)
            if analysis.issues:
                raise ValueError(str(analysis.issues))
            packed = codec.pack(analysis.records)
            start = s['PROGRAM']
            self.m[start:start+len(packed)] = packed
            self.m[s['PEND']:s['PEND']+2] = (start+len(packed)-1).to_bytes(2, 'big')
            self.input.extend(b'RUN\r')

        def request_run(self, source):
            analysis=analyze(source)
            if analysis.issues:raise ValueError(str(analysis.issues))
            if not self.boot_complete:
                self.pending_program=source
                self.auto_run=True
                return
            # Debugger-style restart of the BASIC console, NOT a machine reset.
            # READY restores the interpreter stack; RUN clears its variables.
            # RAM outside the program/variable arenas, motors and paper survive.
            self.pending_program=None
            self.input.clear();self.held_key=0;self.break_requested=False
            self.host_matrix([],cancel=True)
            self.sound_until=0;self.audio_events.append({'stop':True})
            self.m[s['IKPENDING']]=0
            self.pc=s['READY']
            self.install_program(source)

        def host_matrix(self, keys, shift=False, cancel=False):
            if any(type(k) is not int or not 0<=k<64 for k in keys):
                raise ValueError('Matrix codes must be 00..3F')
            if cancel:
                self.matrix_events.clear();self.matrix_keys.clear()
                self.matrix_next=0;self.matrix_value=0;self.code_latched=False
                self.matrix_shift=False;self.logical_raw=False;self.matrix_scans=0
                return
            if len(self.matrix_events)>=128:raise ValueError('Keyboard input is full')
            self.matrix_events.append((set(keys),bool(shift)))

        def toggle_code(self):
            # BASIC uses a held CODE chord, unlike Canon's latched CODE mode.
            self.code_latched=not self.code_latched

        def raw_keys(self):
            return self.matrix_keys | ({0x3b} if self.code_latched else set())

        def read(self, address):
            if address==0x30:
                value=255
                for key in self.raw_keys():
                    if self.m[0x31]==255^(1<<(key//8)):value&=~(1<<(key%8))
                return value
            if address==0x32:
                return (self.m[address]&127)|(128 if self.matrix_shift else 0)
            return super().read(address)

        def key_position(self, value):
            # Invert the selected firmware's keyboard-I delta maps. This keeps
            # host typing independent of the physical regional layout while II
            # and CODE are translated by the real firmware scanner.
            table=s.get('KDTABLE')
            locale=self.m[s['KLOCALE']]
            if table is None or locale>=10:return None
            for shifted in (False,True):
                for key in range(44):
                    ptr=self.word(table+2*(locale*4+int(shifted)))
                    for _ in range(2000):
                        tag=self.m[ptr]
                        if tag==255:
                            char=self.m[ptr+1+key];break
                        if tag==254:ptr=self.word(ptr+1);continue
                        if tag==key:char=self.m[ptr+1];break
                        ptr+=2
                    else:continue
                    if char==value:return key,shifted
            return None

        def release_logical(self, value):
            if self.logical_raw:
                self.host_matrix([]);self.logical_raw=False
            self.held_key=value

        def step(self):
            self.matrix_ticks+=1
            if self.paper_fast and self.pc in self.paper_kernels:
                self.paper_kernels[self.pc](self)
                return
            if (self.matrix_events and self.matrix_ticks>=self.matrix_next and
                (self.matrix_scans>=2 or (not self.raw_keys() and self.m[s['KHELD']]==255))):
                self.matrix_keys,self.matrix_shift=self.matrix_events.popleft()
                self.matrix_value=0;self.matrix_scans=0
                self.matrix_next=self.matrix_ticks+16000
            if self.matrix_scanning and self.pc==s['KBDRETURN']:
                self.matrix_scans+=1
                if self.a:self.matrix_value=self.a
                if self.code_latched and self.a in (0x11,0x16,0x3c,0x3e):
                    self.code_latched=False
                self.matrix_scanning=False
            # F5 dismisses welcome waits while allowing the real boot to finish.
            # Plain ON/reset leaves those waits interactive.
            if self.auto_run and not self.boot_complete and self.pc==s['GETC'] and not self.input:
                self.input.append(13)
            if self.pc==s['READY'] and not self.m[s['BOOTFLAG']]:self.boot_complete=True
            if self.pending_program is not None and self.boot_complete and self.pc==s['GETC']:
                source=self.pending_program;self.pending_program=None
                self.auto_run=False
                self.install_program(source)
            if self.live and self.pc==0x76e7:
                a,b,c=self.m[0x66:0x69]
                # Keep all 24 native channels: the 16-row graphics projection
                # discards a[0:4] and c[4:8], including the top of 5/7.
                word=a|(b<<8)|(c<<16)
                if word:self.paper_events.append([self.xy[0],self.xy[1],word])
            if self.live and realtime_sound:
                if self.sound_until:
                    if self.break_requested:
                        self.sound_until=0;self.break_requested=False
                        self.audio_events.append({'stop':True})
                        self.pc=s['SNDBREAK']
                    elif time.monotonic()<self.sound_until:return
                    else:self.sound_until=0
                if self.pc==s['SNDPREP']:
                    hz=self.word(s['SNDHZ']);ms=self.word(s['SNDLEFT'])
                    ms=round(ms*self.sound_scale)
                    mode=self.m[s['SNDMODE']]
                    self.audio_events.append(dict(hz=hz,ms=ms,mode=mode))
                    self.sounds.append((hz,ms))
                    self.sound_until=time.monotonic()+ms/1000
                    self.pc=s['SNDSTOP']
                    return
            if self.live and self.pc in (s['KBDPOLL'], s['KBDFAST']):
                physical=bool(self.raw_keys() or self.matrix_events or self.m[s['KHELD']]!=255)
                if physical and not self.break_requested:
                    self.matrix_scanning=True
                    # Bypass only the host's ASCII shortcut, execute the actual
                    # polling/translation code in the selected BASIC ROM.
                    HD6301CPU.step(self)
                    return
                if self.break_requested:
                    self.a = 3
                    self.break_requested = False
                elif self.pc == s['KBDPOLL']:
                    self.a = self.input.popleft() if self.input else 0
                    self.accepting_text = not bool(self.a)
                else:
                    self.a = 0
                self.z = self.a == 0
                self.pc = self.pop()*256+self.pop()
                return
            if self.live and self.pc == 0x8ee6:
                self.accepting_text=False
            if self.live and self.pc == 0x8ef0:
                # Sample current physical state at the actual INKEY return.
                # Never consume the separate command/INPUT text buffer here.
                self.m[s['IKPENDING']]=self.matrix_value if self.raw_keys() else self.held_key
            # Count actual nonzero returns, not attempted injections or idle polls.
            if self.live and self.pc == 0x8ef0 and self.m[s['IKPENDING']]:
                self.last_inkey = self.m[s['IKPENDING']]
                self.key_count += 1
            if self.pc in traced:super().step()
            else:StageCPU.step(self)

        def key_press(self,value):
            if self.code_latched or 0x3b in self.matrix_keys or self.m[s['KMODE']]:
                special={8:0x2f,13:0x2d,18:0x31,19:0x32,20:0x38,21:0x39,32:0x2c}
                position=(special[value],False) if value in special else self.key_position(value)
                if position is not None:
                    self.host_matrix([position[0]],position[1]);self.logical_raw=True
                    return
            self.held_key=value
            if self.accepting_text and len(self.input)<256:self.input.append(value)

        def request_break(self):
            self.host_matrix([],cancel=True)
            self.held_key=0
            self.input.clear()
            self.m[s['IKPENDING']]=0
            self.break_requested=True

        def snapshot(self, paused):
            return dict(type='screen', cells=list(self.lcd[:32]),
                        cgram=list(self.cgram), lower=list(self.lcd[0x40:0x60]),
                        control=self.lcd_control, address=self.lcd_address,
                        cgram_selected=self.cgram_selected,
                        pc=f'{self.pc:04X}', paused=paused, boot_complete=self.boot_complete, jobs=self.jobs,
                        code_active=self.code_latched or 0x3b in self.matrix_keys, keyboard_mode=self.m[s['KMODE']],
                        sound_remaining_ms=max(0,round((self.sound_until-time.monotonic())*1000)), sounds=len(self.sounds), last_inkey=self.last_inkey, key_count=self.key_count, held_key=self.held_key, queued_keys=len(self.input), screen=bytes(self.lcd[:32]).decode('ascii', errors='replace'))

    return InteractiveCPU
