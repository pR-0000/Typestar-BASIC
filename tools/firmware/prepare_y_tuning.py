"""Package .92 only after its exact image passes the gain/motion checks."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]


def main():
    out = ROOT / 'build/paper-y-tuning'
    cpu = (out / 'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    manifest = json.loads((out / 'manifest.json').read_text())
    report = json.loads((out / 'validation.json').read_text())
    digest = hashlib.sha256(cpu).hexdigest()
    assert len(cpu) == 32768 and digest == manifest['sha256'] == report['sha256']
    assert report['result'] == 'PASS' and report['changed_bytes'] == 2
    assert report['fraction_cases'] == 3840 and report['full_cycles_checked'] == 3
    assert report['native_calls'] == 9 and report['x_commanded_drift'] == 0
    assert report['origin_spacing_preserved'] and report['font_and_dictionary_unchanged']
    assert manifest['explicit_free_bytes'] == 70
    socket = cpu[16384:] + cpu[:16384]
    name = 's70-basic-0.4.92-dev-canon-start-nh7'
    for suffix, data in [('', socket), ('-64k-mirror', socket * 2)]:
        path = ROOT / 'release' / (name + suffix + '.bin')
        assert not path.exists() or path.read_bytes() == data
        path.write_bytes(data)
        path.with_suffix('.sha256').write_text(hashlib.sha256(data).hexdigest() + '  ' + path.name + '\n')
    manifest.update(nh7_sha256=hashlib.sha256(socket).hexdigest(),
                    status='CPU fraction/motion checks passed; physical XY comparison with .91 pending')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (ROOT / 'release' / (name + '-manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    print(name + '.bin', manifest['nh7_sha256'])


if __name__ == '__main__':
    main()
