"""Package .49 only after targeted LCD, RAM, retention, SCI and native audit."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'build/lcd-custom'
def main():
    m=json.loads((OUT/'manifest.json').read_text())
    cpu=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    digest=hashlib.sha256(cpu).hexdigest();assert digest==m['sha256']
    reports=['lcd-validation.json','ram-validation.json','retention-validation.json','framing-validation.json','native-rom-audit.json']
    for name in reports:assert json.loads((OUT/name).read_text())['sha256']==digest,name
    audit=json.loads((OUT/'native-rom-audit.json').read_text())
    for group in ('decimal_add','decimal_subtract','decimal_multiply','decimal_divide','keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder'):
        assert not audit['groups'][group]['first_code_collisions'],group
    raw=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.49-dev-canon-start-nh7'
    report=dict(version=m['version'],cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),
        validation_reports=reports,candidate_manifest=m,status='LCDCHAR hardware validation pending; native font substitution removed',
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for directory in ('src','tools') for p in sorted((ROOT/directory).glob('*')) if p.is_file()})
    (ROOT/'release'/f'{name}.bin').write_bytes(raw)
    (ROOT/'release'/f'{name}-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    text=(ROOT/'docs/status/0.4.48-dev.md').read_text(encoding='utf-8')
    text=text.replace('0.4.48-dev','0.4.49-dev').replace('prepare_serial_defaults_release.py','prepare_lcd_custom_release.py')
    text=text.replace('Police LCD native à comparer.','Police native préservée ; LCDCHAR à valider sur machine.')
    text=text.replace('9291','9215').replace('`LCDTRI`,','`LCDCHAR`, `LCDTRI`,')
    a=text.index('## Vérification')
    text=text[:a]+'## Vérification et décision LCD\n\nCinq rapports ciblés : LCDCHAR, état RAM, conservation au redémarrage, 30 combinaisons série et dépendances natives. Aucune validation visuelle matérielle de LCDCHAR à ce stade. Les rapports des versions antérieures restent distincts.\n\n'
    text+='Police de substitution retirée : 665 octets. Nouveau code : 225 octets. Gain net : 440 octets ROM ; neuf octets RAM temporaires hors arène. Le total des modules suivis (9215) excluait les 364 octets de lettres historiques, ce qui explique son évolution distincte du gain net.\n\n'
    text+='LCDTRI accepte seulement un espace ou un glyphe créé par LCDCHAR. Pas de copie approximative de la police native. La documentation publique devra expliquer cette décision et la limite de sept emplacements partagés.\n\n'
    text+='SHA-256 NH7 : `'+report['nh7_sha256']+'`.\n\n[Syntaxe, limites et essai](../basic-0.4.49.md).\n'
    (ROOT/'docs/status/0.4.49-dev.md').write_text(text,encoding='utf-8')
    (ROOT/'docs/firmware-status.md').write_text(text.replace('(../basic-','(basic-'),encoding='utf-8')
    print('READY',name,report['nh7_sha256'])
if __name__=='__main__':main()
