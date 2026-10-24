"""All 26 notes, all three registers, and the six key-dependent Piano modes."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools/diagnostics')]
from core import analyze
from emulator_worker import backend
from validate_sound_synth import run

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',default='sound-steady');out=ROOT/'build'/p.parse_args().build
    C=backend(mask_path=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin',firmware_path=out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin')
    source=(ROOT/'examples/piano-fr.bas').read_text(encoding='utf-8')
    rows=dict(analyze(source).records)
    setup='\n'.join(f'{n} {b}' for n,b in rows.items() if n<=70)
    body='''80 D=50
90 FOR R=0 TO 2:FOR C=65 TO 90
100 I=C-65+26*R
110 SOUND F(I),1,D:SOUND H(I),1,D:SOUND 5889+F(I),1,D
120 SOUND 50,1,1+INT((C-65)*.33334)
130 SOUND 50,1,99-INT((C-65)*.33334)
160 SOUND G(I),1,D,1
170 NEXT C:NEXT R:END'''
    c=C(setup+'\n'+body);c.instant_paper=True;s=c.symbols
    steps=run(c,lambda c:c.pc==s['GETC'] and not c.input,90000000)
    assert not c.screen().startswith('?'),c.screen()
    assert len(c.sounds)==468,len(c.sounds)
    report=dict(result='PASS',sha256=hashlib.sha256((out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()).hexdigest(),notes=26,registers=3,modes=6,noise_keys_per_register=26,commands=len(c.sounds),steps=steps)
    (out/'piano-registers-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report,flush=True)

if __name__=='__main__':main()
