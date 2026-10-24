"""Drive Quest's actual tokenized rules through the HD6301 BASIC firmware.

Only the separately validated initial map is skipped. Fixtures shorten travel;
damage, purchases, input, rewards and paper crosses still execute on the CPU.
"""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'studio/internal'))
from core import analyze
from native_text import encode_source
from emulator_worker import backend
C=backend(mask_path=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin',firmware_path=ROOT/'build/release-candidate/EXPERIMENT-NOT-FOR-FLASH-cpu.bin')
LINES={int(k):v for k,v in json.loads((ROOT/'build/s70-quest-lines.json').read_text()).items()}

def decode(d):
    return int(''.join(f'{b:02x}' for b in d[:4]))/10**(d[4]&7)*(-1 if d[4]&128 else 1)

class Game:
    def __init__(self,fixture=None,language='fr',startup=False,skip_map=False):
        rows=dict(analyze((ROOT/f'examples/games/canon-s70-quest-{language}.bas').read_text(encoding='utf-8')).records)
        if not startup:rows[LINES[910]]='GOTO '+str(LINES[925])
        # Exercise the real Enter/CLEAR/common initialization path without
        # repeating mechanical map rendering in each LCD regression case.
        if skip_map:
            assert startup
            rows[LINES[6000]]='RETURN'
        if fixture:
            entry=max(rows)+1
            rows[LINES[950]]='A$="TEST":GOSUB '+str(LINES[150])+':GOTO '+str(entry)
            for offset,body in enumerate([fixture] if isinstance(fixture,str) else fixture):
                rows[entry+offset]=body
        self.attach(C('\n'.join(f'{n} {b}' for n,b in sorted(rows.items()))))
        self.wait()
    def attach(self,c):
        self.c=c
        c.instant_paper=True;self.steps=0;self.ended=False;self.minimum=5951;self.feedback=[];self.rewards=[];self.silent_pauses=[]
    def wait(self,budget=4000000):
        c=self.c;s=c.symbols
        for _ in range(budget):
            line=c.word(s['RLINE'])
            if c.pc==0x8ee6 and line==LINES[110]:return
            if c.pc==s['GETC'] and not c.input:
                assert not c.screen().startswith('?'),(line,c.screen())
                self.ended=True;return
            if c.pc in (s['SYNTAX'],s['RANGEERROR'],s['PMEMERROR']):raise AssertionError((line,c.screen(),hex(c.pc)))
            if c.pc==s['BASICSOUND'] and line==LINES[3330]:self.feedback.append(c.screen())
            if c.pc==s.get('SNDPLAYPREP') and c.m[s['SNDMODE']]==0:
                self.silent_pauses.append(c.word(s['SNDLEFT']))
            c.step();self.steps+=1
            if self.steps%2048==0:self.minimum=min(self.minimum,c.word(s['DHEAP'])-c.word(s['DFLOOR']))
        raise AssertionError(('timeout',line,c.screen()))
    def key(self,k=13):
        c=self.c;assert not self.ended
        if c.screen().startswith(('Victoire!','Victory!')):self.rewards.append(c.screen())
        c.held_key=k
        for _ in range(100):
            if c.pc==0x8ef0:c.step();break
            c.step()
        else:raise AssertionError(('key injection',hex(c.pc)))
        c.held_key=0;self.wait()
    def vars(self):
        c=self.c
        return {chr(c.m[p]):decode(c.m[p+1:p+6]) for p in range(c.word(c.symbols['DHEAP']),0x3800,6)}
    def set(self,**values):
        for name,value in values.items():
            for p in range(self.c.word(self.c.symbols['DHEAP']),0x3800,6):
                if self.c.m[p]==ord(name):
                    self.c.m[p+1:p+6]=bytes.fromhex(f'{value:08d}00');break
            else:raise AssertionError(('missing variable',name))
    def screen(self):return self.c.screen()
    def menu(self):return 'ATK DEF' in self.screen()
    def battle(self):
        self.key() # opponent title
        for _ in range(45):
            if 'Victoire' in self.screen() or 'Victory!' in self.screen():
                self.key()
                while 'Niveau ' in self.screen() or 'Level ' in self.screen():self.key()
                return
            assert self.menu(),(self.screen(),self.vars())
            if self.vars()['H']<max(12,self.vars()['V']-self.vars()['L']-self.vars()['W']+1) and self.vars()['P']>0:
                while self.vars()['J']!=2:self.key(19)
                self.key()
            while self.vars()['J']!=0:self.key(18)
            self.key()
        raise AssertionError(('battle timeout',self.screen(),self.vars()))

def main():
    global C
    folder=ROOT/'build/release-candidate'
    if '--build' in sys.argv:
        folder=ROOT/'build'/sys.argv[sys.argv.index('--build')+1]
        C=backend(mask_path=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin',firmware_path=folder/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin')
    results=[]
    def record(name,g):
        row=dict(case=name,steps=g.steps,minimum_free=g.minimum,screen=g.screen())
        results.append(row);print(row,flush=True)
    for lang in ('fr','en'):
        # Both startup choices must populate all seven enemy LCD sprites.
        sprites=json.loads((ROOT/'examples/graphics/s70-quest-sprites.json').read_text())['sprites'][1:]
        for printed in (False,True):
            fixture=f'FOR T=0 TO 6:GOSUB {LINES[3000]}:LOCATE 1,10:PRINT T;:GOSUB {LINES[100]}:NEXT'
            g=Game(fixture,lang,startup=True,skip_map=printed)
            g.key(13 if printed else 8);g.key()
            for t,sprite in enumerate(sprites):
                assert g.screen()[9:10]==str(t),(printed,t,g.screen())
                slot=g.c.lcd[31]&7
                assert list(g.c.cgram[8*slot:8*slot+7])==[int(row,2) for row in sprite['rows']],(printed,t)
                g.key()
            assert g.ended
            record(lang+(' printed' if printed else ' reused')+' map: seven enemy sprites',g)
        g=Game('N=30000:GOTO '+str(LINES[200]),lang);g.key()
        assert g.vars()['F']==20 and g.vars()['P']==0,g.vars()
        assert bytes(g.c.lcd[24:31])==bytes((169,32,170,32,201,32,200))
        assert ('NV1 >Cimet.' if lang=='fr' else 'LV1 >Grave') in g.screen(),g.screen()
        # Longer coordinates and maximum health/level still leave all four
        # direction icons intact; every progress stage identifies its next site.
        g.set(X=29,Y=15,H=96,L=12)
        names=('Cimet.','Forêt ','Ruines','Oasis ','Tour  ') if lang=='fr' else ('Grave ','Forest','Ruins ','Oasis ','Tower ')
        for r,name in enumerate(names):
            g.set(R=r);g.key(8);g.key(8)
            expected=encode_source('"'+name+'"')[1:-1]
            assert expected in bytes(g.c.lcd[:24]),(lang,r,g.screen())
            assert ('NV12' if lang=='fr' else 'LV12') in g.screen(),g.screen()
            assert bytes(g.c.lcd[24:31])==bytes((169,32,170,32,201,32,200))
        g.set(R=0,H=30,L=1)
        # Walk every direction in a patch of ordinary ground, with encounters
        # disabled by the fixture. D indexes the displayed up/down/left/right.
        for direction,(dx,dy) in enumerate(((0,-1),(0,1),(-1,0),(1,0))):
            g.set(X=23,Y=2,D=direction);g.key()
            assert (g.vars()['X'],g.vars()['Y'])==(23+dx,2+dy),g.vars()
        g.set(X=5,Y=13,D=0)
        for _ in range(3):g.key(19)
        g.key();assert g.vars()['X']==6,g.vars()
        g.key(18);g.key();assert g.vars()['X']==5,g.vars()
        g.key(8);assert g.screen().startswith('1/3 ') and chr(164)+'20 POT0' in g.screen(),g.screen()
        g.key(19);assert g.screen().startswith('2/3 ') and 'XP0/10' in g.screen() and 'ATK' in g.screen() and 'DEF' in g.screen(),g.screen()
        g.key(19);assert g.screen().startswith('3/3 ') and '+0' in g.screen(),g.screen()
        g.key(8);g.key(32);g.key();assert 'PV' in g.screen() or 'HP' in g.screen()
        # Initial gold cannot buy an upgrade. Test this refusal before funding
        # the fixture to check all four purchases and their exact deductions.
        g.set(X=5,Y=13,D=2);g.key();assert '1 ' in g.screen(),g.screen()
        g.key(51);assert '40' in g.screen();g.key()
        assert g.vars()['S']==0 and g.vars()['F']==20,g.vars()
        g.key(8);g.set(F=300)
        g.key(51);assert '40' in g.screen() and chr(164) in g.screen();g.key();assert g.vars()['S']==1 and g.vars()['F']==260
        g.key(51);assert '80' in g.screen();g.key();assert g.vars()['S']==2 and g.vars()['F']==180
        g.key(52);g.key();assert g.vars()['W']==1
        g.key(52);g.key();assert g.vars()['W']==2
        old=g.vars()['F'];g.key(51);assert g.vars()['F']==old and g.vars()['S']==2
        g.key(50);g.key();assert g.vars()['P']==1
        g.key(49);g.key();assert g.vars()['H']==30
        g.key(8);g.key(8)
        assert chr(164)+'48 POT1' in g.screen(),g.screen()
        g.key(8);record(lang+' movement, paged inventory, zero starting potions and shop prices',g)
        g=Game('T=1:Z=0:GOSUB '+str(LINES[2000])+':GOTO '+str(LINES[200]),lang);g.key()
        expected=encode_source('"'+('FANTôME' if lang=='fr' else 'GHOST')+'"')[1:-1]
        assert bytes(g.c.lcd[:len(expected)])==expected,g.screen()
        record(lang+' uppercase ghost name',g)
    # Five slimes give one level. Rest is actually bought after fight 3;
    # there are no free potions or injected healing in this progression case.
    g=Game([f'FOR X=1 TO 5:T=0:Z=0:GOSUB {LINES[2000]}',
            f'IF X=3 THEN GOSUB {LINES[1400]}',
            f'NEXT:GOTO {LINES[200]}'])
    g.key()
    for fight in range(1,6):
        g.battle()
        assert g.vars()['L']==(2 if fight==5 else 1),g.vars()
        if fight==3:
            assert '1 ' in g.screen(),g.screen()
            g.key(49);g.key();g.key(8)
    assert g.vars()['L']==2 and g.vars()['H']==36,(g.screen(),g.vars())
    assert g.vars()['P']==0 and g.vars()['F']==31 and g.vars()['E']==0,g.vars()
    assert len(g.rewards)==5 and all('+2 XP +3'+chr(164) in v for v in g.rewards),g.rewards
    assert 800 in g.silent_pauses,g.silent_pauses
    assert g.feedback and all('-' in v[7:13] and '-' in v[21:26] for v in g.feedback)
    record('five ordinary fights unlock level 2; one paid rest; damage feedback',g)
    g=Game('P=1:T=0:Z=0:GOSUB '+str(LINES[2000])+':GOTO '+str(LINES[200]))
    g.key();g.key();g.key(19);before=g.vars();g.key()
    assert g.vars()['H']==before['H']-2 and g.vars()['U']==before['U']-2
    assert g.screen()[1]==' ' and g.screen()[30]==' ',repr(g.screen())
    g.key(19);assert 'POT' in g.screen();g.key();assert g.vars()['P']==0 and g.vars()['H']==26
    before=g.vars();g.key();assert g.vars()['H']==before['H'] and g.vars()['U']==before['U'],g.vars()
    g.key(19);g.key();assert not g.menu() and not g.ended
    record('DEF, potion and ordinary FLEE',g)
    g=Game('H=1:T=0:Z=0:GOSUB '+str(LINES[2000])+':GOTO '+str(LINES[9500]))
    g.key();g.key();g.key();assert g.ended and g.vars()['H']==0
    record('defeat',g)
    g=Game('T=6:GOSUB '+str(LINES[1000])+':GOTO '+str(LINES[200]))
    g.key();assert '2' in g.screen();g.key();assert g.vars()['R']==0
    record('first guardian level gate',g)
    # Campaign fixtures only skip walking and set the intended unlock level.
    # Every fight uses normal enemy stats, damage, potions and rewards.
    g=Game('B=1736:N=30000:GOTO '+str(LINES[200]));g.key()
    for z,(x,y,level) in enumerate(((18,13,2),(3,6,4),(16,2,6),(25,5,8),(27,13,10)),1):
        g.set(X=x,Y=y+1,D=0,L=level,H=24+6*level,P=3,S=min(2,z),W=min(2,z))
        g.key();assert ('GARDIEN:' in g.screen() or 'GUARDIAN:' in g.screen()),(z,g.screen(),g.vars())
        oldevents=len(g.c.paper_events);oldgold=g.vars()['F'];g.battle()
        assert g.vars()['R']==z and len(g.c.paper_events)>oldevents,(z,g.screen(),g.vars())
        kind={1:4,2:3,3:5,4:5,5:6}[z]
        xp=2+kind+8+2*z;gold=3+2*kind+8+2*z
        assert f'+{xp} XP +{gold}'+chr(164) in g.rewards[-1],g.rewards[-1]
        assert g.vars()['F']==oldgold+gold and g.vars()['B']==1736 and g.vars()['C']==0,g.vars()
        assert g.vars()['H']>0
        if z<5:assert not g.ended
        print('PASS guardian',z,'gold',gold,'xp',xp,flush=True)
    assert g.ended and g.vars()['R']==5
    record('five guardians, crosses, rewards and ending',g)
    sources={lang:hashlib.sha256((ROOT/f'examples/games/canon-s70-quest-{lang}.bas').read_bytes()).hexdigest() for lang in ('fr','en')}
    text=json.dumps(dict(result='PASS',sha256=hashlib.sha256(bytes(g.c.m[0x4000:0xc000])).hexdigest(),source_sha256=sources,cases=results),indent=2)+'\n'
    (folder/'quest-rules-validation.json').write_text(text)
    if folder.name=='paper-grid':(ROOT/'build/quest-rules-validation.json').write_text(text)

if __name__=='__main__':main()
