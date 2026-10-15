"""Check/package .41. No serial or OneROM device access."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json,os,subprocess,sys
from build_graphics_packed import ROOT,OUT,VERSION
from prepare_token_release import CHECKS

def main():
    reports=list(CHECKS.values())+['array-rom-validation.json','random-validation.json',
                                 'editor-validation.json','graphics-packed-validation.json']
    if '--test' in sys.argv:
        commands=[[sys.executable,'tools/validate_array_current.py',n] for n in CHECKS]
        commands += [[sys.executable,'tools/'+n+'.py'] for n in
                     ('validate_array_rom_image','validate_array_random','validate_keyboard_clear','validate_graphics_packed','test_print_image')]
        env=os.environ.copy();env['TYPESTAR_TEST_DIR']='graphics-packed'
        def run(cmd):
            result=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True)
            name=cmd[-1].replace('/','_').replace('.py','')
            (OUT/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
            return name,result.returncode
        failed=[]
        with ThreadPoolExecutor(max_workers=4) as pool:
            for future in as_completed([pool.submit(run,cmd) for cmd in commands]):
                name,status=future.result();print(name,'PASS' if status==0 else 'FAIL',flush=True)
                if status:failed.append(name)
        if failed:raise SystemExit('Failed: '+', '.join(failed))
    cpu=(OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();digest=hashlib.sha256(cpu).hexdigest()
    m=json.loads((OUT/'manifest.json').read_text());assert len(cpu)==32768 and m['sha256']==digest
    for name in reports:
        r=json.loads((OUT/name).read_text());assert r['sha256']==digest,name
    graphic=json.loads((OUT/'graphics-packed-validation.json').read_text())
    assert graphic['result']=='PASS' and len(graphic['cases'])>=33
    audit=json.loads((OUT/'native-rom-audit.json').read_text())
    for group in ('decimal_add','decimal_subtract','decimal_multiply','decimal_divide',
                  'keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder'):
        assert not audit['groups'][group]['first_code_collisions'],group
    raw=cpu[16384:]+cpu[:16384];name=f's70-basic-{VERSION}-canon-start-nh7'
    report=dict(version=VERSION,status='PC-image printing experiment; hardware validation pending',
        nh7_sha256=hashlib.sha256(raw).hexdigest(),cpu_sha256=digest,image_bytes=len(raw),
        validation_reports=reports,candidate_manifest=m,last_hardware_validated='0.4.42-gb',
        limits=['248x256 pixels, 31x16 tiles, one session per boot.',
                'A full band is buffered before native queued glyph continuation; registration needs hardware validation.',
                'Mechanical registration and heat density require real-machine validation.'],
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                       for directory in ('src','tools') for p in sorted((ROOT/directory).glob('*')) if p.is_file()})
    (ROOT/'release'/f'{name}.bin').write_bytes(raw)
    (ROOT/'release'/f'{name}-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    # Keep the command inventory from the last BASIC baseline, replace statistics.
    text=(ROOT/'docs/status/0.4.38-dev.md').read_text(encoding='utf-8')
    text=text.replace('0.4.38-dev',VERSION).replace('6615',str(6615+m['graphics_bytes']))
    text=text.replace('tools/firmware/prepare_array_release.py','tools/firmware/prepare_graphics_packed_release.py')
    text=text.replace('Fonctionnement confirmé sur S-70 par l’utilisateur ; pas une validation exhaustive des périphériques.',
                      'Image graphique série expérimentale ; validation matérielle attendue.')
    text=text.replace(f'Dernière référence matérielle : **{VERSION}**.','Dernière référence matérielle : **0.4.42-gb**.')
    text=text.replace('Modules suivis : décimaux, tokens, tableaux, RND','Modules suivis : BASIC et imprimante graphique série')
    text=text.replace('16 rapports','17 rapports').replace('5d36480bff5eb522d74fbd260d06b633bc7c61800c494a8cf75a3a3542727a0e',report['nh7_sha256'])
    text=text.replace('Les prototypes d’impression 53 + 4 octets restent hors de cette image.',
                      'Le pilote thermique, le récepteur et le pont RTI sont liés dans cette image.')
    text=text.replace('fonctions trigonométriques, LPRINT ou graphiques papier dans cet interpréteur.',
                      'fonctions trigonométriques, LPRINT ou instructions graphiques papier BASIC. '
                      'Le mode imprimante graphique série est accessible séparément par CODE+P.')
    text+='\n## Imprimante graphique série CODE+P\n\n'
    text+=f'{m["graphics_bytes"]} octets à $8800..${0x8800+m["graphics_bytes"]-1:04X}. '
    text+='Ils remplacent les 1427 octets de la .42. Tampon temporaire : 64 × nombre de blocs, '
    text+='soit 64..512 octets empruntés à l’espace libre entre DFLOOR et DHEAP, sans écraser programme ou variables. '
    text+='Si la place manque, NEW est effectué après validation du premier bloc, jamais à l’entrée CODE+P ou sur le seul en-tête. '
    text+='RAM de travail : ligne série $1DCB..$1E60 (150 octets), bloc validé $1BC0..$1BFF (64), '
    text+='décodage $1B91..$1B9B, état image/codec $1E61..$1E7D et pilote $1E80..$1E86. '
    text+='Hors NEW conditionnel, programme et variables restent intacts. '
    low=min(int(case['low_stack'],16) for case in graphic['cases'])
    text+=f'Minimum de pile observé ${low:04X}. Limite de 248 × 256 pixels, 128 blocs maximum, '
    text+='une session par démarrage. Pas de nouvelle instruction BASIC. '
    text+='[Procédure et script PC](../basic-0.4.43-gp.md).\n'
    (ROOT/f'docs/status/{VERSION}.md').write_text(text,encoding='utf-8')
    (ROOT/'docs/firmware-status.md').write_text(text.replace('(../basic-','(basic-'),encoding='utf-8')
    print('READY',name+'.bin',report['nh7_sha256'])

if __name__=='__main__':main()
