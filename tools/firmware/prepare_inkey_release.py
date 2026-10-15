"""Validate/package INKEY, retaining the validated serial graphics driver."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json,os,subprocess,sys
from build_inkey import ROOT,OUT,VERSION
from prepare_token_release import CHECKS

def main():
    reports=list(CHECKS.values())+['array-rom-validation.json','random-validation.json',
        'editor-validation.json','graphics-packed-validation.json','inkey-validation.json']
    if '--test' in sys.argv:
        commands=[[sys.executable,'tools/validate_array_current.py',n] for n in CHECKS]
        commands += [[sys.executable,'tools/'+n+'.py'] for n in
            ('validate_array_rom_image','validate_array_random','validate_keyboard_clear',
             'validate_graphics_packed','validate_inkey','test_print_image')]
        env=os.environ.copy();env['TYPESTAR_TEST_DIR']='inkey-current'
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
    report=dict(version=VERSION,status='INKEY hardware validation pending; graphics validated on .43',
        nh7_sha256=hashlib.sha256(raw).hexdigest(),cpu_sha256=digest,image_bytes=len(raw),
        validation_reports=reports,candidate_manifest=m,last_hardware_validated='0.4.43-gp',
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for directory in ('src','tools') for p in sorted((ROOT/directory).glob('*')) if p.is_file()})
    (ROOT/'release'/f'{name}.bin').write_bytes(raw)
    (ROOT/'release'/f'{name}-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    text=(ROOT/'docs/status/0.4.43-gp.md').read_text(encoding='utf-8')
    text=text.replace('État de Typestar BASIC — 0.4.43-gp','État de Typestar BASIC — '+VERSION)
    text=text.replace('tools/firmware/prepare_graphics_packed_release.py','tools/firmware/prepare_inkey_release.py')
    text=text.replace('Image graphique série expérimentale ; validation matérielle attendue.',
        'INKEY testé en émulation ; validation clavier sur machine attendue.')
    text=text.replace('**0.4.42-gb**','**0.4.43-gp**').replace('8274','8426')
    text=text.replace('17 rapports','18 rapports').replace('`RND(1)`','`RND(1)`, `INKEY(0)`')
    text=text.replace('5b29e05f91105c0de542733a77b9ca8a10858c4b35bb9d3bc06113a49d5e5f38',report['nh7_sha256'])
    text+='\n## Clavier non bloquant\n\n'
    text+='INKEY(0) : 152 octets à $8E7B..$8F12, un octet de travail à $1B90. '
    text+='Aucun prélèvement supplémentaire dans l’arène BASIC. Renvoie un code de caractère '
    text+='ou zéro ; une touche conservée entre instructions, BREAK prioritaire. '
    text+='Nom conservé en ASCII dans les lignes tokenisées (37 mots-clés inchangés). '
    text+='Voir [syntaxe, limites et exemple](../basic-0.4.44.md).\n'
    (ROOT/f'docs/status/{VERSION}.md').write_text(text,encoding='utf-8')
    (ROOT/'docs/firmware-status.md').write_text(text.replace('(../basic-','(basic-'),encoding='utf-8')
    print('READY',name+'.bin',report['nh7_sha256'])

if __name__=='__main__':main()
