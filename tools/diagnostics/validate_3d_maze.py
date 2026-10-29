"""Exercise random maze generation and monster rendering on the actual ROM.

--quick uses an explicitly labelled host-generated map fixture to isolate
rendering, rerooting and AI tests from the slower BASIC generation phase.
Normal startup and --generation-only execute the unmodified BASIC generator.
"""
from pathlib import Path
import argparse, collections, copy, hashlib, json, os, random, sys, time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools/examples')]
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from emulator_worker import backend
from core import analyze,codec
from native_text import encode_source
from build_3d_maze import (half_view,GLYPHS,BANK,TRIPLES,MONSTERS,WALL_TILE,
                          LEFT_BRACKET,RIGHT_BRACKET,NATIVE_GLYPHS,SHAPES,LINE_MAP)
DELTA=(-10,1,10,-1)

def decode(raw):
    return int(''.join(f'{b:02x}' for b in raw[:4]))/10**(raw[4]&7)*(-1 if raw[4]&128 else 1)
def number(n):
    return bytes.fromhex(f'{abs(int(n)):08d}{128 if n<0 else 0:02x}')
def encoded(s):return bytes(encode_source('"'+s+'"')[1:-1])
def neighbors(cells,n):
    for d,delta in enumerate(DELTA):
        m=n+delta
        if cells[n]&(1<<d) and 0<=m<100 and abs(m%10-n%10)+abs(m//10-n//10)==1:yield d,m

def paths(cells,root):
    parents={root:(None,None)};todo=collections.deque([root])
    while todo:
        n=todo.popleft()
        for d,m in neighbors(cells,n):
            if m not in parents:parents[m]=(n,(d+2)%4);todo.append(m)
    return parents

def rooted(cells,root):
    p=paths(cells,root)
    assert len(p)==100
    return [(v&143)+(0 if n==root else 16*(p[n][1]+1)) for n,v in enumerate(cells)]

def generated(seed):
    """Independent host DFS for fixtures, not used by the playable program."""
    rng=random.Random(seed);cells=[0]*100;seen={0};stack=[0]
    while stack:
        n=stack[-1]
        candidates=[(d,n+delta) for d,delta in enumerate(DELTA)
                    if 0<=n+delta<100 and abs((n+delta)%10-n%10)+abs((n+delta)//10-n//10)==1 and n+delta not in seen]
        if not candidates:stack.pop();continue
        d,m=rng.choice(candidates);cells[n]|=1<<d;cells[m]|=1<<((d+2)%4)
        seen.add(m);stack.append(m)
    cells[0]|=8;cells[99]|=4
    return rooted(cells,0)

def check_map(cells,root):
    assert len(cells)==100
    count=0
    for n,v in enumerate(cells):
        assert 0<v<256,(n,v)
        for d,delta in enumerate(DELTA):
            m=n+delta;inside=0<=m<100 and abs(m%10-n%10)+abs(m//10-n//10)==1
            if inside:
                assert bool(v&(1<<d))==bool(cells[m]&(1<<((d+2)%4))),(n,d)
                count+=bool(v&(1<<d))
            else:assert bool(v&(1<<d))==((n,d) in ((0,3),(99,2))),(n,d)
    assert count==198,count
    assert cells==rooted(cells,root),'Parent pointers must lead to the player along actual passages'
    return hashlib.sha256(bytes(v&15 for v in cells)).hexdigest()

def view(cells,c,d):
    left=right=stop=0;distance_cells=[]
    for depth in range(3):
        bits=cells[c]&15
        left|=(not(bits&(1<<((d+3)%4))))<<depth
        right|=(not(bits&(1<<((d+1)%4))))<<depth
        if not bits&(1<<d):break
        c+=DELTA[d];stop+=1
        if not 0<=c<100:break
        distance_cells.append(c)
    a=half_view(stop,left)
    b=tuple(tuple(int(f'{v:05b}'[::-1],2) for v in g) for g in reversed(half_view(stop,right)))
    center=WALL_TILE if stop==0 else a[3] if stop==1 else NATIVE_GLYPHS[45] if stop==2 else NATIVE_GLYPHS[32]
    if stop==0:a=a[:2]+(LEFT_BRACKET,RIGHT_BRACKET);b=(LEFT_BRACKET,RIGHT_BRACKET)+b[2:]
    return stop,a+(center,)+b,distance_cells

def check_banks():
    for stop,left,right,expected in SHAPES:
        indices=(left if stop==0 else 2+(left&3),
                 0 if stop==0 else 1 if stop==1 else 4*stop-6+(left>>2)+2*(right>>2),
                 right if stop==0 else 2+(right&3))
        actual=tuple(BANK[ord(ch)-35] for bank,i in zip(TRIPLES,indices) for ch in bank[i])
        assert actual==expected,(stop,left,right)

def sprite_catalogue(lang):
    """Draw the exact tested LCD pixels at a common scale for the guide."""
    from PySide6.QtGui import QColor,QFont,QImage,QPainter
    image=QImage(720,230,QImage.Format.Format_RGB32)
    image.fill(QColor('#e6ead6'))
    painter=QPainter(image)
    ink=QColor('#293d2c');painter.setPen(ink)
    painter.setFont(QFont('Segoe UI',15))
    for col,distance in enumerate((3,2,1)):
        title=(f'À {distance} case'+('s' if distance>1 else '') if lang=='fr'
               else f'{distance} cell'+('s' if distance>1 else '')+' away')
        painter.drawText(col*240+56,32,title)
        for y,row in enumerate(MONSTERS[distance]):
            for x in range(5):
                if row&(1<<(4-x)):
                    painter.fillRect(col*240+88+12*x,48+12*y,10,10,ink)
        width,height={3:(1,3),2:(3,5),1:(5,7)}[distance]
        painter.drawText(col*240+64,180,f'{width} × {height} pixels')
        painter.drawText(col*240+58,213,'Motif LCD réel' if lang=='fr' else 'Actual LCD pattern')
    painter.end()
    name='maze-3d-monster-sprites'+('' if lang=='fr' else '-en')+'.png'
    assert image.save(str(ROOT/'examples/guides/images'/name))

class Game:
    def __init__(self,C,lang,native,render,quick=False,seed=None,paper=False,menu_polls=0):
        self.lang=lang;self.native=native;self.render=render
        self.paper=paper
        path=ROOT/'examples/games'/('labyrinthe-3d-fr.bas' if lang=='fr' else '3d-maze-en.bas')
        source=path.read_text(encoding='utf-8');self.sha=hashlib.sha256(source.encode()).hexdigest()
        if seed is not None:source=source.replace('RANDOMIZE PEEK(9)*255+PEEK(10)+1',f'RANDOMIZE {seed}')
        if quick:
            fixture=generated(1841)
            spawn=next(n for n in range(1,99) if len(list(neighbors(fixture,n)))>=3)
            source=source.replace(f'{LINE_MAP[2050]} GOSUB {LINE_MAP[20]}:',f'{LINE_MAP[2050]} C={spawn}:')
            if not paper:
                # The generated labels are consecutive. Append diagnostics to
                # this one statement rather than inserting competing labels.
                old=f'{LINE_MAP[200]} GOSUB {LINE_MAP[1100]}'
                source=source.replace(old,old+f':IF K=84 THEN GOSUB {LINE_MAP[1300]}:GOTO {LINE_MAP[400]}')
                source=source.replace(f'{LINE_MAP[250]} IF K=81',f'{LINE_MAP[250]} IF K=86 THEN {LINE_MAP[400]} ELSE IF K=81')
        self.fixture_sha=hashlib.sha256(source.encode()).hexdigest()
        self.analysis=analyze(source);assert not self.analysis.issues,self.analysis.issues
        self.packed=codec.pack(self.analysis.records)
        self.c=C(source);self.s=self.c.symbols;self.steps=0;self.minimum=5951;self.messages=[];self.frames=0
        self.printed=[];self.glyph_rows=[];self.text_positions=[];self.glyph_positions=[]
        self.c.instant_paper=paper
        self.wait()
        for _ in range(menu_polls):
            self.c.step();self.wait()
        self.generation_seed=self.c.word(0x1ec6)
        self.c.held_key=13 if paper else 8
        self.c.step();self.c.held_key=0
        self.wait(180000000)
        if quick:
            cells=rooted(fixture,spawn);self.put_map(cells)
            self.set(D=1-(cells[spawn]&1))
            self.key(18);self.key(19)
        self.spawn=self.vars()['C']
        self.map_hash=check_map(self.cells(),self.spawn);self.check_view();self.unchanged()
    def unchanged(self):assert bytes(self.c.m[0x20c0:0x20c0+len(self.packed)])==self.packed
    def wait(self,budget=10000000):
        c=self.c;s=self.s
        for i in range(budget):
            if c.pc==0x8ef0 and c.word(s['RLINE']) in (LINE_MAP[1110],LINE_MAP[2014]):return
            assert c.pc not in (s['SYNTAX'],s['RANGEERROR'],s['PMEMERROR'],s['RBPAPERERROR']), (hex(c.pc),c.word(s['RLINE']),c.screen())
            if c.pc==s['GETC'] and not c.input:return
            if c.pc==s['SNDPLAYPREP']:self.messages.append(bytes(c.lcd[:32]))
            if c.pc==s.get('LPBUILD'):
                ptr=c.word(s['LPREAD']);length=c.m[s['LPREMAIN']]
                if c.m[s['SGACTIVE']]:
                    p=self.array_base()
                    palette=[int(decode(c.m[p+5*j:p+5*j+5])) for j in range(64)]
                    self.glyph_rows.append((list(c.m[ptr:ptr+length]),palette))
                    self.glyph_positions.append(tuple(c.xy))
                else:
                    self.printed.append((bytes(c.m[ptr:ptr+length]).decode('ascii'),bool(c.m[s['LPSUPPRESS']])))
                    self.text_positions.append(tuple(c.xy))
            c.step();self.steps+=1
            if self.steps%4096==0:self.minimum=min(self.minimum,c.word(s['DHEAP'])-c.word(s['DFLOOR']))
            if i and i%20000000==0:print('STARTUP',self.lang,i,c.word(s['RLINE']),c.screen(),flush=True)
        raise AssertionError(('timeout',hex(c.pc),c.word(s['RLINE']),self.vars(),c.screen()))
    def vars(self):
        c=self.c
        return {chr(c.m[p]):int(decode(c.m[p+1:p+6])) for p in range(c.word(self.s['DHEAP']),0x3800,6)}
    def array_base(self):
        p=self.c.word(self.s['PEND'])+1
        assert self.c.m[p]==ord('V')
        return p+9
    def cells(self):
        p=self.array_base();return [int(decode(self.c.m[p+5*i:p+5*i+5])) for i in range(100)]
    def put_map(self,cells):
        p=self.array_base()
        for i,value in enumerate(cells):self.c.m[p+5*i:p+5*i+5]=number(value)
    def field(self,index,value=None):
        p=self.array_base()+5*index
        if value is not None:self.c.m[p:p+5]=number(value)
        return int(decode(self.c.m[p:p+5]))
    def set(self,**values):
        old=self.vars()
        if 'X' in values or 'Y' in values:
            values['C']=10*values.get('Y',old['Y'])+values.get('X',old['X'])
            self.put_map(rooted(self.cells(),values['C']))
        for name,value in values.items():
            for p in range(self.c.word(self.s['DHEAP']),0x3800,6):
                if self.c.m[p]==ord(name):self.c.m[p+1:p+6]=number(value);break
            else:raise AssertionError(('missing',name))
    def key(self,k,check=True):
        assert self.c.pc==0x8ef0
        self.c.held_key=k;self.c.step();self.c.held_key=0
        self.wait(60000000 if self.paper else 10000000)
        if check:self.check_view()
    def face(self,d):
        diff=(d-self.vars()['D'])%4
        if diff:self.key({1:19,2:8,3:18}[diff])
    def check_view(self):
        c=self.c;v=self.vars();cells=self.cells();root=10*v['Y']+v['X']
        assert v['C']==root
        check_map(cells,root)
        stop,expected,sight=view(cells,root,v['D'])
        entity=0
        for distance,n in enumerate(sight,1):
            if n==v['R']:entity=distance;break
            if distance<=2 and cells[n]&128:entity=-distance;break
        assert (v['H'],v['E'])==(stop,entity),(v,stop,entity)
        if entity>0:expected=expected[:4]+(MONSTERS[entity],)+expected[5:]
        if entity<0:expected=expected[:4]+(tuple(self.native[197 if entity==-1 else 46]),)+expected[5:]
        for cell,bitmap in enumerate(expected):
            code=c.lcd[cell]
            actual=tuple(c.cgram[code*8:code*8+7]) if code<8 else tuple(self.native[code])
            assert actual==bitmap,(cell,code,v,actual,bitmap)
        for slot,bitmap in enumerate(GLYPHS):assert tuple(c.cgram[slot*8:slot*8+7])==bitmap
        assert tuple(c.cgram[56:63])==(WALL_TILE if v['I']==4 else MONSTERS[v['I']])
        assert c.lcd[9]==32
        assert (' PV' if self.lang=='fr' else ' HP').encode()+str(v['M']).encode() in bytes(c.lcd[10:32])
        if not self.paper:assert c.jobs==0 and not c.paper_events
        self.frames+=1;self.unchanged()
    def capture(self,name):
        path=ROOT/'examples/guides/images'/name
        assert self.render(1600,168,self.c.snapshot(False),self.native,spaced=True,blink=False).save(str(path))
    def info(self):
        return dict(source_sha256=self.sha,test_source_sha256=self.fixture_sha,tokenized_bytes=self.analysis.used,
                    minimum_free_bytes=self.minimum,instructions=self.steps,views_checked=self.frames,map_sha256=self.map_hash,
                    generation_seed=self.generation_seed,spawn_cell=self.spawn)

def reference_generation(state):
    """Independent host oracle for the published LFSR and stackless DFS.

    State is sampled after the confirmation key. This does not replace the
    BASIC generator; natural scenarios compare its actual output to this oracle.
    """
    def rnd():
        nonlocal state
        while True:
            for _ in range(8):state=(state>>1)^(0xb400 if state&1 else 0)
            if state-1<60000:return ((state-1)%10000)/10000
    spawn=0
    while not spawn:
        cells=[0]*100;cells[0]=8;c=count=0
        while count<99:
            start=int(rnd()*4)
            for offset in range(4):
                d=(start+offset)%4;p=c+DELTA[d]
                if not(0<=p<100) or abs(p%10-c%10)>1 or cells[p]:continue
                q=(d+2)%4;cells[p]=16*(q+1)+(1<<q);cells[c]+=1<<d
                mask=cells[c]&15
                if mask in (7,11,13,14,15):spawn=c
                c=p;count+=1
                break
            else:c+=DELTA[(cells[c]//16)-1]
    cells[99]+=4
    cells=rooted(cells,spawn)
    for a in range(2):
        for b in range(2):
            j=10*(1+4*a+int(rnd()*4))+1+5*b+int(rnd()*4)
            if j==spawn:j-=1
            cells[j]+=128
    treasure=(1+int(rnd()*8),1+int(rnd()*8))
    monster=99 if spawn<50 else 0
    return cells,monster,treasure,spawn

def natural_scenarios(g):
    """Unmodified source, real generated world, ordinary movement only.

    No teleports, diagnostic key handlers, forced monster/fragment placement or
    forced RNG seeds. The junction and first fragment must occur naturally.
    """
    cells,monster,treasure,spawn=reference_generation(g.generation_seed)
    assert g.cells()==cells
    v=g.vars();assert (v['T'],v['U'])==treasure and v['R']==monster and v['C']==spawn
    assert len(list(neighbors(cells,spawn)))>=3
    assert len(route(cells,spawn,monster))>=5
    g.capture(f'maze-3d-{g.lang}.png')
    marked=[n for n,v in enumerate(cells) if v&128]
    assert len(marked)==4 and {(n%10//5,n//10//5) for n in marked}=={(0,0),(0,1),(1,0),(1,1)}
    assert spawn not in marked
    first=min(marked,key=lambda n:len(route(cells,spawn,n)))
    for d in route(cells,spawn,first):
        g.face(d);g.key(13)
    assert g.field(101)==1 and not(g.cells()[first]&128)
    assert ('C1/4' if g.lang=='fr' else 'M1/4').encode() in bytes(g.c.lcd[:32])
    if g.paper:
        assert g.c.jobs>0 and len(g.glyph_rows)==10
        actual=[[False]*80 for _ in range(80)]
        for ty,(ids,palette) in enumerate(g.glyph_rows):
            assert len(ids)==10
            for tx,tile in enumerate(ids):
                words=palette[4*tile:4*tile+4]
                for yy,mask in enumerate(b for word in words for b in (word>>8,word&255)):
                    for xx in range(8):actual[8*ty+yy][8*tx+xx]=bool(mask&(128>>xx))
        expected=[[False]*80 for _ in range(80)]
        x0=5*((first%10)//5);y0=5*((first//10)//5)
        for yy in range(80):
            for xx in range(80):
                v=cells[10*(y0+yy//16)+x0+xx//16]
                expected[yy][xx]=((yy%16==0 and not(v&1)) or (xx%16==15 and not(v&2)) or
                    (yy%16==15 and not(v&4)) or (xx%16==0 and not(v&8)))
        assert actual==expected
        from paper import PaperRaster
        from PIL import ImageChops
        raster=PaperRaster();raster.add(g.c.paper_events)
        image=raster.output().convert('RGB');box=ImageChops.invert(image.convert('L')).getbbox();assert box
        image.crop((max(0,box[0]-16),max(0,box[1]-16),box[2]+16,box[3]+16)).save(
            ROOT/f'examples/guides/images/maze-3d-fragment-{g.lang}.png')
    else:assert g.c.jobs==0
    discovered_at=g.vars()['N'];seen=[]
    # Follow the wandering monster's current route using ordinary movement.
    # The player moves twice as fast, so eventual visible contact is possible.
    for _ in range(200):
        v=g.vars();d=route(cells,v['C'],v['R'])[0]
        g.face(d)
        if g.vars()['E']>0:seen.append((g.vars()['N'],g.vars()['E']))
        g.key(13)
        if g.vars()['E']>0:seen.append((g.vars()['N'],g.vars()['E']))
        if g.vars()['M']<3:break
    assert g.vars()['M']==2,(g.vars(),seen)
    assert g.vars()['R']!=g.vars()['C']
    assert seen,'The approaching monster must be visible before contact'
    g.unchanged()
    return dict(first_fragment_at_step=discovered_at,first_contact_at_step=g.vars()['N'],monster_sightings=seen,
                spawn_internal_passages=len(list(neighbors(cells,spawn))),
                natural_source=True,ordinary_movement_only=True)

def scenarios(g,ai=False):
    cells=g.cells();v=g.vars();g.capture(f'maze-3d-{g.lang}.png')
    # All three visible distances, then removal without changing the view.
    corridor=next((n,d,sight) for n in range(100) for d in range(4)
                  if len(sight:=view(cells,n,d)[2])==3)
    n,d,sight=corridor
    for distance in (3,2,1):
        g.set(X=n%10,Y=n//10,D=(d+1)%4,R=sight[distance-1]);g.key(18)
        g.capture(f'maze-3d-monster-{distance}-{g.lang}.png')
    g.set(R=next(m for m in range(100) if m not in sight and m!=n))
    if ai:g.key(86)  # same corridor, only the monster presence changed
    else:g.key(18);g.key(19)
    assert g.vars()['E']==0
    # A real wall hides a monster which is geometrically straight ahead.
    n,d=next((n,d) for n in range(100) for d,delta in enumerate(DELTA)
             if not(cells[n]&(1<<d)) and 0<=n+delta<100 and abs((n+delta)%10-n%10)+abs((n+delta)//10-n//10)==1)
    g.set(X=n%10,Y=n//10,D=(d+1)%4,R=n+DELTA[d]);g.key(18)
    assert g.vars()['E']==0;g.capture(f'maze-3d-wall-{g.lang}.png')
    # Actual movement reverses the parent edge. Cadence continues past 9999.
    for score in (0,9999):
        g.set(X=0,Y=0,D=0,N=score,R=99)
        walk=next(m for m in range(100) if len(route(cells,0,m))>=4)
        for d in route(cells,0,walk)[:4]:
            g.face(d);before=g.vars();g.key(13);after=g.vars()
            assert after['C']==before['C']+DELTA[d]
            assert after['N']==before['N']+1
            if after['N']%2:assert after['R']==before['R']
            else:assert after['R'] in [before['R']]+[m for _,m in neighbors(cells,before['R'])]
    if ai:
        # Hearing uses actual passage distance, through bends and regardless
        # of where the player looks. Close pursuit follows the true route.
        target=0;monster=next(m for m in range(100) if len(route(cells,target,m))==3)
        g.set(X=0,Y=0,R=monster,N=1,D=0,G=0)
        g.key(86)
        for _ in range(3):
            before=g.vars()['R'];distance=len(route(cells,before,target))
            if not distance:break
            g.key(84)
            assert len(route(cells,g.vars()['R'],target))==max(1,distance-1),(before,distance,g.vars())
        # Beyond hearing range the monster can choose a different branch:
        # it no longer has an omniscient route to the player.
        fork=next(m for m in range(1,99) if len(list(neighbors(cells,m)))>=3 and len(route(cells,m,0))>=6)
        off_route=False
        for _ in range(16):
            g.set(X=0,Y=0,R=fork,N=1);g.key(84)
            if len(route(cells,g.vars()['R'],0))>len(route(cells,fork,0)):off_route=True;break
        assert off_route,'A distant monster must be able to take a wrong branch'
        # Wandering stays inside the grid and follows an actual passage or waits.
        for monster in (0,99,33,66):
            target=99 if monster<50 else 0
            g.set(X=target%10,Y=target//10,R=monster,N=8);g.key(84)
            assert g.vars()['R'] in [monster]+[m for _,m in neighbors(cells,monster)]
    # Help pages retain the LCD custom slots and the frozen monster.
    g.key(32,False)
    for _ in range(3):g.key(13,False)
    g.check_view()
    # Production collision handling: three hits, visible retreat, game over.
    saved=copy.deepcopy(g.c)
    d,enemy=next(neighbors(cells,0))
    g.set(M=3)
    for remaining in (2,1,0):
        g.set(X=0,Y=0,D=(d+1)%4,R=enemy,N=0)
        g.key(18);g.key(13,remaining>0)
        assert g.vars()['M']==remaining
        if remaining:assert g.vars()['R']!=g.vars()['C']
    assert encoded('PERDU !' if g.lang=='fr' else 'CAUGHT!') in bytes(g.c.lcd[:32])
    g.key(13,False);assert g.c.pc==g.s['GETC']
    g.c=saved;g.check_view()
    # Treasure, required-before-exit guard, victory and clean END.
    t=10*v['U']+v['T'];previous,d=next((m,(dd+2)%4) for dd,m in neighbors(cells,t))
    g.set(X=previous%10,Y=previous//10,T=t%10,U=t//10,F=0,R=99,N=0,D=(d+1)%4)
    g.key(18);g.key(13);assert g.vars()['F']==1
    g.capture(f'maze-3d-treasure-{g.lang}.png')
    g.set(X=9,Y=9,F=0,R=0,D=1);g.key(19);g.key(13)
    assert (g.vars()['C'],g.vars()['F'])==(99,0)
    g.set(F=1);g.key(13,False)
    assert encoded('GAGNÉ EN ' if g.lang=='fr' else 'WON IN ') in bytes(g.c.lcd[:32])
    g.capture(f'maze-3d-win-{g.lang}.png');g.key(13,False)
    assert g.c.pc==g.s['GETC'];g.unchanged()

def escape_scenario(g):
    """Walk away from a nearby pursuer using only ordinary player controls."""
    saved=copy.deepcopy(g.c);cells=g.cells()
    fork,finish=next((n,m) for n in range(1,99)
                     if len(list(neighbors(cells,n)))>=3
                     for m in range(100) if len(route(cells,n,m))>=8)
    escape=route(cells,fork,finish)[:8]
    monster=next(m for d,m in neighbors(cells,fork) if d!=escape[0])
    g.set(X=fork%10,Y=fork//10,R=monster,N=0,M=3,D=(escape[0]+1)%4)
    g.key(18)
    trace=[]
    for direction in escape:
        g.face(direction);g.key(13)
        v=g.vars();distance=len(route(cells,v['C'],v['R']))
        assert v['M']==3,'An uninterrupted escape route must avoid damage'
        trace.append(dict(step=v['N'],player=v['C'],monster=v['R'],distance=distance))
    assert trace[0]['distance']==2
    assert trace[-1]['distance']>3
    assert any(t['step']%2==0 and t['distance']>3 for t in trace)
    g.c=saved;g.check_view()
    return dict(ordinary_controls_only=True,health_lost=0,escape_trace=trace)


def entity_scenarios(g):
    """Visible fragments, occlusion, and formerly invisible corner attacks."""
    cells=g.cells();saved=copy.deepcopy(g.c)
    n,d,sight=next((n,d,sight) for n in range(100) for d in range(4)
                  if len(sight:=view(cells,n,d)[2])==3)
    far=next(m for m in range(100) if m not in sight and m!=n)
    for distance in (3,2,1):
        world=[v&127 for v in cells];world[sight[distance-1]]|=128
        g.put_map(world);g.set(X=n%10,Y=n//10,D=(d+1)%4,R=far)
        g.key(18);assert g.vars()['E']==(-distance if distance<=2 else 0)
        if distance<=2:g.capture(f'maze-3d-fragment-lcd-{distance}-{g.lang}.png')
        # Remove the marker without changing the corridor: cached view must
        # still be refreshed and the ordinary centre tile restored.
        world[sight[distance-1]]&=127;g.put_map(rooted(world,n))
        g.key(86);assert g.vars()['E']==0
    # A wall hides a fragment, just as it hides a monster.
    wall,dd=next((n,d) for n in range(100) for d,delta in enumerate(DELTA)
                 if not(cells[n]&(1<<d)) and 0<=n+delta<100 and abs((n+delta)%10-n%10)+abs((n+delta)//10-n//10)==1)
    world=[v&127 for v in cells];world[wall+DELTA[dd]]|=128
    g.put_map(world);g.set(X=wall%10,Y=wall//10,D=(dd+1)%4,R=far)
    g.key(18);assert g.vars()['E']==0
    # Nearest visible entity wins the shared centre cell. A monster standing
    # on a fragment has priority. Collecting a fragment reveals the next one.
    world=[v&127 for v in cells];world[sight[0]]|=128;world[sight[1]]|=128
    g.put_map(world);g.set(X=n%10,Y=n//10,D=(d+1)%4,R=sight[0],M=3,N=0)
    g.key(18);assert g.vars()['E']==1
    g.set(R=far);g.key(86);assert g.vars()['E']==-1
    g.key(13);assert g.field(101)==1 and g.vars()['E']==-1
    g.key(13);assert g.field(101)==2 and not(g.cells()[sight[1]]&128)
    g.c=copy.deepcopy(saved)
    corners=[]
    for turn in (1,3):
        # The monster is one step around a bend beyond the player's next cell.
        p,dd,c,r=next((p,d,c,c+DELTA[(d+turn)%4])
                     for p in range(100) for d,c in neighbors(cells,p)
                     if cells[c]&(1<<((d+turn)%4)) and 0<=c+DELTA[(d+turn)%4]<100)
        g.set(X=p%10,Y=p//10,D=(dd+1)%4,R=r,M=3,N=1)
        g.key(18);assert g.vars()['E']==0
        g.key(13);assert g.vars()['M']==3 and g.vars()['R']==r
        assert g.vars()['C']==c
        g.face((dd+turn)%4);assert g.vars()['E']==1
        g.key(13);assert g.vars()['M']==2
        corners.append(turn)
        g.c=copy.deepcopy(saved)
    # Front-on convergence is still dangerous, with a visible warning.
    g.set(X=n%10,Y=n//10,D=(d+1)%4,R=sight[1],M=3,N=1)
    g.key(18);assert g.vars()['E']==2
    g.key(13);assert g.vars()['M']==2
    g.c=saved;g.check_view()
    return dict(fragment_distances=[1,2],fragment_hidden_at_three=True,wall_occlusion=True,nearest_entity_priority=True,
                consecutive_collections=True,corner_attack_guards=corners,visible_front_attack=True)

def route(cells,start,end):
    p=paths(cells,start);result=[];n=end
    while n!=start:
        previous,reverse=p[n];result.append((reverse+2)%4);n=previous
    return result[::-1]

def paper_scenarios(g,sectors=4):
    """Four hidden sectors, exact 80x80 wall pixels, no duplicate reveal."""
    assert g.field(100)!=0 and g.field(101)==0
    assert g.c.jobs==0 and not g.printed
    cells=g.cells()
    for n in (22,27,72,77):cells[n]|=128
    g.put_map(cells)
    # A nearby monster on an undiscovered fragment keeps the right parent.
    player=next(m for m in range(100) if len(route(cells,22,m))==3)
    g.set(X=player%10,Y=player//10,R=22,N=1)
    direction,target=next((d,m) for d,m in neighbors(cells,player) if len(route(cells,22,m))==2);g.face(direction)
    before=len(route(cells,22,target));g.key(13)
    assert len(route(cells,g.vars()['R'],target))==before-1
    lines=[]
    offset=0
    targets={1:(22,),2:(22,77),4:(22,27,72,77)}[sectors]
    for count,target in enumerate(targets,1):
        d,previous=next(neighbors(cells,target));d=(d+2)%4
        g.set(X=previous%10,Y=previous//10,D=(d+1)%4,R=99,N=0)
        g.key(18);monster=g.vars()['R'];jobs=g.c.jobs
        row_start=len(g.glyph_rows);text_start=len(g.printed);g.key(13)
        if os.environ.get('TYPESTAR_MAZE_SNAPSHOT'):
            import pickle
            state={k:v for k,v in vars(g).items() if k not in ('c','render')}
            state['cpu']={k:v for k,v in vars(g.c).items() if k not in ('paper_kernels','instant_paper_kernels')}
            (ROOT/f'build/maze-3d/paper-state-{g.lang}-{count}.pickle').write_bytes(pickle.dumps(state))
        if count==1:
            from paper import PaperRaster
            from PIL import ImageChops
            raster=PaperRaster();raster.add(g.c.paper_events)
            image=raster.output().convert('RGB')
            box=ImageChops.invert(image.convert('L')).getbbox();assert box
            image.crop((max(0,box[0]-16),max(0,box[1]-16),box[2]+16,box[3]+16)).save(
                ROOT/f'build/maze-3d/paper-preview-{g.lang}.png')
        assert g.field(101)==count
        assert g.vars()['R']==monster,'Printing must freeze the monster'
        assert not(g.cells()[target]&128)
        assert sum(bool(v&128) for v in g.cells())==4-count
        assert g.c.jobs>jobs
        added=[];partial=''
        for text,suppressed in g.printed[offset:]:
            partial+=text
            if not suppressed:added.append(partial);lines.append(partial);partial=''
        offset=len(g.printed)
        x0=5*((target%10)//5);y0=5*((target//10)//5)
        expected=[('CARTE ' if g.lang=='fr' else 'MAP ')+f'{count}/4 - '+chr(65+target%10)+str(target//10+1),
                  '   '+' '.join(chr(65+x0+k) for k in range(5))]
        assert added==expected,(added,expected,g.printed)
        row_labels=[f'{y0+k+1:2}' for k in range(5)]
        assert partial==''.join(row_labels)
        assert [t for t,s in g.printed[-5:]]==row_labels
        assert all(s for t,s in g.printed[-5:])
        rows=g.glyph_rows[row_start:];assert len(rows)==10
        positions=g.glyph_positions[row_start:]
        gx,gy=positions[0]
        assert all((x,y)==(gx,gy+112*k) for k,(x,y) in enumerate(positions)),positions
        # Two reverse positioning commands follow the labels: LLOCATE back
        # to row 1, then FEED -28. The firmware adds an occasional forward
        # unit for real paper asymmetry. The functional emulator counts these
        # raw phases without modelling the mechanical loss. Recover the exact
        # number of added units from the fractional accumulator, rather than
        # allowing an arbitrary alignment tolerance (one unit = two phases).
        gain=g.s.get('YPGAIN',0)
        after=g.c.m[g.s['YPACC']] if gain else 0
        before=(after-2*gain)&255
        corrections=(before+2*gain)//256
        expected_positions=[(gx-80,gy+56-2*corrections+224*k) for k in range(5)]
        assert g.text_positions[-5:]==expected_positions,dict(actual=g.text_positions[-5:],expected=expected_positions,grid=positions)
        actual=[[False]*80 for _ in range(80)]
        for ty,(ids,palette) in enumerate(rows):
            assert len(ids)==10
            for tx,tile in enumerate(ids):
                words=palette[4*tile:4*tile+4]
                masks=[b for word in words for b in (word>>8,word&255)]
                for yy,mask in enumerate(masks):
                    for xx in range(8):actual[8*ty+yy][8*tx+xx]=bool(mask&(128>>xx))
        expected_pixels=[[False]*80 for _ in range(80)]
        for yy in range(80):
            for xx in range(80):
                v=cells[10*(y0+yy//16)+x0+xx//16]
                expected_pixels[yy][xx]=((yy%16==0 and not(v&1)) or
                    (xx%16==15 and not(v&2)) or (yy%16==15 and not(v&4)) or
                    (xx%16==0 and not(v&8)))
        assert actual==expected_pixels,'Only the discovered sector walls may be drawn'
        if count==1:
            from paper import PaperRaster
            from PIL import ImageChops
            raster=PaperRaster();raster.add(g.c.paper_events)
            image=raster.output().convert('RGB')
            box=ImageChops.invert(image.convert('L')).getbbox();assert box
            image.crop((max(0,box[0]-16),max(0,box[1]-16),box[2]+16,box[3]+16)).save(
                ROOT/f'examples/guides/images/maze-3d-fragment-{g.lang}.png')
        # Walking over a collected fragment preserves paper and counter.
        g.set(X=previous%10,Y=previous//10,D=(d+1)%4,R=99,N=0)
        g.key(18);jobs=g.c.jobs;length=len(g.printed)
        g.key(13)
        assert g.c.jobs==jobs and len(g.printed)==length and g.field(101)==count
        print('FRAGMENT',g.lang,count,'PASS',g.minimum,flush=True)
    g.key(113,False);assert g.c.pc==g.s['GETC']
    return dict(fragments=sectors,printed_lines=lines,graphic_pixels_per_sector=6400,duplicate_prints=0,
                axis_labels='column centres and row centres',row_10_tested=sectors>1)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mask-rom',required=True,type=Path)
    p.add_argument('--firmware-rom',type=Path,default=ROOT/'firmware/0.4.100-dev/typestar-basic-32k.bin')
    p.add_argument('--language',choices=('fr','en','both'),default='both')
    p.add_argument('--quick',action='store_true')
    p.add_argument('--generation-only',action='store_true')
    p.add_argument('--paper',action='store_true',help='Choose paper mode; with --quick, test discovery and exact output of all four sectors')
    p.add_argument('--seed',type=int)
    p.add_argument('--natural',action='store_true',help='Play the first fragment and monster encounter using only ordinary controls')
    p.add_argument('--menu-polls',type=int,default=0,help='Wait this many extra idle polls before confirming the initial menu')
    p.add_argument('--paper-sectors',type=int,choices=(1,2,4),default=4,help='In the paper fixture, test the first sector, two opposite sectors or all four')
    p.add_argument('--entities-only',action='store_true',help='With --quick, isolate fragment visibility and contact fairness scenarios')
    args=p.parse_args();assert not(args.quick and args.generation_only)
    (ROOT/'build/maze-3d').mkdir(parents=True,exist_ok=True)
    check_banks()
    from PySide6.QtWidgets import QApplication
    from lcd_glass import render_glass
    app=QApplication.instance() or QApplication([])
    native={int(k,16):v for k,v in json.loads((ROOT/'studio/internal/assets/lcd-font.json').read_text(encoding='utf-8'))['rows'].items()}
    C=backend(mask_path=args.mask_rom,firmware_path=args.firmware_rom)
    report={'result':'PASS','scope':('host map fixture' if args.paper else 'host map fixture and diagnostic T/V keys') if args.quick else 'actual BASIC generation',
            'all_corridor_bank_combinations':len(SHAPES),'languages':{}}
    for lang in (('fr','en') if args.language=='both' else (args.language,)):
        sprite_catalogue(lang)
        start=time.monotonic();g=Game(C,lang,native,render_glass,args.quick,args.seed,args.paper,args.menu_polls)
        print('READY',lang,g.info(),flush=True)
        if os.environ.get('TYPESTAR_MAZE_SNAPSHOT'):
            import pickle
            state={k:v for k,v in vars(g).items() if k not in ('c','render')}
            state['cpu']={k:v for k,v in vars(g.c).items() if k not in ('paper_kernels','instant_paper_kernels')}
            tag=('paper' if args.paper else 'lcd')+('-quick' if args.quick else '-generated')
            (ROOT/f'build/maze-3d/startup-09-{tag}-{lang}.pickle').write_bytes(pickle.dumps(state))
        paper_result={}
        if args.entities_only:
            assert args.quick and not args.paper
            paper_result=entity_scenarios(g)
        elif args.natural:
            assert not args.quick and args.seed is None
            paper_result=natural_scenarios(g)
        elif args.generation_only:
            expected,monster,treasure,spawn=reference_generation(g.generation_seed)
            assert g.cells()==expected
            assert g.vars()['C']==spawn and len(list(neighbors(expected,spawn)))>=3
            assert g.vars()['R']==monster and (g.vars()['T'],g.vars()['U'])==treasure
            marked=[n for n,v in enumerate(g.cells()) if v&128]
            assert len(marked)==4,marked
            assert {(n%10//5,n//10//5) for n in marked}=={(0,0),(0,1),(1,0),(1,1)}
            assert spawn not in marked
        elif args.paper:paper_result=paper_scenarios(g,args.paper_sectors)
        else:
            if args.quick:
                paper_result=entity_scenarios(g)
                paper_result.update(escape_scenario(g))
            scenarios(g,args.quick)
        report['languages'][lang]=dict(g.info(),seconds=round(time.monotonic()-start,2))
        report['languages'][lang].update(paper_result)
        print('PASS',lang,report['languages'][lang],flush=True)
    name='validation-09'+('-paper' if args.paper else '-lcd')+('-entities' if args.entities_only else '-natural-'+str(args.menu_polls) if args.natural else '-quick' if args.quick else '-generation' if args.generation_only else '')+('' if args.seed is None else '-'+str(args.seed))+'-'+args.language+'.json'
    (ROOT/'build/maze-3d'/name).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
