"""Register-driven functional timers and steppers; no firmware PC/RAM hooks.

Timer register semantics: Hitachi HD63701Y0 datasheet pp. 751–757.
Time is currently four E clocks per instruction, not instruction-cycle exact.
The ASIC keyboard capture cadence (8 ms) and ideal home sensor are assumptions.
"""

class Timer1:
    def __init__(self):
        self.counter=0
        self.compare=[0xffff,0xffff]
        self.capture=0
        self.control1=self.control2=0
        self.flags=0  # ICF=80, OCF1=40, TOF=20, OCF2=10 internally
        self.seen=0
        self.low_latch=0

    def event(self,flag):
        self.flags |= flag
        self.seen &= ~flag  # A later event cannot be cleared using an old read.

    def tick(self,clocks):
        before=self.counter
        for index,flag in ((0,0x40),(1,0x10)):
            distance=(self.compare[index]-before)&65535
            if 0 < distance <= clocks or clocks>=65536:self.event(flag)
        if before+clocks>=65536:self.event(0x20)
        self.counter=(before+clocks)&65535

    def capture_edge(self):
        self.capture=self.counter
        self.event(0x80)

    def clear_seen(self,flag):
        if self.seen & flag:self.flags &= ~flag
        self.seen &= ~flag

    def read(self,a):
        if a==8:
            self.seen |= self.flags & 0xe0
            return self.control1 | (self.flags & 0xe0)
        if a==15:
            self.seen |= self.flags & 0xd0
            return self.control2 | (self.flags & 0xc0) | ((self.flags & 0x10)<<1)
        if a==9:
            self.clear_seen(0x20);self.low_latch=self.counter&255
            return self.counter>>8
        if a==10:return self.low_latch
        if a==13:
            self.clear_seen(0x80);return self.capture>>8
        if a==14:return self.capture&255
        if a in (11,12,25,26):
            v=self.compare[int(a>=25)]
            return v>>8 if a in (11,25) else v&255
        raise KeyError(a)

    def write(self,a,v):
        v &= 255
        if a==8:self.control1=v&31
        elif a==15:self.control2=v&15
        elif a==9:self.counter=0xfff8 # 6801-family FRC write convention; not used by the native boot
        elif a==10:pass
        elif a in (11,12,25,26):
            index=int(a>=25)
            self.clear_seen(0x40 if index==0 else 0x10)
            self.compare[index]=((v<<8)|(self.compare[index]&255)) if a in (11,25) else ((self.compare[index]&0xff00)|v)
        elif a not in (13,14):raise KeyError(a)

    def pending(self):
        if self.flags&0x80 and self.control1&16:return 0xfff6
        if (self.flags&0x40 and self.control1&8) or (self.flags&0x10 and self.control2&8):return 0xfff4
        if self.flags&0x20 and self.control1&4:return 0xfff2
        return None


class Mechanics:
    X_PHASES=(12,4,6,2,3,1,9,8)
    Y_PHASES=(0xc0,0x60,0x30,0x90)
    def __init__(self):
        self.x=self.y=0
        self.x_phase=self.y_phase=None
        self.x_steps=self.y_steps=0
        self.home_changes=0

    def drive(self,value):
        for axis,phase,table,unit in (('x',value&15,self.X_PHASES,1),('y',value&0xf0,self.Y_PHASES,2)):
            if phase not in table:continue  # coils off retain rotor position
            index=table.index(phase);old=getattr(self,axis+'_phase')
            setattr(self,axis+'_phase',index)
            if old is None:continue
            delta=(index-old)%len(table)
            step=unit if delta==1 else -unit if delta==len(table)-1 else 0
            if step:
                before=self.x>0
                pos=getattr(self,axis)+step
                setattr(self,axis,max(0,pos) if axis=='x' else pos)
                setattr(self,axis+'_steps',getattr(self,axis+'_steps')+1)
                if axis=='x' and before!=(self.x>0):self.home_changes+=1


class ThermalHead:
    """24-bit serial head latch, committed by the Timer 1 output-2 gate.

    Register-level interpretation of the S-70 $33/$34 strobe and $0F gate.
    Each heating phase is additive ink; there is no Canon glyph/PC lookup.
    """
    def __init__(self):
        self.data=[]
        self.columns=0

    def strobe(self, value):
        self.data.append(value & 255)
        self.data=self.data[-3:]

    def heat(self, control, x, y):
        if control & 6 != 6 or len(self.data)!=3:return None
        a,b,c=self.data;self.data=[]
        word=a|(b<<8)|(c<<16)
        if word:
            self.columns+=1
            return [x,y,word]
        return None


class BuzzerGate:
    """IC5 bit 6 drives a live fixed-carrier audio gate.

    Duration metadata uses approximate emulated E clocks; the host audio stream
    keeps the carrier continuous between register transitions, even if Python
    executes fewer emulated clocks per real second than the physical CPU.
    """
    def __init__(self):
        self.on=False
        self.since=0

    def update(self, enabled, clocks):
        enabled=bool(enabled)
        if enabled==self.on:return []
        duration=0 if enabled else (clocks-self.since)/1000
        self.on=enabled
        if enabled:self.since=clocks
        return [dict(gate=enabled,hz=0,ms=duration,mode=0)]
