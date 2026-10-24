"""Execute the shipped Quest program and retain startup paper/motion evidence."""
from pathlib import Path
import argparse,hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'studio/internal'))
from emulator_worker import backend
from core import analyze
MASK=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin'

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',default='examples/games/canon-s70-quest-fr.bas');p.add_argument('--limit',type=int,default=100000000);p.add_argument('--build',default='sound-steady');a=p.parse_args()
 C=backend(mask_path=MASK,firmware_path=ROOT/'build'/a.build/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin')
 c=C((ROOT/a.source).read_text(encoding='utf-8'));c.instant_paper=True;s=c.symbols;low=5951;start=time.monotonic();motions=[]
 for i in range(a.limit):
  if c.pc==s['GETC'] and not c.input:raise AssertionError(('wait',i,c.word(s['RLINE']),c.screen(),low,c.jobs))
  if c.pc in (s['RANGEERROR'],s['SYNTAX'],s['PMEMERROR']):raise AssertionError(('error',hex(c.pc),i,c.word(s['RLINE']),c.screen(),low,c.jobs,c.word(s['DHEAP'])-c.word(s['DFLOOR'])))
  if c.pc==0x8ee6:break
  if c.pc==s['GPCALL']:motions.append((c.x,c.word(0xba),c.word(0xb8)))
  c.step()
  if i%4096==0:low=min(low,c.word(s['DHEAP'])-c.word(s['DFLOOR']))
  if i and i%4000000==0:print('PROGRESS',i,c.word(s['RLINE']),c.screen(),low,c.jobs,flush=True)
 else:raise AssertionError(('timeout',c.word(s['RLINE']),c.screen(),low,c.jobs))
 result=dict(result='PASS',sha256=hashlib.sha256(bytes(c.m[0x4000:0xc000])).hexdigest(),source=a.source,steps=i,seconds=time.monotonic()-start,minimum_free=low,jobs=c.jobs,tiles=c.tiles,events=c.paper_events,motions=motions,screen=c.screen())
 (ROOT/'build'/('quest-'+Path(a.source).stem+'-startup.json')).write_text(json.dumps(result))
 print({k:v for k,v in result.items() if k not in ('events','motions')},flush=True)

if __name__=='__main__':main()
