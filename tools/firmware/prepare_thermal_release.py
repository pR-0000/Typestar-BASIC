"""Package only matching tested .40 thermal image; never access OneROM USB."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from build_thermal_test import ROOT,OUT
from prepare_token_release import CHECKS

def main():
    cpu=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    digest=hashlib.sha256(cpu).hexdigest()
    m=json.loads((OUT/'manifest.json').read_text())
    assert m['sha256']==digest and len(cpu)==32768
    reports=list(CHECKS.values())+['array-rom-validation.json','random-validation.json',
                                 'editor-validation.json','thermal-validation.json']
    for name in reports:
        r=json.loads((OUT/name).read_text());assert r['sha256']==digest,name
    thermal=json.loads((OUT/'thermal-validation.json').read_text())
    assert thermal['result']=='PASS' and len(thermal['cases'])==8
    audit=json.loads((OUT/'native-rom-audit.json').read_text())
    for group in ('decimal_add','decimal_subtract','decimal_multiply','decimal_divide',
                  'keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder'):
        assert not audit['groups'][group]['first_code_collisions'],group
    raw=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.40-th-canon-start-nh7'
    report=dict(version='0.4.40-th',status='Experimental thermal print test; hardware validation pending',
        nh7_sha256=hashlib.sha256(raw).hexdigest(),cpu_sha256=digest,image_bytes=len(raw),
        validation_reports=reports,candidate_manifest=m,last_hardware_validated='0.4.39-rx',
        limits=['One fixed 31x16 glyph per boot, no serial graphic reception in this test mode.',
                'ASIC/timer readiness simulated; thermal behavior and geometry need real machine test.',
                'Native motion state intentionally persists; no absolute positioning API is claimed.',
                'Original timing tables retained, bounded wait replacements add instruction overhead.'],
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                       for directory in ('src','tools') for p in sorted((ROOT/directory).glob('*')) if p.is_file()})
    (ROOT/'release'/f'{name}.bin').write_bytes(raw)
    (ROOT/'release'/f'{name}-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    status=(ROOT/'docs/status/0.4.38-dev.md').read_text(encoding='utf-8')
    status=status.replace('0.4.38-dev','0.4.40-th').replace('6615',str(6615+791+m['thermal_bytes']))
    status=status.replace('tools/firmware/prepare_array_release.py','tools/firmware/prepare_thermal_release.py')
    status=status.replace('Fonctionnement confirmé sur S-70 par l’utilisateur ; pas une validation exhaustive des périphériques.',
        'Binaire expérimental avec sortie thermique réelle ; validation matérielle attendue.')
    status=status.replace('Dernière référence matérielle : **0.4.40-th**.',
                          'Dernière référence matérielle : **0.4.39-rx**.')
    status=status.replace('Modules suivis : décimaux, tokens, tableaux, RND',
                          'Modules suivis : BASIC, réception diagnostic et test thermique')
    status=status.replace('16 rapports','17 rapports').replace(
        '5d36480bff5eb522d74fbd260d06b633bc7c61800c494a8cf75a3a3542727a0e',report['nh7_sha256'])
    status+='\n## CODE+P : diagnostic thermique\n\n'
    status+=f'{m["thermal_bytes"]} octets supplémentaires à $8C00..${0x8C00+m["thermal_bytes"]-1:04X}, '
    status+='dont motif et messages. Dix octets de contrôle à $1B94..$1B9D, '
    status+='motif de 64 octets à $1BC0..$1BFF, sans allocation dans le tas utilisateur. '
    status+='Cadre RTI de sept octets ; minimum de pile observé $1FEB dans les tests. '
    status+='Les 53 octets du préparateur print-raw-context ne sont pas liés : '
    status+='la préparation native appelle le décodeur une seule fois. '
    status+='Un essai par démarrage, sans PC. CODE+P ne reçoit pas de flux dans cette variante ; '
    status+='LOAD/SAVE restent inchangés. [Procédure](../basic-0.4.40-th.md).\n'
    status=status.replace('Les prototypes d’impression 53 + 4 octets restent hors de cette image.',
                          'Le callback de fin de glyphe est maintenant lié dans le module thermique.')
    (ROOT/'docs/status/0.4.40-th.md').write_text(status,encoding='utf-8')
    (ROOT/'docs/firmware-status.md').write_text(status.replace('(../basic-0.4.40-th.md)','(basic-0.4.40-th.md)'),encoding='utf-8')
    print('READY',name+'.bin',report['nh7_sha256'])

if __name__=='__main__':main()
