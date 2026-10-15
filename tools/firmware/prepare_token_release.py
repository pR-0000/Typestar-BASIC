"""Validate and package the decimal/token S-70 hardware trial. Never flashes.

Input: build/token-current candidate and the archived 0.4.34 base. Run
build_token_current.py first after changing linked sources. Reports must all
refer to the exact CPU image being packaged. Native paper services stay unused.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/token-current'
VERSION='0.4.36-dev'
CHECKS={
    'validate_token_current':'validation.json',
    'validate_token_serial':'serial-validation.json',
    'validate_token_retention':'retention-validation.json',
    'validate_decimal_if':'decimal-if-validation.json',
    'validate_decimal_for':'decimal-for-validation.json',
    'validate_token_statements':'statements-validation.json',
    'validate_decimal_radix':'radix-validation.json',
    'validate_decimal_functions':'functions-validation.json',
    'validate_candidate_ram':'ram-validation.json',
    'validate_native_flag_query':'native-flag-validation.json',
    'audit_candidate_rom':'native-rom-audit.json',
    'validate_token_release_demo':'release-demo-validation.json',
    'validate_inline_then':'inline-then-validation.json',
}

def sha(data):return hashlib.sha256(data).hexdigest()

def write_status(report, manifest):
    base=json.loads((ROOT/'build/decimal-current/manifest.json').read_text())
    modules=base['modules']+manifest['runtime_segments']+manifest['loop_modules']+manifest['statement_modules']
    module_bytes=sum(m['bytes'] for m in modules)+sum(manifest[k] for k in
        ('save_bytes','format_bytes','decimal_if_bytes','retention_bytes'))
    demo=json.loads((OUT/'release-demo-validation.json').read_text())
    hardware=json.loads((ROOT/'tools/firmware/hardware_validation.json').read_text())
    validated=hardware['latest_validated_version']
    state=('Version confirmée sur S-70 par l’utilisateur.' if
        validated==VERSION and hardware['nh7_sha256']==report['nh7_sha256'] else
        'Image d’essai CPU-validée ; validation matérielle attendue.')
    text=f'''# État de Typestar BASIC — {VERSION}

Généré par `tools/firmware/prepare_token_release.py`. {state}
Dernière référence matérielle : **{validated}**.

| Mesure | Valeur |
|---|---:|
| Image IC8 / NH7 | 32768 octets |
| Modules décimaux/tokenisation liés | {module_bytes} octets |
| Arène programme et variables | 5952 octets |
| Libre à vide, sentinelle déduite | 5951 octets |
| Variable numérique créée | 6 octets |
| Gestion par ligne | 3 octets + corps tokenisé |
| Numéros de lignes | 1..65535 |
| Exemple fourni | {demo['lines']} lignes, {demo['stored_bytes_including_sentinel']} octets RAM avec sentinelle |
| Mots-clés tokenisés | 35 |
| Précision décimale | 8 chiffres significatifs, au plus 7 décimales |
| Saisie par ligne | 63 caractères, numéro compris |
| Profondeur FOR / GOSUB | 8 / 8 |

Les {module_bytes} octets de modules ne représentent **ni tout le firmware ni
un besoin net supplémentaire** : certains remplacent d’anciens chemins entiers.
Le reste du BASIC, les données LCD et les services Canon conservés occupent
également IC8. Aucune réserve globale de ROM libre n’est affirmée ici.
Les prototypes d’impression 53 + 4 octets restent hors de cette image.

L’arène est partagée : les variables réduisent MEM pendant l’exécution.
Le nombre de lignes n’est plus limité à 255 : 1000 lignes sont exécutées dans
les tests. Le maximum dépend du contenu, avec un plafond de 1487 enregistrements
minimaux de quatre octets (par exemple REM vide), et non 65535 lignes en RAM.

## Commandes intégrées

`PRINT`, `INPUT`, `LET`/affectation, `RUN`, `LIST` et ses plages, `NEW`, `GOTO`,
`IF ... THEN numéro/instruction`, `FOR ... TO ... STEP`, `NEXT`, `GOSUB`, `RETURN`, `END`,
`REM`, `HELP`, `MEM`, `LOAD`, `SAVE`, `CLS`, `LOCATE`, `CURSOR`, `ICON`,
`LCDTRI`, `LCDLINE`, `BEEP`, `SOUND`, `POKE`, `KEYS`.
Fonctions : `ABS`, `SGN`, `INT`, `PEEK`. Opérateurs : `+ - * /`, parenthèses,
comparaisons ; constantes décimales, `%binaires`, `&Hhexadécimales`.
Instructions multiples séparées par `:`.

Variables numériques A..Z ; pas encore de variables chaînes, tableaux,
fonctions trigonométriques, LPRINT ou graphiques papier dans cet interpréteur.
Le programme retenu utilise la signature $5424 ; l’ancien format $5423 n’est
pas converti. Le transfert reste du texte ASCII en 1200/7E1 avec
`tools/transfer_token_basic.py`.

## Vérification

{len(CHECKS)} rapports correspondent à la même image CPU. Calculs, erreurs,
contrôle de flux, éditeur, listing, série simulée, conservation après boot,
état RAM LCD et dépendances natives sont contrôlés. Les périphériques et les
temps réels restent à valider sur machine.

SHA-256 NH7 : `{report['nh7_sha256']}`.

Voir [la procédure et les limites détaillées](basic-0.4.36.md).
'''
    (ROOT/'docs/firmware-status.md').write_text(text,encoding='utf-8')
    historical=text.replace('(basic-0.4.36.md)','(../basic-0.4.36.md)')
    (ROOT/'docs/status'/f'{VERSION}.md').write_text(historical,encoding='utf-8')

def main():
    image=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    digest=sha(image)
    assert len(image)==32768 and (b'Typestar BASIC '+VERSION.encode()) in image
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert manifest['sha256']==digest
    stable=(ROOT/'build/canon-basic/s70-basic-cpu.bin').read_bytes()
    assert sha(stable)=='2916f9387c07847e6472d3ad7a945e114debd8d46b49802f3c85b2e87d458d20'
    assert image[0x2800:0x2859]==stable[0x2800:0x2859]
    assert image[0x6C00:]==stable[0x6C00:]

    def check(item):
        tool,report=item
        path=OUT/report
        # Reuse only a report for this exact image newer than its test source.
        source=ROOT/'tools'/f'{tool}.py'
        cached=path.exists() and path.stat().st_mtime>=source.stat().st_mtime
        if not cached or json.loads(path.read_text()).get('sha256')!=digest:
            result=subprocess.run([sys.executable,str(source)],cwd=ROOT,capture_output=True,text=True)
            (OUT/f'{tool}.log').write_text(result.stdout+result.stderr,encoding='utf-8')
            if result.returncode:raise RuntimeError(f'{tool} failed; see build/token-current/{tool}.log')
        assert json.loads(path.read_text())['sha256']==digest,report
        return tool

    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in as_completed([pool.submit(check,item) for item in CHECKS.items()]):
            print('PASS',result.result(),flush=True)
    audit=json.loads((OUT/'native-rom-audit.json').read_text())
    for group in ('decimal_add','decimal_subtract','decimal_multiply','decimal_divide',
                  'keyboard_translate','startup_helper','periodic_irq'):
        assert not audit['groups'][group]['first_code_collisions'],group
    assert sha((OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes())==digest
    raw=image[16384:]+image[:16384]
    release=ROOT/'release';release.mkdir(exist_ok=True)
    name=f's70-basic-{VERSION}-canon-start-nh7.bin'
    (release/name).write_bytes(raw)
    report=dict(version=VERSION,status='hardware-trial; CPU-validated, not yet hardware-validated',
        cpu_sha256=digest,nh7_sha256=sha(raw),image_bytes=len(raw),
        stable_version='0.4.35-dev',ram_arena_bytes=5952,empty_program_free=5951,
        retention_signature='5424',validation_reports=list(CHECKS.values()),
        source_sha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted((ROOT/'src').glob('*')) if p.is_file()},
        candidate_manifest=manifest,
        limitations=['Old 5423 RAM programs are discarded: SAVE as text before flashing.',
                     'Paper printing/graphics are not integrated; printer experiments are not linked.',
                     'S-70 only. Serial/motor timing and electrical behavior require hardware testing.'])
    (release/f's70-basic-{VERSION}-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    write_status(report,manifest)
    print('READY',name,'SHA256',sha(raw),flush=True)

if __name__=='__main__':main()
