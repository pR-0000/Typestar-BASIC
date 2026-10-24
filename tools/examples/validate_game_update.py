"""Run shipped startup paths and complete grid/map printing on the actual ROM."""
from pathlib import Path
import hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools/examples')]
from emulator_worker import backend
from core import analyze
from validate_paper_games import marks
from paper import PaperRaster

OUT=ROOT/'build/paper-grid'
ROM=OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin'
C=backend(mask_path=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin',firmware_path=ROM)
WAIT_LINE=json.loads((ROOT/'build/s70-quest-lines.json').read_text())['110']


def run(c,limit=90000000,quest=True):
    s=c.symbols;minimum=5951;start=time.monotonic()
    if not hasattr(c,'paper_origin_corrections'):c.paper_origin_corrections=[(0,0)]
    extra=c.paper_origin_corrections[-1][1]
    for n in range(limit):
        if c.pc in (s['SYNTAX'],s['RANGEERROR'],s['PMEMERROR']):
            raise AssertionError(('firmware error',c.word(s['RLINE']),hex(c.pc),c.screen(),minimum))
        if (quest and c.pc==0x8ee6 and c.word(s['RLINE'])==WAIT_LINE) or c.pc==s['GETC'] and not c.input:break
        if c.pc==s.get('YPPOST') and c.word(s['PMTY'])-c.word(s['PMY'])<=-2 and c.m[s['YPACC']]+s['YPGAIN']>=256:
            extra+=2;c.paper_origin_corrections.append((len(c.paper_events),extra))
        c.step()
        if n%2048==0:minimum=min(minimum,c.word(s['DHEAP'])-c.word(s['DFLOOR']))
        if n and n%10000000==0:print('progress',n,c.word(s['RLINE']),c.screen(),minimum,flush=True)
    else:raise AssertionError(('timeout',c.word(s['RLINE']),hex(c.pc),c.screen()))
    assert not c.screen().startswith('?'),c.screen()
    return dict(steps=n,seconds=round(time.monotonic()-start,2),minimum_free=minimum,jobs=c.jobs,tiles=c.tiles,screen=c.screen())


def key(c,k):
    c.held_key=k
    for n in range(100):
        if c.pc==0x8ef0:c.step();break
        c.step()
    else:raise AssertionError('key injection')
    c.held_key=0


def main():
    global OUT,ROM,C
    if '--build' in sys.argv:
        OUT=ROOT/'build'/sys.argv[sys.argv.index('--build')+1]
        ROM=OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin'
        C=backend(mask_path=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin',firmware_path=ROM)
    results={}
    for lang in (() if '--orbital-only' in sys.argv else ('fr','en')):
        source=(ROOT/f'examples/games/canon-s70-quest-{lang}.bas').read_text(encoding='utf-8')
        assert not analyze(source).issues
        c=C(source);c.instant_paper=True;r=run(c)
        assert ('CARTE:' in c.screen() or 'MAP:' in c.screen()) and c.jobs==0,r
        key(c,8);r=run(c);assert c.jobs==0 and ('sorcier' in c.screen() or 'sorcerer' in c.screen()),r
        # Reuse leaves B at zero: unknown paper origin, so later guardian
        # victories must stay on the LCD instead of moving this sheet.
        p=c.word(c.symbols['DHEAP'])
        b=next((i for i in range(p,0x3800,6) if c.m[i]==ord('B')),None)
        assert b is None or not any(c.m[b+1:b+6])
        results['quest-reuse-'+lang]=r;print('PASS reuse',lang,r,flush=True)
    if '--orbital-only' not in sys.argv:
        c=C((ROOT/'examples/games/canon-s70-quest-fr.bas').read_text(encoding='utf-8'));c.instant_paper=True
        run(c);key(c,13);r=run(c)
        assert c.jobs==35 and c.tiles==602,r
        # Printing initializes B/C after CLEAR; guardian crosses use this
        # known reading position, while reuse keeps B=0 and disables them.
        p=c.word(c.symbols['DHEAP']);end=0x3800
        values={chr(c.m[i]):int(''.join(f'{b:02x}' for b in c.m[i+1:i+5]))/10**(c.m[i+5]&7)*(-1 if c.m[i+5]&128 else 1)
                for i in range(p,end,6)}
        assert values['B']==1736 and values['C']==0,values
        r['paper_view_y']=values['B']
        results['quest-print']=r;print('PASS map',r,flush=True)
        raster=PaperRaster();raster.add(c.paper_events);raster.output().save(OUT/'quest-map.png')
        # Continue the exact freshly printed game into its first battle.
        # Previously the printing branch jumped past B$ initialization, which
        # only became visible as ?RANGE when decoding the enemy's LCD sprite.
        sys.path.insert(0,str(ROOT/'tools/diagnostics'))
        from validate_quest_rules import Game
        g=Game.__new__(Game);g.attach(c);g.key()
        g.set(X=18,Y=14,D=0,L=2,H=36,P=3,S=1,W=1)
        oldjobs=c.jobs;g.key();g.battle()
        assert g.vars()['R']==1 and g.vars()['B']==1736 and g.vars()['C']==0,g.vars()
        assert c.jobs==oldjobs+1,c.jobs
        results['quest-first-battle-after-print']=dict(steps=g.steps,screen=g.screen(),guardian=1,jobs=c.jobs)
        print('PASS first battle after actual map printing',results['quest-first-battle-after-print'],flush=True)
        sources={lang:hashlib.sha256((ROOT/f'examples/games/canon-s70-quest-{lang}.bas').read_bytes()).hexdigest() for lang in ('fr','en')}
        (OUT/'quest-startup-validation.json').write_text(json.dumps(dict(result='PASS',sha256=hashlib.sha256(ROM.read_bytes()).hexdigest(),source_sha256=sources,cases=results),indent=2)+'\n')
        if '--quest-only' in sys.argv:return
    for lang,name in (('fr','duel-orbital'),('en','orbital-duel')):
        source=(ROOT/f'examples/games/{name}-{lang}.bas').read_text(encoding='utf-8')
        assert not analyze(source).issues
        c=C(source);c.instant_paper=True;r=run(c,quest=False)
        assert c.pc==c.symbols['GETC'] and ('CASE' in c.screen() or 'CELL' in c.screen()),r
        results['orbital-grid-'+lang]=r;print('PASS grid',lang,r,flush=True)
        raster=PaperRaster();raster.add(c.paper_events);raster.output().save(OUT/f'orbital-grid-{lang}.png')
        points=marks(c);(OUT/f'orbital-grid-{lang}-marks.json').write_text(json.dumps(sorted(points)))
        # A full-height closing edge must have the same coverage as the left edge.
        from collections import Counter
        counts=Counter(x for x,y in points if 450<=y<=2163)
        edges=[(x,n) for x,n in counts.items() if n>=230]
        assert edges and max(x for x,n in edges)-min(x for x,n in edges)==1155,edges
        assert len(edges)==13*4,edges
    result=dict(result='PASS',sha256=hashlib.sha256(ROM.read_bytes()).hexdigest(),cases=results)
    (OUT/'games-validation.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
