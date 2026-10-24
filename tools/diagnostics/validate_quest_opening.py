"""First guardian with the gold/XP earned by five real slime victories.

validate_quest_rules verifies those five fights and one paid rest. This case
resumes that exact state, buys both potions through the real shop and uses DEF.
Walking alone is shortened; no free gear, potions or healing are injected.
"""
from pathlib import Path
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/diagnostics'))
from validate_quest_rules import Game,LINES


def main():
    g=Game('L=2:H=36:F=31:GOTO '+str(LINES[200]));g.key()
    assert g.vars()['P']==0 and g.vars()['S']==0 and g.vars()['W']==0
    g.set(X=5,Y=13,D=2);g.key()
    for _ in range(2):g.key(50);g.key()
    assert g.vars()['P']==2 and g.vars()['F']==15,g.vars()
    g.key(8);g.set(X=18,Y=14,D=0);g.key();g.key()
    assert g.menu()
    rounds=potions=0
    while not g.screen().startswith('Victoire!'):
        assert g.menu() and not g.ended,(g.screen(),g.vars())
        desired=2 if g.vars()['H']<=8 and g.vars()['P']>0 else 1
        while g.vars()['J']!=desired:g.key(19)
        g.key();rounds+=1;potions+=desired==2
        assert rounds<=20,(g.screen(),g.vars())
    assert '+16 XP +21'+chr(164) in g.screen(),g.screen()
    g.key()
    while g.screen().startswith('Niveau '):g.key()
    v=g.vars()
    assert v['R']==1 and v['L']==3 and v['E']==2 and v['F']==36,v
    assert v['P']==0 and v['H']>0 and v['S']==v['W']==0,v
    assert g.c.jobs==0 and v.get('B',0)==0
    report=dict(result='PASS',sha256=hashlib.sha256(bytes(g.c.m[0x4000:0xc000])).hexdigest(),
                source_sha256={'fr':hashlib.sha256((ROOT/'examples/games/canon-s70-quest-fr.bas').read_bytes()).hexdigest()},
                starting_state=dict(level=2,health=36,gold=31,potions=0),
                result_state=dict(level=v['L'],health=v['H'],gold=v['F'],potions=v['P'],xp=v['E']),
                rounds=rounds,potions_bought=2,potions_used=potions,steps=g.steps)
    (ROOT/'build/release-candidate/quest-opening-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS opening',report,flush=True)


if __name__=='__main__':main()
