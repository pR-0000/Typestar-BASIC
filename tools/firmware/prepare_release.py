"""Package existing tested BASIC artifacts and verified original NH7; no flash."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    out = ROOT / 'release'
    out.mkdir(exist_ok=True)
    original = ROOT.parents[1] / 'ROMReader/dumps/256ROM_NH7_1181.bin'
    raw = original.read_bytes()
    assert len(raw) == 32768
    assert hashlib.sha256(raw).hexdigest() == '5eb09f28e9e93989631544f1f13defe32679e86300702692e5c7d137f168f03c'
    manifest = json.loads((ROOT / 'build/manifest.json').read_text())
    for name, expected in manifest['source_files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, 'rebuild changed source first'
    for name, meta in manifest['images'].items():
        data = (ROOT / 'build' / name).read_bytes()
        assert len(data) == meta['size'] and hashlib.sha256(data).hexdigest() == meta['sha256']
    shutil.copyfile(original, out / 'nh7-original-1181.bin')
    for name in ('s70-basic-nh7.bin', 'manifest.json', 'validation.md'):
        shutil.copyfile(ROOT / 'build' / name, out / name)
    sums = ''.join(hashlib.sha256((out / name).read_bytes()).hexdigest()+'  '+name+'\n'
                   for name in ('nh7-original-1181.bin', 's70-basic-nh7.bin'))
    (out / 'SHA256SUMS.txt').write_text(sums, encoding='ascii')
    version = manifest['version']
    versioned = f's70-basic-{version}-nh7.bin'
    shutil.copyfile(out / 's70-basic-nh7.bin', out / versioned)
    sums += hashlib.sha256((out / versioned).read_bytes()).hexdigest()+'  '+versioned+'\n'
    diagnostic_dir = ROOT / 'build/lcd-only'
    dm = json.loads((diagnostic_dir / 'manifest.json').read_text())
    assert dm['profile'] == 'lcd-only' and dm['version'] == version
    for name, expected in dm['source_files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    diag_data = (diagnostic_dir / 's70-basic-nh7.bin').read_bytes()
    assert hashlib.sha256(diag_data).hexdigest() == dm['images']['s70-basic-nh7.bin']['sha256']
    diagnostic_name = f's70-lcd-only-{version}-nh7.bin'
    (out / diagnostic_name).write_bytes(diag_data)
    sums += hashlib.sha256(diag_data).hexdigest()+'  '+diagnostic_name+'\n'
    (out / 'SHA256SUMS.txt').write_text(sums, encoding='ascii')
    archive = out / f's70-basic-{version}-fire28.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for directory in ('src', 'docs', 'tools', 'tests', 'examples'):
            for path in sorted((ROOT / directory).rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts:
                    z.write(path, path.relative_to(ROOT))
        z.write(ROOT / 'README.md', 'README.md')
        for name in ('nh7-original-1181.bin','s70-basic-nh7.bin','manifest.json','SHA256SUMS.txt','validation.md'):
            z.write(out / name, 'release/'+name)
        z.write(out / versioned, 'release/'+versioned)
        z.write(out / diagnostic_name, 'release/'+diagnostic_name)
        for path in sorted(diagnostic_dir.iterdir()):
            if path.is_file():
                z.write(path, path.relative_to(ROOT))
        for name in ('s70-basic-cpu.bin','s70-basic-nh7.bin','manifest.json','symbols.json','basic.bin','basic.lst','validation.md'):
            z.write(ROOT / 'build' / name, 'build/'+name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert z.read('release/s70-basic-nh7.bin') == (out / 's70-basic-nh7.bin').read_bytes()
    print(archive)
    print(sums)


if __name__ == '__main__':
    main()
