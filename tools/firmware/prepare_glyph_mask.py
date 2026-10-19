"""Package .89 only after the independent actual-ROM GLYPH checks pass."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]


def main():
    out = ROOT / 'build/glyph-mask'
    cpu = (out / 'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    manifest = json.loads((out / 'manifest.json').read_text())
    report = json.loads((out / 'glyph-validation.json').read_text())
    digest = hashlib.sha256(cpu).hexdigest()
    assert len(cpu) == 32768 and digest == manifest['sha256']
    assert report['result'] == 'PASS' and report['sha256'] == digest
    assert report['cases'] >= 6
    raw = cpu[16384:] + cpu[:16384]
    name = 's70-basic-0.4.89-dev-canon-start-nh7'
    destination = ROOT / 'release'
    for suffix, data in [('', raw), ('-64k-mirror', raw * 2)]:
        path = destination / (name + suffix + '.bin')
        assert not path.exists() or path.read_bytes() == data
        path.write_bytes(data)
        path.with_suffix('.sha256').write_text(hashlib.sha256(data).hexdigest() + '  ' + path.name + '\n')
    manifest.update(nh7_sha256=hashlib.sha256(raw).hexdigest(),
                    status='Independent GLYPH CPU validation passed; physical validation pending')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (destination / (name + '-manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    print(name + '.bin', manifest['nh7_sha256'])


if __name__ == '__main__':
    main()
