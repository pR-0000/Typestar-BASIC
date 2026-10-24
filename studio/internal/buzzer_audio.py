from i18n import tr
"""Approximate the measured 5.89 kHz buzzer, gated by BASIC SOUND.
No claim of acoustic identity: speaker/transistor resonance is not modeled.
"""
import math
from array import array
from PySide6.QtCore import QIODevice
from threading import Lock
from PySide6.QtMultimedia import QAudioSink, QAudioFormat, QMediaDevices

# Acoustic approximation based on measured amplitude modulation, not an electrical model.
# Carrier harmonics are negligible in HOLD; modulation changes only its envelope.
CARRIER_HZ=5888.3
ATTACK_SECONDS=.002
RELEASE_SECONDS=.003

def pcm(hz,ms,mode,rate=44100,channels=1,duty=50,wave=0,extended=False):
    if extended:return synth_pcm(hz,ms,mode,rate,channels,duty,wave)
    count=round(rate*ms/1000);out=array('h');envelope=0.
    attack=1-math.exp(-1/(rate*ATTACK_SECONDS))
    release=1-math.exp(-1/(rate*RELEASE_SECONDS))
    for n in range(count):
        gate=mode==0 or (mode==1 and (n*hz/rate)%1<.5)
        target=1. if gate else 0.
        envelope+=(target-envelope)*(attack if gate else release)
        # Preserve BASIC duration; a sub-ms end taper avoids an artificial click.
        fade=min(1,max(0,(count-1-n)/(rate*.0005)))
        v=int(24000*envelope*fade*math.sin(2*math.pi*CARRIER_HZ*n/rate)) if mode!=2 else 0
        out.extend([v]*channels)
    # Keep the modulated notes audible at high gate rates, without clipping
    # or changing their carrier, modulation frequency or duration.
    peak=max((abs(v) for v in out),default=0)
    if peak:
        gain=min(2.,28000/peak)
        out=array('h',(round(v*gain) for v in out))
    return out.tobytes()

def synth_pcm(hz,ms,mode,rate,channels,duty,wave):
    """Audible preview of measured gate textures, not a calibrated speaker model.

    Oversampled gates retain the 31-bit sequence at clocks above Nyquist.
    A direct switching component previews the strong high-rate survey sounds;
    the fixed resonant component remains audible in slower amplitude modulation.
    """
    count=round(rate*ms/1000);out=array('h');envelope=0.
    state=31;bits=[]
    for _ in range(31):
        bits.append(state&1);state=(state>>1)|(((state^(state>>2))&1)<<4)
    fraction=max(.01,min(.99,duty/100));oversample=8
    direct=.85 if mode==3 or hz>=1000 else .12
    resonance=.22 if mode==3 or hz>=4500 else .82
    for n in range(count):
        gate=0.
        for j in range(oversample):
            phase=(n+(j+.5)/oversample)*hz/rate
            gate+=1. if mode==0 else 0. if mode==2 else bits[int(phase)%31] if mode==3 else float(phase%1<fraction)
        gate/=oversample
        envelope+=(gate-envelope)*.45
        mean=16/31 if mode==3 else fraction
        ac=0 if mode in (0,2) else gate-mean
        value=resonance*envelope*math.sin(2*math.pi*CARRIER_HZ*n/rate)+direct*ac
        fade=min(1,n/(rate*.0005),max(0,(count-1-n)/(rate*.0005)))
        sample=round(26000*max(-1,min(1,value))*fade) if mode!=2 else 0
        out.extend([sample]*channels)
    return out.tobytes()

class AudioStream(QIODevice):
    """Keep the output alive between notes; silence never truncates a queued note."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pending=bytearray();self.lock=Lock()
        self.gate=False;self.phase=0;self.envelope=0.
        self.rate=44100;self.channels=1
        self.open(QIODevice.OpenModeFlag.ReadOnly)
    def isSequential(self):return True
    def bytesAvailable(self):return 65536 + super().bytesAvailable()
    def readData(self, size):
        with self.lock:
            count=min(size,len(self.pending))
            data=bytes(self.pending[:count]);del self.pending[:count]
            remaining=size-count
            if not self.gate and self.envelope<1e-6:return data+bytes(remaining)
            samples=array('h')
            for _ in range(remaining//(2*self.channels)):
                target=1. if self.gate else 0.
                tau=ATTACK_SECONDS if self.gate else RELEASE_SECONDS
                self.envelope+=(target-self.envelope)*(1-math.exp(-1/(self.rate*tau)))
                value=round(24000*self.envelope*math.sin(2*math.pi*self.phase))
                self.phase=(self.phase+CARRIER_HZ/self.rate)%1
                samples.extend([value]*self.channels)
            wave=samples.tobytes()
            return data+wave+bytes(remaining-len(wave))
    def writeData(self,data):return -1
    def append(self,data):
        with self.lock:self.pending.extend(data)
    def set_gate(self,enabled):
        with self.lock:self.gate=bool(enabled)

class BuzzerAudio:
    def __init__(self,parent):
        self.parent=parent;self.sink=None;self.buffer=None
        self.enabled=True;self.volume=.85;self.device_id=None
    def set_volume(self,value):
        self.volume=max(0.,min(1.,value))
        if self.sink:self.sink.setVolume(self.volume)
    def stop(self):
        if self.sink:self.sink.stop();self.sink.deleteLater();self.sink=None
        if self.buffer:self.buffer.close();self.buffer.deleteLater();self.buffer=None
    def play(self,event):
        if not self.enabled:return
        if event.get('gate') is False and not self.sink:return
        if not self.sink:
            device=next((d for d in QMediaDevices.audioOutputs() if bytes(d.id())==self.device_id),QMediaDevices.defaultAudioOutput())
            if device.isNull():return tr('Aucune sortie audio disponible.')
            fmt=QAudioFormat();fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
            for rate,channels in [(44100,1),(48000,1),(48000,2)]:
                fmt.setSampleRate(rate);fmt.setChannelCount(channels)
                if device.isFormatSupported(fmt):break
            else:return tr('Sortie audio incompatible avec PCM 16 bits.')
            self.rate=rate;self.channels=channels
            self.buffer=AudioStream(self.parent)
            self.buffer.rate=rate;self.buffer.channels=channels
            self.sink=QAudioSink(device,fmt,self.parent)
            self.sink.setBufferSize(rate*channels*2//20)
            self.sink.setVolume(self.volume)
            self.enqueue(event)
            self.sink.start(self.buffer)
        else:
            self.enqueue(event)
        if self.sink.error().value:return tr('Erreur de sortie audio : ')+str(self.sink.error())
    def enqueue(self,event):
        if 'gate' in event:self.buffer.set_gate(event['gate'])
        else:self.buffer.append(pcm(event['hz'],event['ms'],event['mode'],self.rate,self.channels,
                                   event.get('duty',50),event.get('wave',0),event.get('extended',False)))

    def pause(self,paused):
        if self.sink:
            self.sink.suspend() if paused else self.sink.resume()
