"""Package a tested reception-only diagnostic. Never program the OneROM."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from build_graphics_rx_test import ROOT,OUT
from prepare_token_release import CHECKS

def main():
    image=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    digest=hashlib.sha256(image).hexdigest()
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert len(image)==32768 and manifest['sha256']==digest
    reports=list(CHECKS.values())+['array-rom-validation.json','random-validation.json',
                                 'editor-validation.json','graphics-rx-validation.json']
    for name in reports:
        report=json.loads((OUT/name).read_text())
        assert report['sha256']==digest,name
    audit=json.loads((OUT/'native-rom-audit.json').read_text())
    for group in ('decimal_add','decimal_subtract','decimal_multiply','decimal_divide',
                  'keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder'):
        assert not audit['groups'][group]['first_code_collisions'],group
    raw=image[16384:]+image[:16384]
    hardware=json.loads((ROOT/'tools/firmware/hardware_validation.json').read_text())
    confirmed=hardware['latest_validated_version']=='0.4.39-rx' and hardware['nh7_sha256']==hashlib.sha256(raw).hexdigest()
    name='s70-basic-0.4.39-rx-canon-start-nh7'
    release=ROOT/'release'
    (release/(name+'.bin')).write_bytes(raw)
    report=dict(version='0.4.39-rx',status='Reception-only diagnostic, hardware test pending',
        cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),image_bytes=len(raw),
        validation_reports=reports,candidate_manifest=manifest,
        last_hardware_validated=hardware['latest_validated_version'],
        limitations=['NO paper printing or motor control. Fixed 62x32 test image only.',
                    'No retries; transport identity is diagnostic-specific, not a final session protocol.',
                    'UART queues modeled; real timing/keyboard chord still require hardware test.',
                    'Native call audit is conservative and does not resolve all indirect calls.'],
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                       for folder in ('src','tools') for p in sorted((ROOT/folder).glob('*')) if p.is_file()})
    if confirmed:
        report['status']='Reception-only diagnostic confirmed by user on S-70'
        report['limitations'][2]='Reception and keyboard chord confirmed on S-70 by user; timing/fault scenarios not exhaustively tested.'
    (release/(name+'-manifest.json')).write_text(json.dumps(report,indent=2)+'\n')
    previous=(ROOT/'docs/status/0.4.38-dev.md').read_text(encoding='utf-8')
    size=manifest['graphics_bytes']
    status=previous.replace('0.4.38-dev','0.4.39-rx').replace('6615',str(6615+size))
    status=status.replace('tools/firmware/prepare_array_release.py','tools/firmware/prepare_graphics_rx_release.py')
    status=status.replace('Modules suivis : décimaux, tokens, tableaux, RND',
                          'Modules suivis : décimaux, tokens, tableaux, RND, éditeur, diagnostic graphique')
    status=status.replace('Fonctionnement confirmé sur S-70 par l’utilisateur ; pas une validation exhaustive des périphériques.',
        'Diagnostic de réception graphique ; validation matérielle attendue. Aucun mouvement moteur.')
    status=status.replace('Dernière référence matérielle : **0.4.39-rx**.',
        f'Dernière référence matérielle : **{hardware["latest_validated_version"]}**.')
    if confirmed:
        status=status.replace('Diagnostic de réception graphique ; validation matérielle attendue.',
                              'Réception graphique et préservation de la saisie confirmées sur S-70 par l’utilisateur.')
    status=status.replace('16 rapports','17 rapports').replace(
        '5d36480bff5eb522d74fbd260d06b633bc7c61800c494a8cf75a3a3542727a0e',report['nh7_sha256'])
    status+='\n## Diagnostic CODE+P (hors langage BASIC)\n\nRéception seulement : 62×32 pixels, quatre tuiles de 31×16. '
    status+=f'{size} octets ROM à $8800..${0x8800+size-1:04X} inclus. Tampon ASCII 150 octets, '
    status+='motif 64 octets et état/scratch 11 octets, soit 225 octets temporaires. '
    status+='Aucune réduction des 5951 octets libres du programme vide. '
    status+='Le tampon ASCII réutilise le travail arithmétique seulement en console inactive. '
    status+='Pas de moteurs, pas de reprise automatique. Voir [procédure](../basic-0.4.39-rx.md).\n'
    (ROOT/'docs/status/0.4.39-rx.md').write_text(status,encoding='utf-8')
    (ROOT/'docs/firmware-status.md').write_text(status.replace('(../basic-0.4.39-rx.md)','(basic-0.4.39-rx.md)'),encoding='utf-8')
    print('READY',name+'.bin',report['nh7_sha256'])

if __name__=='__main__':main()
