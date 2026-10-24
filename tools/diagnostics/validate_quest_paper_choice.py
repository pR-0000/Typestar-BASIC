"""Guardian rewards are identical with printed and read-only reused maps."""
from pathlib import Path
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools/diagnostics'),str(ROOT/'studio/internal')]
from validate_quest_rules import Game,LINES


def main():
    cases=[]
    for language in ('fr','en'):
        for printed in (False,True):
            if printed:
                # Full-map printing is covered by validate_game_update. This
                # fixture starts at the same initialized paper reading origin.
                g=Game('B=1736:GOTO '+str(LINES[200]),language);g.key()
            else:
                # Use the actual startup prompt and Backspace path.
                g=Game(language=language,startup=True)
                assert ('CARTE:' in g.screen() or 'MAP:' in g.screen()),g.screen()
                g.key(8);g.key()
                assert g.vars().get('B',0)==0 and g.c.jobs==0
            g.set(X=18,Y=14,D=0,L=2,H=36,P=3,S=1,W=1)
            jobs=g.c.jobs;events=len(g.c.paper_events);position=tuple(g.c.xy);gold=g.vars()['F']
            g.key();g.battle()
            values=g.vars()
            assert values['R']==1 and values['F']==gold+21,values
            assert values['L']==3 and values['E']==2,values
            assert '+16 XP +21'+chr(164) in g.rewards[-1],g.rewards
            if printed:
                assert g.c.jobs>jobs and len(g.c.paper_events)>events
                assert values['B']==1736 and values['C']==0,values
            else:
                assert g.c.jobs==jobs and len(g.c.paper_events)==events
                assert tuple(g.c.xy)==position and values.get('B',0)==0,values
            row=dict(language=language,printed_map=printed,guardian=values['R'],
                     earned_gold=values['F']-gold,earned_xp=16,
                     additional_paper_jobs=g.c.jobs-jobs,paper_y=values.get('B',0))
            cases.append(row);print('PASS',row,flush=True)
    sources={lang:hashlib.sha256((ROOT/f'examples/games/canon-s70-quest-{lang}.bas').read_bytes()).hexdigest() for lang in ('fr','en')}
    report=dict(result='PASS',sha256=hashlib.sha256(bytes(g.c.m[0x4000:0xc000])).hexdigest(),source_sha256=sources,cases=cases)
    (ROOT/'build/release-candidate/quest-paper-choice-validation.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
