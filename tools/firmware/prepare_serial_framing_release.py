"""Validate/package LCD ASCII composition and configurable SCI on .45."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json,os,subprocess,sys
from build_serial_framing import ROOT,OUT,VERSION
from prepare_token_release import CHECKS

def main():
    reports=list(CHECKS.values())+['array-rom-validation.json','random-validation.json',
        'editor-validation.json','graphics-packed-validation.json','inkey-validation.json','serial-config-validation.json','framing-validation.json']
    if '--test' in sys.argv:
        commands=[[sys.executable,'tools/validate_array_current.py',n] for n in CHECKS]
        commands += [[sys.executable,'tools/'+n+'.py'] for n in
            ('validate_array_rom_image','validate_array_random','validate_keyboard_clear',
             'validate_graphics_packed','validate_inkey','validate_serial_config','validate_serial_framing','test_print_image')]
        env=os.environ.copy();env['TYPESTAR_TEST_DIR']='serial-framing'
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
    report=dict(version=VERSION,status='Parity/stop configurable; native LCD font comparison pending',
        nh7_sha256=hashlib.sha256(raw).hexdigest(),cpu_sha256=digest,image_bytes=len(raw),
        validation_reports=reports,candidate_manifest=m,last_hardware_validated='0.4.45-dev (fast transfer confirmed; LCD font differs)',
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for directory in ('src','tools') for p in sorted((ROOT/directory).glob('*')) if p.is_file()})
    (ROOT/'release'/f'{name}.bin').write_bytes(raw)
    (ROOT/'release'/f'{name}-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    text=(ROOT/'docs/status/0.4.45-dev.md').read_text(encoding='utf-8')
    text=text.replace('État de Typestar BASIC — 0.4.45-dev','État de Typestar BASIC — '+VERSION)
    text=text.replace('tools/firmware/prepare_serial_config_release.py','tools/firmware/prepare_serial_framing_release.py')
    text=text.replace('9161',str(9161+m['framing_bytes'])).replace('19 rapports','20 rapports')
    text=text.replace('INKEY confirmé sur machine ; correctif LCD et débits rapides à valider.',
                      'Transfert rapide confirmé ; parité et stop configurables à valider. Police LCD à comparer.')
    text=text.replace('Dernière référence matérielle : **0.4.44-dev**, défaut de ponctuation LCD corrigé ici.',
                      'Dernière référence matérielle : **0.4.45-dev** ; différences de dessin LCD signalées.')
    text=text.replace('a0a0dacab614f86dbd5d9008ef51d1df4f384a6ec3ab7038ff1a157f3d2b9575',report['nh7_sha256'])
    text=text.replace('`SERCLOSE`.', '`SERCLOSE`, `SERCFG`.')
    text=text.replace('Le transfert reste du texte ASCII en 7E1,',
        'Le transfert reste du texte ASCII en 7N/E/O, un ou deux stops,')
    text=text.replace('Validation matérielle des débits rapides attendue.',
        'Transfert accéléré confirmé sur machine ; nouveaux formats à valider.')
    spans=', '.join(f'${a:04X}..${b-1:04X}' for a,b in m['framing_spans'])
    text+='\n## Format série\n\n'
    text+=f"SERCFG 7N1/7N2/7E1/7E2/7O1/7O2. Module : {m['framing_bytes']} octets, {spans}. "
    text+='Un octet FRAMECFG à $1B8B, hors arène. Défaut 7E1 au démarrage. '
    text+='Configuration commune à LOAD/SAVE, CODE+P et SEROPEN. '
    text+='4800 non proposé : diviseurs incompatibles avec une liaison fiable à cette fréquence. '
    text+='[Procédure et diagnostic police LCD](../basic-0.4.46.md).\n'
    (ROOT/f'docs/status/{VERSION}.md').write_text(text,encoding='utf-8')
    (ROOT/'docs/firmware-status.md').write_text(text.replace('(../basic-','(basic-'),encoding='utf-8')
    print('READY',name+'.bin',report['nh7_sha256'])

if __name__=='__main__':main()
