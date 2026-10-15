"""Package .49 only after targeted LCD, RAM, retention, SCI and native audit."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))

import hashlib,json

from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'build/sqr'

def main():

    m=json.loads((OUT/'manifest.json').read_text())

    cpu=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()

    digest=hashlib.sha256(cpu).hexdigest();assert digest==m['sha256']

    reports=['sqr-validation.json','fre-validation.json','lcd-validation.json','native-rom-audit.json']

    for name in reports:assert json.loads((OUT/name).read_text())['sha256']==digest,name

    audit=json.loads((OUT/'native-rom-audit.json').read_text())

    for group in ('decimal_add','decimal_subtract','decimal_multiply','decimal_divide','keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder'):

        assert not audit['groups'][group]['first_code_collisions'],group

    raw=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.51-dev-canon-start-nh7'

    report=dict(version=m['version'],cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),

        validation_reports=reports,candidate_manifest=m,status='SQR added; hardware validation pending',

        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for directory in ('src','tools') for p in sorted((ROOT/directory).glob('*')) if p.is_file()})

    (ROOT/'release'/f'{name}.bin').write_bytes(raw)

    (ROOT/'release'/f'{name}-manifest.json').write_text(json.dumps(report,indent=2)+'\n')

    text=(ROOT/'docs/status/0.4.50-dev.md').read_text(encoding='utf-8')
    text=text.replace('0.4.50-dev','0.4.51-dev').replace('prepare_fre_release.py','prepare_sqr_release.py')
    text=text.replace('9319','9647').replace('`FRE(0)`,','`SQR(x)`, `FRE(0)`,')
    text=text.replace('FRE(0) ajouté.','SQR ajouté.')
    a=text.index('## Vérification')
    text=text[:a]+'## Vérification et ressources\n\nQuatre rapports ciblés : SQR (valeurs nulles, carrés, fractions, limites, arguments, appels imbriqués et programme), FRE, LCDCHAR et dépendances natives. SQR reste à confirmer sur machine.\n\nSQR ajoute 328 octets ROM et 19 octets de travail hors arène. Huit octets restent dans les deux zones de police récupérées ; ce ne sont pas tous les éventuels espaces disponibles en ROM.\n\n'
    text+='SHA-256 NH7 : `'+report['nh7_sha256']+'`.\n\n[Syntaxe et essai](../basic-0.4.51.md).\n'
    (ROOT/'docs/status/0.4.51-dev.md').write_text(text,encoding='utf-8')
    (ROOT/'docs/firmware-status.md').write_text(text.replace('(../basic-','(basic-'),encoding='utf-8')
    print('READY',name,report['nh7_sha256'])

if __name__=='__main__':main()
