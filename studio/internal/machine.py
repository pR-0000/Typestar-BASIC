"""Experimental S-70 hardware machine, with no firmware-address hooks.

Runs from the supplied maskROM reset vector. LCD and keyboard use I/O registers.
Timers, interrupts, phase outputs and an ideal home sensor drive native firmware.
Timing is functional, not cycle accurate; paper is derived from the head latch.
"""
from collections import deque
from hd6301 import HD6301CPU
from i18n import tr
from machine_devices import Timer1, Mechanics, ThermalHead, BuzzerGate


class GenericMachine(HD6301CPU):
    basic_available = False
    symbols = {}

    def __init__(self, image, mask, mechanics=True, cartridge=None, configuration=0x10):
        if len(image) != 32768 or len(mask) != 16384:
            raise ValueError('Expected 32 KiB external ROM and 16 KiB maskROM')
        super().__init__(image)
        self.m[:0x4000] = bytes(0x4000)
        self.m[0xc000:] = mask
        self.pc = int.from_bytes(mask[-2:], 'big')
        self.sp = 0x00ff
        self.cartridge = cartridge
        if type(configuration) is not int or not 0<=configuration<=255:
            raise ValueError('IC5 configuration must be a byte')
        # Input straps: low nibble = keyboard locale; bit 4 = calculator fitted.
        # S-70 defaults retain locale 0 and advertise its native calculator.
        self.configuration=configuration
        self.m[0x3c]=configuration
        self.input = deque()
        self.held_key = 0
        self.sound_until = 0.0
        self.sound_scale = 1.0
        self.audio_events = []
        self.paper_events = []
        self.instructions = 0
        self.io_reads = {}
        self.io_writes = {}
        self.waiting = None
        self.boot_complete = False  # Unknown firmware has no generic "ready" PC.
        self.jobs = 0
        self.hardware_timing=mechanics
        self.timer=Timer1()
        self.mechanics=Mechanics()
        self.head=ThermalHead()
        self.buzzer=BuzzerGate()
        self.lcd_off_since=None
        self.lcd_retained=None
        self.matrix_events=deque()
        self.matrix_next=0
        self.elapsed_clocks=0
        self.capture_period=8000
        self.next_capture=self.capture_period
        self.irq_counts={}
        self.timer2_clocks=0
        self.wait_stacked=False
        self.asic_busy_until=0

    def read(self, address):
        if address==0x3c:return self.configuration
        if address < 0x40:
            self.io_reads[address] = self.io_reads.get(address, 0) + 1
        if self.hardware_timing:
            if address in (8,9,10,11,12,13,14,15,25,26):return self.timer.read(address)
            if address==0x32:
                return (self.m[address]&31) | (64 if self.mechanics.x>0 else 0) | (128 if self.modifier else 0)
            if address==0x1b:return self.m[address]
            if address==0x34:
                return (self.m[address]&127)|(128 if self.elapsed_clocks<self.asic_busy_until else 0)
        # Same functional timer-completion assumption as the existing startup
        # harness, expressed at the register interface instead of a ROM address.
        if address == 8:return self.m[address] | 0x40
        if address == 0x1b:return self.m[address] | 0x80
        # IC5 font select overlays only the observed resource window.
        if 0x4000<=address<0x6800 and self.m[0x37]&128:
            return self.cartridge.read(address) if self.cartridge else 255
        # External RAM cartridge banks remain absent.
        if 0x2000 <= address < 0x4000 and self.m[0x36] in (1, 2):return 255
        if 0x3800 <= address < 0x4000:return 255
        return super().read(address)

    def write(self, address, value):
        if address==0x3c:return  # Hardware configuration input, not RAM.
        if self.hardware_timing:
            if address==0x34:
                self.audio_events.extend(self.buzzer.update(bool(value&64),self.elapsed_clocks))
            if address==0x38 and 8<=value<=15:
                if not value&4 and self.lcd_control&4:
                    self.lcd_retained=self.lcd_frame()
                    self.lcd_off_since=self.elapsed_clocks
                elif value&4:
                    self.lcd_off_since=None;self.lcd_retained=None
            if address in (8,9,10,11,12,13,14,15,25,26):
                if address==15:
                    event=self.head.heat(value,self.mechanics.x,self.mechanics.y)
                    if event:self.paper_events.append(event)
                self.timer.write(address,value)
                self.m[address]=self.timer.read(address) if address in (11,12,25,26) else value&255
                return
            if address==0x17:self.mechanics.drive(value&255)
            if address==0x34 and value&128:
                # Serial data latches on the control strobe; output 2 gates heat.
                self.head.strobe(self.m[0x33])
                self.asic_busy_until=self.elapsed_clocks+8
            if address==0x1b:
                self.m[address]=(self.m[address]&value&128)|(value&0x7f)
                return
        if address >= 0x4000:return  # Physical ROM is read-only.
        if address < 0x40:
            self.io_writes[address] = self.io_writes.get(address, 0) + 1
        if 0x2000 <= address < 0x4000 and self.m[0x36] in (1, 2):return
        if 0x3800 <= address < 0x4000:return
        if address >= 0x100:
            self.m[address] = value & 255
            self.writes.add(address)
            return
        super().write(address, value)

    def push_interrupt_frame(self):
        cc=0xc0|int(self.c)|(int(self.v)<<1)|(int(self.z)<<2)|(int(self.n)<<3)|(int(self.i)<<4)
        for value in (self.pc&255,self.pc>>8,self.x&255,self.x>>8,self.a,self.b,cc):self.push(value)

    def clock_hardware(self,clocks=4):
        self.elapsed_clocks+=clocks
        if self.matrix_events and self.elapsed_clocks>=self.matrix_next:
            keys,shift=self.matrix_events.popleft()
            self.set_matrix(keys,shift)
            # Two stable scans plus debounce/release time. Host taps must not
            # disappear when press/release arrive in one worker batch.
            self.matrix_next=self.elapsed_clocks+64000
        self.timer.tick(clocks)
        if self.elapsed_clocks>=self.next_capture:
            self.timer.capture_edge()
            self.next_capture+=self.capture_period
        # Timer 2 internal clocks; used for short polling delays by Canon.
        mode=self.m[0x1b]&3
        if self.m[0x1b]&16 and mode<3:
            self.timer2_clocks+=clocks
            divisor=(1,8,128)[mode]
            ticks,self.timer2_clocks=divmod(self.timer2_clocks,divisor)
            for _ in range(ticks):
                self.m[0x1d]=(self.m[0x1d]+1)&255
                if self.m[0x1d]==self.m[0x1c]:
                    self.m[0x1d]=0;self.m[0x1b]|=128

    def step(self):
        if self.hardware_timing:
            self.clock_hardware()
            vector=self.timer.pending()
            if vector is None and self.m[0x1b]&0xc0==0xc0:vector=0xffec
            if vector is not None and self.waiting=='SLP':self.waiting=None
            if vector is not None and not self.i:
                if not self.wait_stacked:self.push_interrupt_frame()
                self.wait_stacked=False;self.waiting=None;self.i=True
                self.pc=self.word(vector)
                self.irq_counts[vector]=self.irq_counts.get(vector,0)+1
                return
        if self.waiting:return
        op=self.m[self.pc]
        if op in (0x1a,0x3e):
            self.waiting='SLP' if op==0x1a else 'WAI'
            self.pc=(self.pc+1)&65535
            if op==0x3e:self.push_interrupt_frame();self.wait_stacked=True
        else:super().step()
        self.instructions+=1

    def set_matrix(self, keys, shift=False):
        if any(not isinstance(k, int) or not 0 <= k < 64 for k in keys):
            raise ValueError('Matrix codes must be 00..3F')
        self.keys = set(keys)
        self.modifier = bool(shift)

    def host_matrix(self, keys, shift=False, cancel=False):
        if any(type(k) is not int or not 0<=k<64 for k in keys):
            raise ValueError('Matrix codes must be 00..3F')
        if cancel:
            self.matrix_events.clear();self.matrix_next=0;self.set_matrix([],False)
            return
        if len(self.matrix_events)>=128:raise ValueError('Native keyboard input is full')
        self.matrix_events.append((list(keys),bool(shift)))

    def key_press(self, value):
        raise ValueError(tr('Mode ROM générique : utiliser le clavier matriciel.'))

    def request_break(self):
        self.host_matrix([0x36]);self.host_matrix([])

    def request_run(self, source):
        raise ValueError(tr('Injection BASIC indisponible en mode ROM générique. Utiliser ON/OFF et Pause / reprise.'))

    def lcd_frame(self):
        return dict(cells=list(self.lcd[:32]),cgram=list(self.cgram),
                    lower=list(self.lcd[0x40:0x60]),control=self.lcd_control,
                    address=self.lcd_address,cgram_selected=self.cgram_selected)

    def snapshot(self, paused):
        reads = sorted(self.io_reads.items(), key=lambda p:p[1], reverse=True)[:4]
        diagnostic = tr('Mécanique, papier et buzzer simulés (temporisations approximatives).')
        if self.waiting:diagnostic += ' ' + self.waiting
        # Canon blanks the LCD for ~12 ms while rewriting DDRAM. Preserve
        # the completed image briefly, approximating glass response/persistence.
        # Long display-off requests still blank the screen; bus reads stay raw.
        frame=self.lcd_frame()
        if self.lcd_retained is not None and self.elapsed_clocks-self.lcd_off_since<32000:
            frame=self.lcd_retained
        return dict(type='screen', **frame,
                    pc=f'{self.pc:04X}', paused=paused, boot_complete=False,
                    basic_available=False, jobs=0, sound_remaining_ms=0, sounds=0,
                    code_active=self.lcd[0x51]==178,
                    last_inkey=None, key_count=0, held_key=0, queued_keys=0,
                    instructions=self.instructions, diagnostic=diagnostic,
                    io_reads={f'{a:02X}':n for a,n in reads},
                    mechanics=dict(x=self.mechanics.x, y=self.mechanics.y,
                                   x_steps=self.mechanics.x_steps, y_steps=self.mechanics.y_steps),
                    interrupts={f'{v:04X}':n for v,n in self.irq_counts.items()},
                    screen=bytes(self.lcd[:32]).decode('ascii', errors='replace'))
