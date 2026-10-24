"""Execute paper examples on the selected BASIC ROM and compare actual marks.

The Ruins fixture supplies a fixed map after DIM, including a crowded row
that forces palette replacement. Gameplay and the printer run in firmware.
"""
from pathlib import Path
import json
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools')]
from core import analyze
from emulator_worker import backend
from paper import PaperRaster

OUT=ROOT/'build/paper-games'
MASK=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin'
ROM=ROOT/'release/s70-basic-0.4.98-dev-canon-start-nh7.bin'
BASELINE_REF='ba66cc628a1b4504c72f2a7deef9c19140b7e6fc'


def array(c,name):
    p=c.word(c.symbols['PEND'])+1
    while p<c.word(c.symbols['DFLOOR']):
        if c.m[p]==ord(name):return p+9
        p+=9+c.word(p+7)
    raise AssertionError(('array',name))


def execute(source,fixture=None,limit=100000000):
    a=analyze(source);assert not a.issues,a.issues
    C=backend(mask_path=MASK,firmware_path=ROM)
    c=C(source);c.instant_paper=True;s=c.symbols;minimum=5951;injected=False;returns=0
    started=time.monotonic();c.paper_origin_corrections=[(0,0)];extra=0
    for steps in range(limit):
        if fixture is not None and not injected and c.word(s['RLINE'])==80:
            p=array(c,'M')
            for i,v in enumerate(fixture):c.m[p+5*i:p+5*i+5]=bytes.fromhex(f'{v:08d}00')
            injected=True
        if c.pc in (s['SYNTAX'],s['RANGEERROR'],s['PMEMERROR']):
            raise AssertionError(('error',c.word(s['RLINE']),hex(c.pc),minimum))
        if c.pc==s['GETC'] and not c.input:break
        if c.pc==s['GPCALL'] and c.x==0x716f:returns+=1
        # The functional bus has ideal rollers, but still executes the real
        # firmware's extra backlash-compensation steps. Exclude those steps
        # only from the comparison oracle, not from execution or raw evidence.
        if c.pc==s.get('YPPOST'):
            delta=c.word(s['PMTY'])-c.word(s['PMY'])
            if delta<=-2 and c.m[s['YPACC']]+s['YPGAIN']>=256:
                extra+=2;c.paper_origin_corrections.append((len(c.paper_events),extra))
        c.step()
        if steps%2048==0:minimum=min(minimum,c.word(s['DHEAP'])-c.word(s['DFLOOR']))
        if steps and steps%10000000==0:print('progress',steps,c.word(s['RLINE']),c.screen(),flush=True)
    else:raise AssertionError(('timeout',c.word(s['RLINE']),c.screen()))
    assert fixture is None or injected
    assert not c.screen().startswith('?'),c.screen()
    result=dict(steps=steps,seconds=time.monotonic()-started,minimum_free=minimum,
                jobs=c.jobs,tiles=c.tiles,head_returns=returns,screen=c.screen(),
                compensation_phase_steps=extra)
    return c,result


def marks(c):
    points=set();timeline=c.paper_origin_corrections;j=0
    for i,(x,y,b) in enumerate(c.paper_events):
        while j+1<len(timeline) and timeline[j+1][0]<=i:j+=1
        points.update((x,y-timeline[j][1]+7*bit) for bit in range(24) if b&(1<<bit))
    return points


def main():
    OUT.mkdir(exist_ok=True)
    fixture=[1]*80
    for y in range(1,7):
        for x in range(1,9):fixture[10*y+x]=0
    fixture[21:29]=[2,3,4,5,6,8,9,10]
    fixture[42:46]=[1,1,2,2]
    report={}
    for lang,name in [('fr','ruines-typestar'),('en','typestar-ruins')]:
        p=ROOT/f'examples/games/{name}-{lang}.bas'
        old=subprocess.check_output(['git','show',f'{BASELINE_REF}:examples/games/{p.name}'],cwd=ROOT).decode('utf-8-sig')
        new=p.read_text(encoding='utf-8')
        for label,source in [('old',old),('new',new)]:
            rows=dict(analyze(source).records);rows[80]='GOSUB 1200:END'
            c,r=execute(''.join(f'{n} {b}\n' for n,b in sorted(rows.items())),fixture)
            (OUT/(p.stem+'-'+label+'.json')).write_text(json.dumps(dict(result=r,events=c.paper_events,compensation=c.paper_origin_corrections)))
            report[p.name+'-'+label]=r;print(p.name,label,r,flush=True)
            if label=='old':previous=marks(c)
            else:
                actual=marks(c)
                assert actual==previous,(len(actual-previous),len(previous-actual))
                raster=PaperRaster();raster.add(c.paper_events)
                raster.output().save(OUT/(p.stem+'.png'))
    for lang in ('fr','en'):
        p=ROOT/f'examples/graphics/tilemap-{lang}.bas'
        c,r=execute(p.read_text());assert c.jobs==4 and c.tiles==24,r
        report[p.name]=r;print(p.name,r,flush=True)
        raster=PaperRaster();raster.add(c.paper_events)
        image=raster.output();box=image.getbbox()
        # Crop around actual ink, keeping a small white frame.
        from PIL import ImageOps
        ink=ImageOps.invert(image.convert('L')).getbbox()
        image=image.crop((max(0,ink[0]-12),max(0,ink[1]-12),ink[2]+12,ink[3]+12))
        image.save(OUT/(p.stem+'.png'))
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')


def focused():
    """All ten sprites in one crowded row; keep source-address lookup real."""
    OUT.mkdir(exist_ok=True);fixture=[0]*80;fixture[20:30]=list(range(1,11));report={}
    for lang,name in [('fr','ruines-typestar'),('en','typestar-ruins')]:
        p=ROOT/f'examples/games/{name}-{lang}.bas'
        for label in (('old','new') if lang=='fr' else ('new',)):
            source=(subprocess.check_output(['git','show',f'{BASELINE_REF}:examples/games/{p.name}'],cwd=ROOT).decode('utf-8-sig')
                    if label=='old' else p.read_text(encoding='utf-8'))
            rows=dict(analyze(source).records);rows[80]='GOSUB 1200:END';rows[1270]='END'
            source=''.join(f'{n} {b}\n' for n,b in sorted(rows.items()))
            source=source.replace('FOR J=0 TO 79','FOR J=20 TO 29').replace('FOR Y=0 TO 7','FOR Y=2 TO 2')
            c,r=execute(source,fixture);report[p.name+'-'+label]=r
            (OUT/(p.stem+'-focused-'+label+'.json')).write_text(json.dumps(dict(result=r,events=c.paper_events,compensation=c.paper_origin_corrections)))
            print(p.name,label,r,flush=True)
            actual={point for point in marks(c) if point[1]>=700}
            if label=='old':reference=actual
            else:assert actual==reference,(len(actual-reference),len(reference-actual))
    report['result']='PASS'
    (OUT/'ruins-validation.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    focused() if '--focused' in sys.argv else main()
