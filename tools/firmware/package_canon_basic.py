"""Package the built Canon-start profile without touching previous releases."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib
import json
from pathlib import Path
import zipfile
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    subprocess.run([sys.executable,str(ROOT/'tools/firmware/update_firmware_status.py')],check=True)
    out = ROOT/'build/canon-basic'
    manifest = json.loads((out/'manifest.json').read_text())
    version = manifest['version']
    stem = f's70-basic-{version}-canon-start'
    release = ROOT/'release'
    data = (out/'s70-basic-nh7.bin').read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    assert len(data) == 32768
    assert digest == manifest['images']['s70-basic-nh7.bin']['sha256']
    for name, expected in manifest['source_files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
    files = {
        stem+'-nh7.bin': data,
        stem+'-manifest.json': (out/'manifest.json').read_bytes(),
        stem+'.sha256': f'{digest}  {stem}-nh7.bin\n'.encode(),
    }
    for name, contents in files.items():
        (release/name).write_bytes(contents)
    with zipfile.ZipFile(release/(stem+'.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
        for directory in ('src','tools','tests','docs','examples','build/canon-basic'):
            for path in (ROOT/directory).rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts:
                    archive.write(path, path.relative_to(ROOT))
        archive.write(ROOT/'README.md','README.md')
        budget = ROOT/'_local/development/analysis/typestar-basic-budget.json'
        if budget.exists():
            archive.write(budget, 'analysis/typestar-basic-budget.json')
        audit = ROOT/'_local/development/analysis/startup-retention-audit.json'
        if audit.exists():archive.write(audit,'analysis/startup-retention-audit.json')
        for name in files:
            archive.write(release/name,'release/'+name)
        for name in ('s70-canon-print-probe-nh7.bin','s70-canon-print-probe-manifest.json','s70-canon-print-probe.sha256'):
            if (release/name).exists():
                archive.write(release/name,'release/'+name)
    print(stem+'-nh7.bin', len(data), digest)


if __name__ == '__main__':
    main()
