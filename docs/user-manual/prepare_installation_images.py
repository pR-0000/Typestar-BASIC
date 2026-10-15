"""Prepare read-only ROM files for the manual; never program hardware."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def prepare():
    version = json.loads((HERE / 'manuel-fr.json').read_text(encoding='utf-8'))['version']
    source = ROOT / 'release' / f's70-basic-{version}-canon-start-nh7.bin'
    data = source.read_bytes()
    if len(data) != 32768:
        raise ValueError('The IC8 source must be exactly 32768 bytes')
    manifest = json.loads(source.with_name(source.stem + '-manifest.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(data).hexdigest()
    if manifest['version'] != version or manifest['nh7_sha256'] != digest:
        raise ValueError('Source version or SHA-256 does not match the release manifest')
    target = ROOT / 'release' / 'installation'
    target.mkdir(exist_ok=True)
    prepared = {'typestar-basic-32k.bin': data, 'typestar-basic-64k-mirror.bin': data + data}
    entries = []
    for name, content in prepared.items():
        path = target / name
        path.write_bytes(content)
        assert path.read_bytes() == content
        entries.append({'file': name, 'bytes': len(content),
                        'sha256': hashlib.sha256(content).hexdigest()})
    mirrored = (target / 'typestar-basic-64k-mirror.bin').read_bytes()
    assert mirrored[:32768] == mirrored[32768:] == data
    (target / 'manifest.json').write_text(json.dumps({
        'version': version, 'source': source.name, 'source_sha256': digest,
        'files': entries, 'operation': 'File preparation only; no device access',
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (target / 'SHA256SUMS.txt').write_text(''.join(
        f"{entry['sha256']}  {entry['file']}\n" for entry in entries), encoding='ascii')
    print(json.dumps({'version': version, 'files': entries, 'device_access': False}))


if __name__ == '__main__':
    prepare()
