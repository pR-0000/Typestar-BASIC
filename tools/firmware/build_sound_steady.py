""".96: guard and replace only .95's sound scheduler; retain all other code."""
from pathlib import Path
import hashlib,json
import build_sound_synth as base
ROOT=base.ROOT
OUT=ROOT/'build/sound-steady'
BASE_SHA='33b50fc934cb3ef104c35d158b72fa533fd22bfa265d50b8e8662102c78f367c'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cpu=bytearray((ROOT/'build/sound-synth/EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes())
    assert hashlib.sha256(cpu).hexdigest()==BASE_SHA
    s=json.loads((ROOT/'build/sound-synth/symbols.json').read_text())
    m=json.loads((ROOT/'build/sound-synth/manifest.json').read_text())
    lo,hi=s['SNDPLAYPREP'],s['SNDPLAYPREPEND']
    base.OUT=OUT
    code,labels=base.assemble('steady',(ROOT/'src/sound-steady.asm').read_text(),lo,s)
    assert len(code)<=hi-lo,(len(code),hi-lo)
    before=bytes(cpu[lo-0x4000:hi-0x4000])
    cpu[lo-0x4000:hi-0x4000]=code+b'\xff'*(hi-lo-len(code))
    # Match v3's 50 Hz pulse/cut experiments. A 20 ms period still fits
    # entirely within one Timer 1 wrap and the 16-bit delay compiler.
    start=s['BASICSOUND']-0x4000;end=s['SNDRATEOK']-0x4000
    segment=bytes(cpu[start:end]);at=segment.index(bytes.fromhex('83003c'))+start
    assert cpu[at+5:at+8]==bytes.fromhex('8379d6')
    cpu[at:at+3]=bytes.fromhex('830032')
    cpu[at+5:at+8]=bytes.fromhex('8379e0')
    old=b'Typestar BASIC 0.4.95-dev';pos=cpu.index(old)
    cpu[pos:pos+len(old)]=b'Typestar BASIC 0.4.96-dev'
    free=m['explicit_free_regions']+([[lo+len(code),hi]] if len(code)<hi-lo else [])
    s.update(labels)
    m.update(version='0.4.96-dev',base_cpu_sha256=BASE_SHA,sha256=hashlib.sha256(cpu).hexdigest(),
             explicit_free_regions=sorted(free),explicit_free_bytes=sum(b-a for a,b in free),
             steady_sound=dict(origin=lo,bytes=len(code),old_bytes=hi-lo,old=before.hex(),new=code.hex()),
             status='Steady sound scheduler; regression and hardware checks pending')
    m['sound']['rate_min']=50
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    (ROOT/'studio/internal/profiles/basic-0.4.96-symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    print(json.dumps(dict(sha256=m['sha256'],scheduler_bytes=len(code),free_rom=m['explicit_free_bytes'])))

if __name__=='__main__':main()
