"""Package 0.4.37 only from matching completed regression reports; never flash."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib
import json
import os
from pathlib import Path
from prepare_token_release import CHECKS
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build'/os.environ.get('TYPESTAR_TEST_DIR','array-current')

def main():
    image=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    digest=hashlib.sha256(image).hexdigest()
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert manifest['sha256']==digest and manifest['version'] in ('0.4.37-dev','0.4.38-dev')
    version=manifest['version']
    hardware=json.loads((ROOT/'tools/firmware/hardware_validation.json').read_text())
    reports=list(CHECKS.values())+['array-rom-validation.json','random-validation.json']
    if version=='0.4.38-dev':reports.append('editor-validation.json')
    for name in reports:
        report=json.loads((OUT/name).read_text())
        assert report['sha256']==digest,name
    audit=json.loads((OUT/'native-rom-audit.json').read_text())
    for group in ('decimal_add','decimal_subtract','decimal_multiply','decimal_divide',
                  'keyboard_translate','startup_helper','periodic_irq','motion_scheduler','pattern_decoder'):
        assert not audit['groups'][group]['first_code_collisions'],group
    assert len(image)==32768 and manifest['array_placement']['full_placement']
    raw=image[16384:]+image[:16384]
    name=f's70-basic-{version}-canon-start-nh7.bin'
    release=ROOT/'release'
    (release/name).write_bytes(raw)
    report=dict(version=version,status='Hardware trial; CPU validated',cpu_sha256=digest,
        nh7_sha256=hashlib.sha256(raw).hexdigest(),image_bytes=len(raw),
        validation_reports=reports,candidate_manifest=manifest,
        last_hardware_validated=hardware['latest_validated_version'],
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                       for folder in ('src','tools') for p in sorted((ROOT/folder).glob('*')) if p.is_file()},
        limitations=['Original paper editor is not callable; paper BASIC is not integrated.',
                    'User hardware confirmation is not exhaustive peripheral validation.'])
    if hardware['latest_validated_version']==version and hardware['nh7_sha256']==report['nh7_sha256']:
        report['status']='CPU validated; user confirmed on S-70'
    (release/f's70-basic-{version}-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    previous=(ROOT/'docs/status/0.4.36-dev.md').read_text(encoding='utf-8')
    module_bytes=5380+1038+29+12+manifest['random']['bytes']+manifest.get('editor_clear_left_bytes',0)
    status=previous.replace('0.4.36',version.removesuffix('-dev')).replace('5380',str(module_bytes))
    status=status.replace('Version confirmée sur S-70 par l’utilisateur.',
        'Image complète validée en émulation ; confirmation sur S-70 attendue.')
    status=status.replace(f'**{version}**.','**0.4.36-dev**.')
    status=status.replace('Dernière référence matérielle : **0.4.36-dev**.',
        f'Dernière référence matérielle : **{hardware["latest_validated_version"]}**.')
    if hardware['latest_validated_version']==version and hardware['nh7_sha256']==report['nh7_sha256']:
        status=status.replace('Image complète validée en émulation ; confirmation sur S-70 attendue.',
            'Fonctionnement confirmé sur S-70 par l’utilisateur ; pas une validation exhaustive des périphériques.')
    status=status.replace('tools/firmware/prepare_token_release.py','tools/firmware/prepare_array_release.py')
    status=status.replace('| Mots-clés tokenisés | 35 |','| Mots-clés tokenisés | 37 |')
    status=status.replace('Modules décimaux/tokenisation liés','Modules suivis : décimaux, tokens, tableaux, RND')
    demo=json.loads((OUT/'array-rom-validation.json').read_text())
    status=status.replace('| Exemple fourni | 11 lignes, 211 octets RAM avec sentinelle |',
        f'| Exemple matrice | {demo["lines"]} lignes, {demo["stored_bytes"]} octets RAM avec sentinelle |')
    status=status.replace('`PRINT`, `INPUT`,','`DIM`, `PRINT`, `INPUT`,')
    status=status.replace('Variables numériques A..Z ; pas encore de variables chaînes, tableaux,',
        'Variables numériques A..Z et tableaux décimaux 1D/2D.\nUn tableau coûte 9 + 5 × nombre de cellules octets, créés par DIM.\nPas encore de variables chaînes,')
    status=status.replace('tools/transfer_token_basic.py','tools/transfer_array_basic.py')
    status=status.replace('Fonctions : `ABS`, `SGN`, `INT`, `PEEK`.',
        'Fonctions : `ABS`, `SGN`, `INT`, `PEEK`, `RND(1)`.\nRND utilise deux octets de travail à $1EC6 ; résultat de 0 à 0.9999.\nLes autres arguments RND ne sont pas encore acceptés.')
    status=status.replace('13 rapports',f'{len(reports)} rapports')
    if version=='0.4.38-dev':status+='\nMaj+Retour arrière efface à gauche du curseur, conserve le suffixe et revient en colonne zéro.\n'
    status=status.replace('3842d911260ec7fa6534be37b224046dd04998e4805b9f043f706060a1fa480e',report['nh7_sha256'])
    (ROOT/f'docs/status/{version}.md').write_text(status,encoding='utf-8')
    (ROOT/'docs/firmware-status.md').write_text(status,encoding='utf-8')
    print('READY',name,report['nh7_sha256'])

if __name__=='__main__':main()
