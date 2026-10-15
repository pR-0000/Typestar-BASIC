"""Assemble and execute the checked HD6301 array-address module; no flash ROM."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib
import itertools
import json
import random
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
READER = ROOT.parents[1] / "ROMReader"
OUT = ROOT / "build/array-index"
OUT.mkdir(parents=True, exist_ok=True)
result = subprocess.run([str(READER / "tmp/m680x-tools/a09.exe"), "-W",
                         "-Bbuild/array-index/module.bin", "-Lbuild/array-index/module.lst",
                         "src/array-index.asm"], cwd=ROOT, capture_output=True, text=True)
listing = (OUT / "module.lst").read_text()
assert result.returncode == 0 and re.search(r"\b0 error\(s\)", listing), listing
binary = (OUT / "module.bin").read_bytes()
sys.path.insert(0, str(READER / "tools"))
from trace_s70_keyboard import KeyboardMachine


class ArrayMachine(KeyboardMachine):
    def write(self, address, value):
        assert 0x110C <= address < 0x1115 or 0x1F00 <= address < 0x2000, hex(address)
        super().write(address, value)


def check(rank, size, n0, n1, base, i0, i1, irq=True):
    mem = bytearray(65536)
    mem[0x6000:0x6000 + len(binary)] = binary
    fields = (n0, n1, base, i0, i1, 0xBEEF)
    job = bytes([rank, size]) + b"".join(v.to_bytes(2, "big") for v in fields)
    mem[0x1100:0x110E] = job
    m = ArrayMachine(mem)
    m.i = irq
    span = n0 * n1 * size
    valid = (rank in (1, 2) and size in (1, 2, 4, 5) and n0 > 0 and n1 > 0
             and (rank != 1 or (n1 == 1 and i1 == 0)) and i0 < n0 and i1 < n1
             and span <= 65535 and base + span <= 65536)
    expected = base + (i0 * n1 + i1) * size if valid else 0xBEEF
    m.call(0x6000, x=0x1100, budget=3000)
    assert m.c == (not valid), (rank, size, n0, n1, base, i0, i1, m.c)
    assert int.from_bytes(m.m[0x110C:0x110E], "big") == expected
    assert m.m[0x1100:0x110C] == job[:12] and m.x == 0x1100 and m.i == irq
    return valid


cases = []
for size in (1, 2, 4, 5):
    cases += [(2, size, 16, 31, 0x1200, y, x) for y in range(16) for x in range(31)]
    cases += [(1, size, 16, 1, 0x1200, y, 0) for y in range(16)]
cases += [(rank, size, n0, n1, base, i0, i1)
          for rank, size, n0, n1, base, i0, i1 in (
              (0, 1, 1, 1, 0, 0, 0), (3, 1, 1, 1, 0, 0, 0),
              (1, 3, 1, 1, 0, 0, 0), (1, 0, 1, 1, 0, 0, 0),
              (1, 1, 0, 1, 0, 0, 0), (2, 1, 1, 0, 0, 0, 0),
              (1, 1, 16, 2, 0, 0, 0), (1, 1, 16, 1, 0, 0, 1),
              (2, 1, 16, 31, 0, 16, 0), (2, 1, 16, 31, 0, 0, 31),
              (2, 1, 256, 256, 0, 0, 0), (2, 1, 65535, 65535, 0, 0, 0),
              (1, 2, 32768, 1, 0, 0, 0), (1, 4, 16384, 1, 0, 0, 0),
              (1, 1, 2, 1, 65535, 0, 0), (1, 4, 1, 1, 65533, 0, 0),
              (1, 1, 1, 1, 65535, 0, 0), (1, 4, 1, 1, 65532, 0, 0),
              (1, 1, 65535, 1, 1, 65534, 0), (2, 1, 255, 257, 1, 254, 256))]
rng = random.Random(7016)
cases += [(1,5,n,1,base,i,0) for n,base,i in (
    (13107,0,13106),(13108,0,0),(1,65531,0),(1,65532,0),
    (16,0x1200,15),(16,0x1200,16))]
for _ in range(256):
    n0, n1 = rng.randrange(1, 400), rng.randrange(1, 400)
    cases.append((2, rng.choice((1, 2, 4, 5)), n0, n1, rng.randrange(65536),
                  rng.randrange(n0 + 1), rng.randrange(n1 + 1)))
valid_count = sum(check(*case) for case in cases)
for irq in (False, True):
    check(2, 4, 16, 31, 0x1200, 15, 30, irq=irq)
    check(2, 4, 16, 31, 0x1200, 16, 30, irq=irq)
report = {"result": "PASS", "module_bytes": len(binary), "cases": len(cases) + 4,
          "valid_main_cases": valid_count, "invalid_main_cases": len(cases) - valid_count,
          "sha256": hashlib.sha256(binary).hexdigest(),
          "limits": "Standalone module at test origin6000; no allocator, BASIC DIM/parser integration, arena ownership or real IRQ simulation."}
(OUT / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(f"PASS {len(binary)}-byte HD6301 module; {len(cases) + 4} checked 1D/2D address cases")
