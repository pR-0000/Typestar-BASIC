"""Build .92 from .91 with a smaller, separately applied paper correction.

Only the fractional-gain operand and one version digit change. Reassemble the
shared routine to verify the exact instruction and its unchanged control flow.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = '5eaaf3462af9f968a5113b4a78ec6fb17166ed478bfa4f0574d16d200f6b25fe'
VERSION = '0.4.92-dev'
GAIN = 64


def main():
    base = ROOT / 'release/s70-basic-0.4.91-dev-canon-start-nh7.bin'
    socket = base.read_bytes()
    old = socket[16384:] + socket[:16384]
    assert len(old) == 32768 and hashlib.sha256(old).hexdigest() == BASE_SHA
    manifest = json.loads(base.with_name(base.stem + '-manifest.json').read_text())
    symbols = json.loads((ROOT / 'studio/internal/profiles/basic-0.4.91-symbols.json').read_text())
    symbols['YPGAIN'] = GAIN
    out = ROOT / 'build/paper-y-tuning'
    out.mkdir(exist_ok=True)
    body = re.split(r'; @island \w+\n', (ROOT / 'src/paper-y-poststep.asm').read_text())[0]
    labels = set(re.findall(r'^([A-Z][A-Z0-9_]*)\b', body, re.M))
    definitions = ''.join(f'{k} EQU ${v:04X}\n' for k, v in symbols.items() if k not in labels)
    source = out / 'post.asm'
    source.write_text(' OPT H01\n' + definitions + f" ORG ${symbols['YPPOST']:04X}\n" + body,
                      encoding='ascii')
    assembler = ROOT.parent.parent / 'ROMReader/tmp/m680x-tools/a09.exe'
    run = subprocess.run([str(assembler), '-W', '-B' + str(source.with_suffix('.bin')),
                          '-L' + str(source.with_suffix('.lst')), str(source)],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    code = source.with_suffix('.bin').read_bytes()
    start = symbols['YPPOST'] - 0x4000
    end = symbols['YPEND'] - 0x4000
    previous = old[start:end]
    assert len(code) == len(previous) == 39
    changes = [i for i, (a, b) in enumerate(zip(previous, code)) if a != b]
    assert len(changes) == 1
    gain_offset = changes[0]
    assert previous[gain_offset - 1:gain_offset + 1] == bytes((0x8B, 96))
    assert code[gain_offset - 1:gain_offset + 1] == bytes((0x8B, GAIN))
    cpu = bytearray(old)
    cpu[start:end] = code
    banner = b'Typestar BASIC 0.4.91-dev'
    assert old.count(banner) == 1
    banner_start = old.index(banner)
    cpu[banner_start:banner_start + len(banner)] = b'Typestar BASIC 0.4.92-dev'
    changed = [i + 0x4000 for i, (a, b) in enumerate(zip(old, cpu)) if a != b]
    assert len(changed) == 2
    assert start + gain_offset + 0x4000 in changed
    manifest.update(version=VERSION, sha256=hashlib.sha256(cpu).hexdigest(),
                    base_cpu_sha256=BASE_SHA,
                    status='Gain reduced to 1/4; CPU checks and physical validation pending')
    manifest.pop('nh7_sha256', None)
    manifest['y_poststep'].update(numerator=1, denominator=4, fraction_increment=GAIN)
    manifest['y_tuning'] = dict(base_version='0.4.91-dev', changed_addresses=changed,
                               previous_fraction_increment=96, fraction_increment=GAIN,
                               algorithm_unchanged=True, extra_rom_bytes=0, extra_ram_bytes=0,
                               reason='Physical XY test: residual downward drift at 3/8, stronger with segmented feed')
    (out / 'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (out / 'symbols.json').write_text(json.dumps(symbols, indent=2) + '\n')
    (ROOT / 'studio/internal/profiles/basic-0.4.92-symbols.json').write_text(json.dumps(symbols, indent=2) + '\n')
    print(json.dumps(dict(version=VERSION, sha256=manifest['sha256'],
                          changed_addresses=changed, free_rom=manifest['explicit_free_bytes'])))


if __name__ == '__main__':
    main()
