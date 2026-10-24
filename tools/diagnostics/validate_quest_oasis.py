"""Check the central 26,6 Oasis, its four approaches and ordinary water."""
from pathlib import Path
from collections import deque
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/diagnostics'))
from validate_quest_rules import Game,LINES


def main():
    rows=json.loads((ROOT/'tools/examples/s70-quest-assets.json').read_text())['map']
    def walkable(x,y):
        return 0<=x<30 and 0<=y<16 and (rows[y][x]<'J' or (x,y)==(25,5))
    seen={(5,13)};queue=deque(seen)
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((0,-1),(0,1),(-1,0),(1,0)):
            p=x+dx,y+dy
            if p not in seen and walkable(*p):seen.add(p);queue.append(p)
    assert len(seen)==sum(walkable(x,y) for y in range(16) for x in range(30))
    cases=[]
    for language in ('fr','en'):
        for x,y in ((25,5),):
            assert rows[y][x]=='J' and (x,y) in seen
            g=Game('N=30000:GOTO '+str(LINES[200]),language);g.key()
            # A true water cell remains an obstacle, independent of level.
            assert rows[15][5]=='J' and walkable(5,14)
            g.set(X=5,Y=14,D=1,R=3,L=8);g.key()
            assert (g.vars()['X'],g.vars()['Y'])==(5,14),g.vars()
            # Oasis is walkable but requires the earlier guardians and level 8.
            g.set(X=x,Y=y+1,D=0,R=2,L=8);g.key()
            assert (g.vars()['X'],g.vars()['Y'],g.vars()['T'],g.vars()['Z'])==(x,y,9,4),g.vars()
            assert ('pr' if language=='fr' else 'previous') in g.screen(),g.screen()
            g.key();g.set(X=x,Y=y+1,R=3,L=7);g.key()
            assert '8' in g.screen() and 'ATK' not in g.screen(),g.screen()
            g.key()
            # A cleared Oasis can be crossed from all four land neighbours.
            for sx,sy,direction in ((x,y+1,0),(x,y-1,1),(x+1,y,2),(x-1,y,3)):
                assert walkable(sx,sy)
                g.set(X=sx,Y=sy,D=direction,R=4,L=8);g.key()
                assert (g.vars()['X'],g.vars()['Y'],g.vars()['T'])==(x,y,9),g.vars()
                assert g.vars()['R']==4 and ('NV8' if language=='fr' else 'LV8') in g.screen(),g.screen()
            # The two formerly mistaken boss sites are decorative tiles.
            for px,py in ((24,4),(26,6)):
                assert rows[py][px]=='O'
                g.set(X=px,Y=py+1,D=0);g.key()
                assert (g.vars()['X'],g.vars()['Y'])==(px,py+1),g.vars()
            # With the correct progression, the same ordinary movement starts
            # the fourth guardian, rather than a water-blocked movement.
            g.set(X=x,Y=y+1,D=0,R=3,L=8);g.key()
            assert (g.vars()['R'],g.vars()['Z'],g.vars()['T'])==(3,4,5),g.vars()
            assert g.screen().startswith('GARDIEN:' if language=='fr' else 'GUARDIAN:'),g.screen()
            g.key();assert g.menu() and 'POT' in g.screen(),g.screen()
            row=dict(language=language,cell=[x+1,y+1],guardian=4,level=8,walkable_approaches=4,steps=g.steps)
            cases.append(row);print('PASS',row,flush=True)
    sources={lang:hashlib.sha256((ROOT/f'examples/games/canon-s70-quest-{lang}.bas').read_bytes()).hexdigest() for lang in ('fr','en')}
    report=dict(result='PASS',sha256=hashlib.sha256(bytes(g.c.m[0x4000:0xc000])).hexdigest(),source_sha256=sources,reachable_cells=len(seen),cases=cases)
    (ROOT/'build/release-candidate/quest-oasis-validation.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
