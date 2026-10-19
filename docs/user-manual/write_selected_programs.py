"""Keep the manual's complete selected listings identical to examples/."""
from pathlib import Path
import hashlib,json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def write_chapter(config):
    english=config.get('language')=='en'
    destination=HERE/config.get('content_directory','.')
    if english:
        out=['# 11 - Complete programs to try','',
             'This Typestar BASIC selection includes a sound instrument, an LCD game and paper games. Open the named file in **Typestar BASIC Studio**, then use **Run (F5)** in the emulator or **Send → LOAD** for the Canon. The listings below are the complete sources of the supplied files.','',
             '![Printy discovers games on the display and on paper.](../images/printy-jeux.png)','',
             '**Memory holds one program at a time.** Save your work before loading a game. For printed games, prefer **thermal paper** and let the motors position the sheet during play. Old transfer ribbons would be consumed quickly.','']
        report=[]
        for entry in config['example_programs']:
            p=ROOT/'examples'/entry['file'];source=p.read_text(encoding='utf-8-sig').rstrip('\r\n')
            out+=['## '+entry['title'],'',entry['description'],'',entry['controls'],'']
            for illustration in entry.get('illustrations',[]):
                out+=['!['+illustration['caption']+'](images/'+illustration['file']+')','']
            out+=['**What to look for:** '+entry['learning'],'',
                  '**File to open in Studio:** ['+entry['file']+'](../../../examples/'+entry['file']+').','',
                  '```basic',source,'```','']
            report.append({'file':entry['file'],'lines':len(source.splitlines()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        (destination/'11-programmes-complets.md').write_text('\n'.join(out),encoding='utf8')
        (ROOT/'build/user-manual/selected-programs-en.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        return
    out=['# 11 - Des programmes complets à essayer','',
         'La sélection Typestar BASIC réunit un instrument sonore, un jeu sur LCD et des jeux sur papier. Ouvrez le fichier indiqué dans **Typestar BASIC Studio**, puis utilisez **Exécuter (F5)** dans l’émulateur ou **Envoyer → LOAD** pour la Canon. Les listings ci-dessous sont les codes sources complets des fichiers fournis.','',
         '![Printy découvre les jeux sur écran et sur papier.](images/printy-jeux.png)','',
         '**Un seul programme tient en mémoire à la fois.** Sauvegardez votre travail avant de charger un jeu. Pour les jeux imprimés, utilisez de préférence du **papier thermique** et laissez les moteurs positionner la feuille pendant la partie. Les anciens rubans de transfert seraient rapidement consommés.','']
    report=[]
    for entry in config['example_programs']:
        p=ROOT/'examples'/entry['file'];source=p.read_text(encoding='utf-8-sig').rstrip('\r\n')
        out += ['## '+entry['title'],'',entry['description'],'',entry['controls'],'']
        for illustration in entry.get('illustrations', []):
            out += ['!['+illustration['caption']+'](images/'+illustration['file']+')','']
        out += ['**À observer dans le programme :** '+entry['learning'],'',
                '**Fichier à ouvrir dans Studio :** ['+entry['file']+'](../../examples/'+entry['file']+').','',
                '```basic',source,'```','']
        report.append({'file':entry['file'],'lines':len(source.splitlines()),
                       'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    (HERE/'11-programmes-complets.md').write_text('\n'.join(out),encoding='utf-8')
    folder=ROOT/'build/user-manual';folder.mkdir(parents=True,exist_ok=True)
    (folder/'selected-programs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
    write_chapter(json.loads((HERE/'manuel-fr.json').read_text(encoding='utf-8')))
