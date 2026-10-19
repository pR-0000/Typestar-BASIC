"""Build .89 from .88: rebind GLYPH's row-mask table after relocation.

The incremental builds retained one old immediate address in SGRENDER.
Use the final symbol map and verify the table's contents before rebinding it.
No mechanical, heating, UART, RAM, token or font changes. No flashing.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
VERSION = '0.4.89-dev'
BASE_SHA = 'c6c4a5b26e1b61fa6ff05936c30e8f220a0dce0fbd95d861f4965204d066647e'


def main():
    base = ROOT / 'release/s70-basic-0.4.88-dev-canon-start-nh7.bin'
    raw = base.read_bytes()
    assert len(raw) == 32768
    old = raw[16384:] + raw[:16384]
    assert hashlib.sha256(old).hexdigest() == BASE_SHA
    symbols = json.loads((ROOT / 'studio/internal/profiles/basic-0.4.88-symbols.json').read_text())
    manifest = json.loads(base.with_name(base.stem + '-manifest.json').read_text())
    # This ordering is the hardware-validated top-to-bottom row permutation.
    rows = (12, 13, 14, 15, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
    masks = b''.join((1 << row).to_bytes(2, 'big') for row in rows)
    target = symbols['PBMASKS']
    assert old[target - 0x4000:target - 0x4000 + 32] == masks
    start, end = symbols['SGRENDER'], symbols['SGRENDEREND']
    region = old[start - 0x4000:end - 0x4000]
    needle = bytes.fromhex('ce40f8')
    assert region.count(needle) == 1
    address = start + region.index(needle)
    assert address == 0x804A
    cpu = bytearray(old)
    cpu[address - 0x4000 + 1:address - 0x4000 + 3] = target.to_bytes(2, 'big')
    previous = b'Typestar BASIC 0.4.88-dev'
    assert old.count(previous) == 1
    banner_address = old.index(previous) + 0x4000
    cpu = cpu.replace(previous, b'Typestar BASIC ' + VERSION.encode('ascii'))
    allowed = {address + 1, address + 2, banner_address + previous.index(b'88-dev') + 1}
    changed = [i + 0x4000 for i, (a, b) in enumerate(zip(old, cpu)) if a != b]
    assert set(changed) == allowed, changed
    digest = hashlib.sha256(cpu).hexdigest()
    manifest.update(version=VERSION, sha256=digest,
                    status='GLYPH mask reference corrected; CPU and physical validation pending',
                    base_cpu_sha256=BASE_SHA,
                    glyph_mask_fix=dict(instruction_address=address,
                                        old_target=0x40F8, new_target=target,
                                        changed_cpu_addresses=changed,
                                        source='src/paper-glyph-render.asm: LDX #PBMASKS'))
    # The release manifest previously contained the .88 socket hash.
    manifest.pop('nh7_sha256', None)
    out = ROOT / 'build/glyph-mask'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (out / 'symbols.json').write_text(json.dumps(symbols, indent=2) + '\n')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (ROOT / 'studio/internal/profiles/basic-0.4.89-symbols.json').write_text(json.dumps(symbols, indent=2) + '\n')
    print(json.dumps(dict(version=VERSION, cpu_sha256=digest,
                          instruction=hex(address), target=hex(target),
                          changed_bytes=len(changed), free_rom=manifest['explicit_free_bytes'])))


if __name__ == '__main__':
    main()
