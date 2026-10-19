"""Package .93 after the exact CPU image passes native glyph/font regressions."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]


def main():
    out = ROOT / 'build/glyph-repeat'
    cpu = (out / 'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    manifest = json.loads((out / 'manifest.json').read_text())
    report = json.loads((out / 'validation.json').read_text())
    digest = hashlib.sha256(cpu).hexdigest()
    assert len(cpu) == 32768 and digest == manifest['sha256'] == report['sha256']
    assert report['result'] == 'PASS' and report['legacy_cases'] == 6
    assert report['font_characters'] == 95
    assert report['tokens'] == 37 and report['commands'] == 54
    assert report['break_cleanup'] and report['blank_skip']
    assert report['public_syntax_and_decimal'] and len(report['invalid_no_motion']) == 5
    assert report['free_basic_bytes'] == 5951 and manifest['explicit_free_bytes'] == 61
    row = next(v for v in report['continuous_cases'] if v['repeat'] == 10)
    assert row['native_head_returns'] == 2 and row['buffer_bytes'] == 348
    socket = cpu[16384:] + cpu[:16384]
    name = 's70-basic-0.4.93-dev-canon-start-nh7'
    for suffix, data in [('', socket), ('-64k-mirror', socket * 2)]:
        path = ROOT / 'release' / (name + suffix + '.bin')
        assert not path.exists() or path.read_bytes() == data
        path.write_bytes(data)
        path.with_suffix('.sha256').write_text(hashlib.sha256(data).hexdigest() + '  ' + path.name + '\n')
    manifest.update(nh7_sha256=hashlib.sha256(socket).hexdigest(),
                    status='Native glyph/font/BREAK regressions passed; hardware validation recorded in release notes')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (ROOT / 'release' / (name + '-manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    print(name + '.bin', manifest['nh7_sha256'])


if __name__ == '__main__':
    main()
