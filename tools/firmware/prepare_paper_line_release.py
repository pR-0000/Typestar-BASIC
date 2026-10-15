"""Package the uniform-coordinate PBOX image after matching-image checks."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
base = ROOT / 'build/paper-line-linked'

def main():
    cpu = (base / 'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    digest = hashlib.sha256(cpu).hexdigest()
    manifest = json.loads((base / 'manifest.json').read_text())
    assert len(cpu) == 32768 and digest == manifest['sha256']
    assert manifest['version'] == '0.4.58-dev' and manifest['paper_real_ram']
    paths = [base / name for name in (
        'line-validation.json', 'keyboard-validation.json', 'retention-validation.json', 'decimal-for-validation.json', 'graphics-packed-validation.json',
        'paper-errors-validation.json', 'native-rom-audit.json')]
    paths.append(ROOT / 'build/paper-line-linked-test/validation.json')
    for path in paths:
        report = json.loads(path.read_text())
        assert report['sha256'] == digest, path
        if 'result' in report:
            assert report['result'] == 'PASS', path
    audit = json.loads((base / 'native-rom-audit.json').read_text())
    for group in ('decimal_add', 'decimal_subtract', 'decimal_multiply',
                  'decimal_divide', 'keyboard_translate', 'startup_helper',
                  'motion_scheduler', 'periodic_irq', 'pattern_decoder'):
        assert not audit['groups'][group]['first_code_collisions'], group
    raw = cpu[16384:] + cpu[:16384]
    name = 's70-basic-0.4.58-dev-canon-start-nh7'
    target = ROOT / 'release' / (name + '.bin')
    assert not target.exists() or target.read_bytes() == raw
    report = dict(version='0.4.58-dev', status='PLINE hardware validation pending; PBOX aspect ratio validated in .57',
                  cpu_sha256=digest, nh7_sha256=hashlib.sha256(raw).hexdigest(),
                  paper_code_bytes=1585, known_free_fragmented_bytes=107,
                  ram=manifest['paper_ram_map'], candidate_manifest=manifest,
                  validation_reports=[str(p.relative_to(ROOT)) for p in paths],
                  limits=['Approximate 2:1 native dot aspect ratio',
                          'One PBOX, PLINE or CODE+P job per boot',
                          'PBOX Y=0..255 logical units, 128 native rows',
                          'Native paper font partially replaced; LPRINT unavailable'],
                  source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for d in ('src', 'tools') for p in sorted((ROOT/d).glob('*')) if p.is_file()})
    target.write_bytes(raw)
    target.with_name(name + '-manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(target.name, report['nh7_sha256'])

if __name__ == '__main__':
    main()
