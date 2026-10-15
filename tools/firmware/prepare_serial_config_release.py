"""Validate/package LCD ASCII composition and configurable SCI on .45."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json,os,subprocess,sys
from build_serial_config import ROOT,OUT,VERSION
from prepare_token_release import CHECKS

def main():
    reports=list(CHECKS.values())+['array-rom-validation.json','random-validation.json',
        'editor-validation.json','graphics-packed-validation.json','inkey-validation.json','serial-config-validation.json']
    if '--test' in sys.argv:
        commands=[[sys.executable,'tools/validate_array_current.py',n] for n in CHECKS]
        commands += [[sys.executable,'tools/'+n+'.py'] for n in
            ('validate_array_rom_image','validate_array_random','validate_keyboard_clear',
             'validate_graphics_packed','validate_inkey','validate_serial_config','test_print_image')]
        env=os.environ.copy();env['TYPESTAR_TEST_DIR']='serial-config'
        def run(cmd):
            r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True)
            name=cmd[-1].replace('/','_').replace('.py','')
            (OUT/(name+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
            return name,r.returncode
        failed=[]
        with ThreadPoolExecutor(max_workers=4) as pool:
            for future in as_completed([pool.submit(run,cmd) for cmd in commands]):
                name,status=future.result();print(name,'FAIL' if status else 'PASS',flush=True)
                if status:failed.append(name)
        if failed:raise SystemExit('Failed: '+', '.join(failed))
    cpu=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    digest=hashlib.sha256(cpu).hexdigest();m=json.loads((OUT/'manifest.json').read_text())
    assert len(cpu)==32768 and m['sha256']==digest
    for name in reports:
        r=json.loads((OUT/name).read_text());assert r['sha256']==digest,name
    audit=json.loads((OUT/'native-rom-audit.json').read_text())
    for group in ('decimal_add','decimal_subtract','decimal_multiply','decimal_divide',
                  'keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder'):
        assert not audit['groups'][group]['first_code_collisions'],group
    raw=cpu[16384:]+cpu[:16384];name=f's70-basic-{VERSION}-canon-start-nh7'
    report=dict(version=VERSION,status='LCD ASCII and faster SCI awaiting hardware test',
        nh7_sha256=hashlib.sha256(raw).hexdigest(),cpu_sha256=digest,image_bytes=len(raw),
        validation_reports=reports,candidate_manifest=m,last_hardware_validated='0.4.44-dev (LCD punctuation defect reported)',
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for directory in ('src','tools') for p in sorted((ROOT/directory).glob('*')) if p.is_file()})
    (ROOT/'release'/f'{name}.bin').write_bytes(raw)
    (ROOT/'release'/f'{name}-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    text=(ROOT/'docs/status/0.4.44-dev.md').read_text(encoding='utf-8')
    text=text.replace('0.4.44-dev',VERSION).replace('tools/firmware/prepare_inkey_release.py','tools/firmware/prepare_serial_config_release.py')
    text=text.replace('8426',str(8426+m['serial_config_bytes'])).replace('18 rapports','19 rapports')
    text=text.replace('INKEY testé en émulation ; validation clavier sur machine attendue.',
        'INKEY confirmé sur machine ; correctif LCD et débits rapides à valider.')
    text=text.replace('Dernière référence matérielle : **0.4.43-gp**.',
        'Dernière référence matérielle : **0.4.44-dev**, défaut de ponctuation LCD corrigé ici.')
    text=text.replace('Le transfert reste du texte ASCII en 1200/7E1 avec',
        'Le transfert reste du texte ASCII en 7E1, à 1200/2400/7812 bauds, avec')
    text=text.replace('`LCDTRI`, `LCDLINE`, `BEEP`, `SOUND`, `POKE`, `KEYS`.',
        '`LCDTRI`, `LCDLINE`, `BEEP`, `SOUND`, `POKE`, `KEYS`, `BAUD`, `SEROPEN`, `SEROUT`, `SERCLOSE`.')
    text=text.replace('`INKEY(0)`.', '`INKEY(0)`, `SERIN(0)`.')
    text=text.replace('ce28b4c4f8dc75dbc8202038203109a4a051604abb3ee0d33fa3a0980369a7ea',report['nh7_sha256'])
    text+='\n## LCD ASCII et série configurable\n\n'
    spans=', '.join(f'${a:04X}..${b-1:04X}' for a,b in m['serial_config_spans'])
    text+=f"Module : {m['serial_config_bytes']} octets, {spans}. "
    text+='BAUDCONST : $1B8A, un octet hors arène. BAUD 1200/2400/7812 commun à LOAD/SAVE et CODE+P. '
    text+='SEROPEN débit, SEROUT valeur, SERIN(0), SERCLOSE : API 7E1 sans file RX logicielle. '
    text+='95 caractères ASCII imprimables composables avec LCDTRI. '
    text+='Nouveaux noms conservés en ASCII ; dictionnaire inchangé. '
    text+='Validation matérielle des débits rapides attendue. [Procédure](../basic-0.4.45.md).\n'
    (ROOT/f'docs/status/{VERSION}.md').write_text(text,encoding='utf-8')
    (ROOT/'docs/firmware-status.md').write_text(text.replace('(../basic-','(basic-'),encoding='utf-8')
    print('READY',name+'.bin',report['nh7_sha256'])

if __name__=='__main__':main()
