"""Compare actual LPRINT output; exercise regrouped helpers and host audio."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools/diagnostics')]
from emulator_worker import backend
from validate_glyph_pair import MASK,run_to
OUT=ROOT/'build/tile-stream'

def main():
    image=OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin';paper=[]
    for path in (ROOT/'build/sound-steady'/image.name,image):
        C=backend(mask_path=MASK,firmware_path=path)
        c=C('10 LPRINT "Courier 5g{}\\|~"\n20 END');s=c.symbols
        run_to(c,lambda c:c.word(s['RLINE'])==20,4000000)
        paper.append(c.paper_events)
    assert paper[0]==paper[1]
    C=backend(mask_path=MASK,firmware_path=image)
    for args,x,y in [('',0,0),('0',0,0),('128',128,0),('128,448',128,448),('37,192',37,192)]:
        c=C();c.command('ORIGIN '+args);s=c.symbols
        assert c.word(s['PMX'])==x and c.word(s['PMY'])==y and c.jobs==0
    for args in ('129','128,449','-1','0,-1'):
        c=C();c.allow_errors=True;c.command('ORIGIN '+args)
        assert c.screen().startswith('?RANGE') and c.jobs==0
    c=C('10 DIM G(15):A=10\n20 CLEAR\n30 PRINT A\n40 END');s=c.symbols
    run_to(c,lambda c:c.word(s['RLINE'])==40,1500000);assert c.screen()=='0',c.screen()
    for n in range(16):
        c.a=n;c.pc=s['HEXDIGIT'];run_to(c,lambda c:c.pc==s['PUTC'],100)
        assert c.a==ord('0123456789ABCDEF'[n])
    C=backend(realtime_sound=True,mask_path=MASK,firmware_path=image)
    c=C('10 BEEP 1:SOUND 0,1:SOUND 5000,1\n20 END');s=c.symbols
    run_to(c,lambda c:c.word(s['RLINE'])==20,2000000)
    assert [e['mode'] for e in c.audio_events if 'mode' in e]==[0,2,1],c.audio_events
    result=dict(result='PASS',sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                identical_lprint=True,origin_boundaries=True,clear_variables=True,hex_digits=16,
                audio_gate_modes=[0,2,1])
    (OUT/'compatibility-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)

if __name__=='__main__':
    if '--build' in sys.argv:OUT=ROOT/'build'/sys.argv[sys.argv.index('--build')+1]
    main()
