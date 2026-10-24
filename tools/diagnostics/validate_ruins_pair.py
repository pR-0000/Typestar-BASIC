"""Compare both Ruins map plans using a common map, actual BASIC and native driver."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools')]
from emulator_worker import backend
from paper import PaperRaster
OUT=ROOT/'build/glyph-pair'

def run(name,source,firmware):
    cache=OUT/(name+'-map-validation.json')
    digest=hashlib.sha256(source.encode()).hexdigest()
    if cache.exists():
        r=json.loads(cache.read_text())
        if r['source_sha256']==digest:return r
    trail=64 if name=='candidate' else 16
    records={int(l.split()[0]):l.split(' ',1)[1] for l in source.splitlines()}
    records[50]=f'G({trail})=6:G({trail+1})=15:G({trail+2})=15:G({trail+3})=6'
    records[60]='B=0:C=0:GOSUB 1200'
    source='\n'.join(f'{n} {b}' for n,b in sorted(records.items()))+'\n'
    C=backend(mask_path=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin',firmware_path=firmware)
    c=C(source);c.instant_paper=True;s=c.symbols
    board=json.loads((ROOT/'build/ruins/initial-map.json').read_text());injected=False;calls=[];groups=[];low=5951
    for steps in range(110000000):
        if steps%4000000==0:print(name,steps,c.word(s['RLINE']),flush=True)
        line=c.word(s['RLINE'])
        assert c.pc not in (s['SYNTAX'],s['RANGEERROR'],s['RBPAPERERROR'],s['PMEMERROR']), (name,line,hex(c.pc),c.screen())
        if line==60 and not injected:
            start=c.word(s['PEND'])+10
            for i,v in enumerate(board):
                v=v%16
                c.m[start+5*i:start+5*i+5]=bytes.fromhex(f'{v:08d}00')
            injected=True
        if injected and line in (1262,1270):break
        assert not injected or c.pc!=s['READY'], ('BASIC error',line,c.screen())
        if c.pc==s['GPCALL']:calls.append((c.x,c.word(0xba),c.word(0xb8)))
        if c.pc==s['SGSTAGE']:groups.append((c.m[s['SGWIDTH']],c.m[s['SGHEIGHT']],c.m[s['SGREPEAT']]))
        low=min(low,c.word(s['DHEAP'])-c.word(s['DFLOOR']))
        c.step()
    else:raise AssertionError(('timeout',name,c.screen()))
    raster=PaperRaster();raster.add(c.paper_events)
    from PIL import ImageChops
    im=raster.output();box=ImageChops.invert(im.convert('L')).getbbox();im.crop((box[0]-10,box[1]-10,box[2]+10,box[3]+10)).save(OUT/(name+'-ruins.png'))
    def signed(v):return v-65536 if v>=32768 else v
    result=dict(source_sha256=digest,steps=steps,min_free=low,tiles=c.tiles,groups=groups,
                paper_events=c.paper_events,head_distance=sum(abs(signed(b)) for x,b,a in calls if x==0x716f),
                paper_distance=sum(abs(signed(a)) for x,b,a in calls if x==0x7154),native_calls=len(calls))
    cache.write_text(json.dumps(result)+'\n')
    return result

def main():
    old=(ROOT/'examples/games/ruines-typestar-fr.bas').read_text(encoding='utf8')
    new=(OUT/'ruines-typestar-fr.bas').read_text(encoding='utf8')
    a=run('baseline',old,ROOT/'firmware/0.4.93-dev/typestar-basic-32k.bin')
    b=run('candidate',new,OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin')
    def pixels(r):
        # Different travel orders accumulate the existing fractional Y trims at
        # different moments. The emulator has ideal rollers; compare nominal
        # 112-phase band anchors and exact head bits, keeping raw traces too.
        return {(x,round(y/112)*112,i) for x,y,v in r['paper_events'] for i in range(24) if v&(1<<i)}
    assert pixels(a)==pixels(b),('changed map pixels',len(pixels(a)^pixels(b)))
    report=dict(result='PASS',candidate_source_sha256=b['source_sha256'],comparison='Exact head bits and nominal bands; raw motor traces retained',baseline={k:a[k] for k in ('steps','head_distance','native_calls')},candidate={k:b[k] for k in ('steps','min_free','head_distance','native_calls')},mixed_groups=sum(w==32 for w,h,n in b['groups']))
    report['nominal_travel']=json.loads((OUT/'ruins-travel.json').read_text())
    (OUT/'ruins-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
if __name__=='__main__':main()
