"""Package .49 only after targeted LCD, RAM, retention, SCI and native audit."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))

import hashlib,json

from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'build/randomize'

def main():

    m=json.loads((OUT/'manifest.json').read_text())

    cpu=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()

    digest=hashlib.sha256(cpu).hexdigest();assert digest==m['sha256']

    reports=['randomize-validation.json','lcd-validation.json','random-validation.json','native-rom-audit.json']

    for name in reports:assert json.loads((OUT/name).read_text())['sha256']==digest,name

    audit=json.loads((OUT/'native-rom-audit.json').read_text())

    for group in ('decimal_add','decimal_subtract','decimal_multiply','decimal_divide','keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder'):

        assert not audit['groups'][group]['first_code_collisions'],group

    raw=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.55-dev-canon-start-nh7'

    report=dict(version=m['version'],cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),

        validation_reports=reports,candidate_manifest=m,status='RANDOMIZE added; hardware validation pending',

        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for directory in ('src','tools') for p in sorted((ROOT/directory).glob('*')) if p.is_file()})

    (ROOT/'release'/f'{name}.bin').write_bytes(raw)

    (ROOT/'release'/f'{name}-manifest.json').write_text(json.dumps(report,indent=2)+'\n')

    text=(ROOT/'docs/status/0.4.54-dev.md').read_text(encoding='utf-8')
    text=text.replace('0.4.54-dev','0.4.55-dev').replace('prepare_fix_release.py','prepare_randomize_release.py')
    text=text.replace('**0.4.53-dev**','**0.4.54-dev**').replace('FIX ajouté.','FIX validé ; RANDOMIZE ajouté.')
    text=text.replace('`DIM`,','`RANDOMIZE`, `DIM`,')
    a=text.index('## Vérification')
    text=text[:a]+'## Vérification et ressources\n\nQuatre rapports ciblés : RANDOMIZE (séquences reproductibles, limites, rejet sans mutation, RUN), LCDCHAR, RND et dépendances natives. FIX est validé sur machine en .54.\n\nRANDOMIZE consomme 48 octets parmi les zones du décodeur récemment récupérées ; il en reste 100. Aucune RAM supplémentaire : état RND existant réutilisé. Les réservations historiques des modules ne mesurent pas exactement tous les octets occupés.\n\n'
    text+='SHA-256 NH7 : `'+report['nh7_sha256']+'`.\n\n[Syntaxe et essai](../basic-0.4.55.md).\n'
    (ROOT/'docs/status/0.4.55-dev.md').write_text(text,encoding='utf-8')
    (ROOT/'docs/firmware-status.md').write_text(text.replace('(../basic-','(basic-'),encoding='utf-8')
    print('READY',name,report['nh7_sha256'])

if __name__=='__main__':main()
