"""Package .48 with targeted checks; .47 regression evidence stays separate."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from build_serial_defaults import ROOT,OUT
def main():
    m=json.loads((OUT/'manifest.json').read_text())
    cpu=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    assert hashlib.sha256(cpu).hexdigest()==m['sha256']
    reports=['serial-config-validation.json','framing-validation.json']
    for name in reports:
        r=json.loads((OUT/name).read_text());assert r['sha256']==m['sha256'] and r['result']=='PASS'
    raw=cpu[16384:]+cpu[:16384]
    m.update(nh7_sha256=hashlib.sha256(raw).hexdigest(),validation_reports=reports,
             hardware_validated_base='0.4.47-dev: 15625 and 31250 confirmed by Pierre Raimbault',
             validation_scope='Targeted serial tests on .48; prior full regression reports remain on .47')
    name='s70-basic-0.4.48-dev-canon-start-nh7'
    (ROOT/'release'/f'{name}.bin').write_bytes(raw)
    (ROOT/'release'/f'{name}-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    text=(ROOT/'docs/status/0.4.47-dev.md').read_text(encoding='utf-8')
    text=text.replace('0.4.47-dev','0.4.48-dev').replace('tools/firmware/prepare_serial_fast_release.py','tools/firmware/prepare_serial_defaults_release.py')
    text=text.replace('7812 confirmé ; 15625 et 31250 à tester.','15625 et 31250 confirmés sur .47 ; défaut .48 : 31250/7E1.')
    text=text.replace('**0.4.45-dev**','**0.4.47-dev**')
    a=text.index('21 rapports');b=text.index('##',a)
    text=text[:a]+('Deux rapports série ciblés vérifient cette image : démarrage à 31250, 47 contrôles série, 95 caractères composés et 30 combinaisons débit/format. Les 21 rapports complets de .47 restent propres à cette version précédente. Seuls le diviseur au démarrage et un caractère de version changent (deux octets) ; aucune allocation supplémentaire.\n\nSHA-256 NH7 : `'+m['nh7_sha256']+'`.\n\n')+text[b:]
    text=text.replace('Défaut 7E1 au démarrage.','Défaut 31250/7E1 au démarrage.').replace('../basic-0.4.47.md','../basic-0.4.48.md')
    (ROOT/'docs/status/0.4.48-dev.md').write_text(text,encoding='utf-8')
    (ROOT/'docs/firmware-status.md').write_text(text.replace('(../basic-','(basic-'),encoding='utf-8')
    print('READY',name,m['nh7_sha256'])
if __name__=='__main__':main()
