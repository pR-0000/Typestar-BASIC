"""Compare all three original 16x16 sprites with their streamed row versions."""
from pathlib import Path
import json
import subprocess
from validate_paper_games import ROOT, OUT, execute, marks, BASELINE_REF


def main():
    report={}
    for lang,name in [('fr','duel-orbital'),('en','orbital-duel')]:
        p=ROOT/f'examples/games/{name}-{lang}.bas'
        for label in ('old','new'):
            source=(subprocess.check_output(['git','show',f'{BASELINE_REF}:examples/games/{p.name}'],cwd=ROOT).decode('utf-8-sig')
                    if label=='old' else p.read_text(encoding='utf-8'))
            rows={int(n):b for n,b in (r.split(' ',1) for r in source.splitlines())}
            rows[1]='GOTO 35'
            rows[40]='LSPACING 1:B=0:C=0:FOR V=0 TO 2'
            if label=='old':
                rows[41]='FOR I=0 TO 2:G=25+48*I:K=238+140*V:GOSUB 1500'
                rows[42]='GLYPH Z(16*V),16,16,4:B=K+112:C=G:NEXT I:NEXT V'
            else:
                rows[41]='G=25:K=238+140*V:GOSUB 1500:T=1+4*V:W=3'
                rows[42]='GOSUB 1450:NEXT V'
            rows[43]='END'
            c,r=execute(''.join(f'{n} {b}\n' for n,b in sorted(rows.items())),limit=25000000)
            OUT.mkdir(exist_ok=True)
            (OUT/(p.stem+'-'+label+'.json')).write_text(json.dumps(dict(result=r,events=c.paper_events)))
            report[p.name+'-'+label]=r;print(p.name,label,r,flush=True)
            if label=='old':previous=marks(c)
            else:
                actual=marks(c);assert actual==previous,(len(actual-previous),len(previous-actual))
                assert r['head_returns']<report[p.name+'-old']['head_returns'],r
    OUT.mkdir(exist_ok=True);(OUT/'orbital-validation.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
