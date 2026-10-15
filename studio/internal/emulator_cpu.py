"""Optional BASIC firmware adapter, sharing the HD6301 instruction core.

This functional model supplies BASIC-specific conveniences, not electrical or
cycle-accurate emulation. ROM files must be selected explicitly or configured.
"""
import os
from collections import deque
from core import ROOT
from hd6301 import HD6301CPU as CPU

S = s = {}
IMAGE = MASK = b''
boot = None


def configure(mask_path=None, firmware_path=None, layout='auto'):
    global S, s, IMAGE, MASK, boot
    from machine import GenericMachine
    from rom_images import load_roms
    # Defaults are reserved for offline regression tests; desktop passes both paths.
    mask_path = mask_path or os.environ.get('TYPESTAR_MASK_ROM')
    if not mask_path:raise ValueError('Select a maskROM file before starting the emulator')
    firmware_path = firmware_path or os.environ.get('TYPESTAR_TEST_FIRMWARE') or os.environ.get('TYPESTAR_BASIC_ROM')
    if not firmware_path:raise ValueError('Select a BASIC firmware file before starting the emulator')
    IMAGE,MASK,S,_ = load_roms(mask_path,firmware_path,mode='basic',layout=layout)
    s = S
    class BasicStartupMachine(GenericMachine):
        def step(self):
            # Legacy BASIC fast-start convenience, deliberately outside the
            # generic machine: skip the known maskROM carriage homing service.
            if self.pc == 0xf2da:
                self.pc = self.pop()*256 + self.pop()
                return
            super().step()
    boot = BasicStartupMachine(IMAGE, MASK, mechanics=False)
    for _ in range(2000000):
        if boot.pc == 0x6829:break
        boot.step()
    else:raise RuntimeError(f'BASIC startup timeout at ${boot.pc:04X}')
    return GameCPU, s


class DecimalCPU(CPU):
    def __init__(self):
        super().__init__(IMAGE);self.m[0xC000:]=MASK;self.input=deque()

    def write(self,address,value):
        if address==0x18E5:
            self.writes.add(address);self.m[address]=value&255;return
        super().write(address,value)

    def step(self):
        if self.pc in (S['KBDPOLL'],S['KBDFAST']):
            if self.pc==S['KBDFAST']:self.a=0 # Queued test text belongs to blocking INPUT, not RUN polling.
            elif self.input and self.word(self.sp+3)==S['RESULTKEY']+3:self.a=13
            else:self.a=self.input.popleft() if self.input else 0
            self.z=self.a==0;self.pc=self.pop()*256+self.pop();return
        super().step()

    def idle(self):
        for _ in range(1500000):
            if self.pc==S['GETC'] and not self.input:return
            self.step()
        raise AssertionError(f'No keyboard wait at {self.pc:04X}')

    def command(self,text):
        self.input.extend((text+'\r').encode());self.idle()

    def screen(self):return bytes(self.lcd[:32]).decode('latin1').strip()


class StageCPU(DecimalCPU):
    def __init__(self):
        super().__init__()
        self.frames=[]

    def write(self,address,value):
        if 0x100<=address<0x1900:
            self.m[address]=value&255;self.writes.add(address);return
        super().write(address,value)



class GameCPU(StageCPU):
    def __init__(self):
        super().__init__()
        self.m[:0x4000] = boot.m[:0x4000]
        self.keys = deque()
        self.screens = []
        self.min_free = 5951
        self.jobs = self.tiles = 0
        self.sounds = []
        self.map_tiles = []
        self.lcd_characters = []
        self.xy = [0,0]
        self.paper_heat_y = []
        self.columns = bytearray()

    def fetch(self):
        # Instruction fetches in RAM/ROM cannot touch memory-mapped I/O.
        pc=self.pc
        value=self.m[pc] if pc>=0x100 else self.read(pc)
        self.pc=(pc+1)&65535
        return value

    def write(self,address,value):
        if 0x100<=address<0x3800:
            self.m[address]=value&255;self.writes.add(address);return
        super().write(address,value)

    def read(self, a):
        if a>=0x100:return self.m[a]
        if a == 0x30: return 255
        if a == 8: return self.m[a] | 64
        if a == 15: return self.m[a] | 32
        if a == 52: return self.m[a] & 127
        return super().read(a)

    def step(self):
        if self.pc == 0x76e7: self.columns.extend(self.m[0x66:0x69])
        if self.pc == s['LCDPUT']: self.lcd_characters.append(self.a)
        if self.pc == 0x7563:
            self.xy[bool(self.m[65]&32)] += -1 if self.m[65]&16 else 1
        if self.pc == s['GPWAIT']: self.m[9:11] = self.m[11:13]
        if self.pc == s['RBJOB']: self.jobs += 1
        if self.pc == s['GPPRINT']:
            self.paper_heat_y.append(self.xy[1])
            self.tiles += 1
            if self.m[s['LPMODE']] == 0:
                p = self.word(s['GXPATPTR'])
                self.map_tiles.append(bytes(self.m[p:p+64]).hex())
        if self.pc == s['SNDPREP']:
            self.sounds.append((self.word(s['SNDHZ']), self.word(s['SNDLEFT'])))
        if self.pc == 0x8EE6 and self.keys:
            self.m[s['IKPENDING']] = self.keys.popleft()
        super().step()

    def idle(self):
        for _ in range(45000000):
            if not self.input and not self.keys and self.pc in (s['GETC'], 0x8EE6):
                screen = self.screen()
                assert getattr(self,'allow_errors',False) or not screen.startswith('?'), (screen, self.jobs)
                self.screens.append(screen)
                if self.pc == 0x8EE6:
                    self.min_free = min(self.min_free,
                        self.word(s['DHEAP']) - self.word(s['DFLOOR']))
                return
            self.step()
        raise AssertionError(('timeout', hex(self.pc), self.screen(), self.jobs))
