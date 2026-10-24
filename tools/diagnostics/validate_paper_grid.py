"""Regression for the .97/.98 scene callback loop, including mixed producers."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools/diagnostics')]
from emulator_worker import backend
from validate_glyph_pair import MASK,run_to
OUT=ROOT/'build/paper-grid'


def main():
    image=OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin'
    C=backend(mask_path=MASK,firmware_path=image);cases=[]
    for text in ('BOX 0,0,3,255,1,1','LINE 0,0,20,20,1','CIRCLE 20,20,10,1,0'):
        source='10 DIM G(64):G(0)=32896\n20 LPRINT "TEST"\n30 GLYPH G(0),1,8,5\n40 '+text+'\n50 END'
        c=C(source);c.instant_paper=True;s=c.symbols
        run_to(c,lambda c:c.word(s['RLINE'])==50 or c.pc in (s['SYNTAX'],s['RANGEERROR'],s['PMEMERROR']),4000000)
        assert c.word(s['RLINE'])==50,(text,hex(c.pc),c.screen())
        assert c.jobs>=3,(text,c.jobs)
        cases.append(dict(statement=text,jobs=c.jobs,tiles=c.tiles))
        print('PASS geometry after font and tile row',cases[-1],flush=True)
    invalid=('LINE -1,0,20,20,1','LINE 0,0,248,20,1','LINE 0,0,20,256,1',
             'LINE 0,0,20,20,0','LINE 0,0,20,20,17')
    for text in invalid:
        c=C();c.allow_errors=True;c.command(text)
        assert c.screen().startswith('?RANGE') and c.jobs==0,(text,c.screen(),c.jobs)
    report=dict(result='PASS',sha256=hashlib.sha256(image.read_bytes()).hexdigest(),cases=cases,invalid_before_motion=list(invalid))
    (OUT/'scene-validation.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    if '--build' in sys.argv:OUT=ROOT/'build'/sys.argv[sys.argv.index('--build')+1]
    main()
