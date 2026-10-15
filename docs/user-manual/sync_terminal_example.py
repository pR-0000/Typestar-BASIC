"""Keep complete terminal listings synchronized, leaving Markdown prose editable."""
from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def sync(edition='fr'):
    path=HERE/('en' if edition=='en' else '.')/'09-terminal-papier.md'
    text=path.read_text(encoding='utf-8')
    names=[('basic','basic','terminal-en.bas'),('python','python','terminal_pc_en.py')] if edition=='en' else [('basic','basic','terminal-fr.bas'),('python','python','terminal_pc_fr.py')]
    for kind,language,name in names:
        start=f'<!-- terminal-{kind}:start -->'
        end=f'<!-- terminal-{kind}:end -->'
        source=(ROOT/'examples/terminal'/name).read_text(encoding='utf-8').rstrip()
        block=start+'\n```'+language+'\n'+source+'\n```\n'+end
        text,count=re.subn(re.escape(start)+'.*?'+re.escape(end),
                           lambda _:block,text,flags=re.S)
        assert count==1,(path,kind,count)
    path.write_text(text,encoding='utf-8')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--language',choices=['fr','en'],default='fr')
    sync(parser.parse_args().language)
