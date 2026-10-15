"""Build/execute dynamic array creation in a synthetic private RAM arena."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
READER = ROOT.parents[1] / "ROMReader"
OUT = ROOT / "build/array-create"
OUT.mkdir(parents=True, exist_ok=True)
result = subprocess.run([str(READER / "tmp/m680x-tools/a09.exe"), "-W",
                         "-Bbuild/array-create/module.bin", "-Lbuild/array-create/module.lst",
                         "src/array-create.asm"], cwd=ROOT, capture_output=True, text=True)
listing = (OUT / "module.lst").read_text()
assert result.returncode == 0 and re.search(r"\b0 error\(s\)", listing), listing
symbols = {name: int(value, 16) for name, value in re.findall(r"\b(ARRAY_\w+)\s+02\s+([0-9A-F]{4})", listing)}
binary = (OUT / "module.bin").read_bytes()
sys.path.insert(0, str(READER / "tools"))
from trace_s70_keyboard import KeyboardMachine

JOB = 0x1000


class ArenaMachine(KeyboardMachine):
    def __init__(self):
        mem = bytearray([0xA5] * 65536)
        mem[0x6000:0x6000+len(binary)] = binary
        super().__init__(mem)
        self.arena = (0x1200, 0x1E00)
        self.low_sp = self.sp

    def write(self, address, value):
        assert (JOB+6 <= address <= JOB+22 or JOB+25 <= address <= JOB+28
                or self.arena[0] <= address < self.arena[1]
                or 0x1F00 <= address < 0x2000), hex(address)
        super().write(address, value)

    def step(self):
        self.low_sp = min(self.low_sp, self.sp)
        super().step()


def word(m, offset):
    return int.from_bytes(m.m[JOB+offset:JOB+offset+2], "big")


def setup(m, rank, size, n0, n1, cursor, limit):
    m.m[JOB:JOB+29] = bytes([0xA5] * 29)
    m.m[JOB:JOB+6] = bytes([rank, size]) + n0.to_bytes(2, "big") + n1.to_bytes(2, "big")
    for offset, value in ((21, cursor), (23, limit), (25, 0xBEEF)):
        m.m[JOB+offset:JOB+offset+2] = value.to_bytes(2, "big")


def allocate(m, rank, size, n0, n1, cursor, limit):
    setup(m, rank, size, n0, n1, cursor, limit)
    inputs = bytes(m.m[JOB:JOB+6])
    before = bytes(m.m[m.arena[0]:m.arena[1]])
    irq = m.i
    span = n0*n1*size
    valid = (rank in (1, 2) and size in (1, 2, 4, 5) and n0 > 0 and n1 > 0
             and (rank != 1 or n1 == 1) and 0 < span <= 65535
             and cursor < limit and cursor+8+span <= limit <= 65535)
    m.call(symbols["ARRAY_CREATE"], x=JOB, budget=20000)
    assert m.c == (not valid), (rank, size, n0, n1, cursor, limit)
    assert m.x == JOB and m.i == irq and m.m[JOB:JOB+6] == inputs
    assert word(m, 23) == limit
    expected_arena = bytearray(before)
    if valid:
        descriptor = inputs + span.to_bytes(2, "big")
        begin = cursor-m.arena[0]
        expected_arena[begin:begin+8+span] = descriptor + bytes(span)
        assert word(m, 21) == cursor+8+span and word(m, 25) == cursor
    else:
        assert word(m, 21) == cursor and word(m, 25) == 0xBEEF
    assert m.m[m.arena[0]:m.arena[1]] == expected_arena
    return valid


cases = []
for rank, n0, n1 in ((1, 1, 1), (1, 8, 1), (1, 16, 1), (2, 7, 5), (2, 16, 31)):
    for size in (1, 2, 4, 5):
        for spare in (-1, 0, 1, 8):
            cases.append((rank, size, n0, n1, 0x1200, 0x1200+8+n0*n1*size+spare))
cases += [(0, 1, 1, 1, 0x1200, 0x1800), (3, 1, 1, 1, 0x1200, 0x1800),
          (1, 0, 1, 1, 0x1200, 0x1800), (1, 3, 1, 1, 0x1200, 0x1800),
          (1, 1, 0, 1, 0x1200, 0x1800), (2, 1, 1, 0, 0x1200, 0x1800),
          (1, 1, 2, 2, 0x1200, 0x1800), (2, 1, 256, 256, 0x1200, 0x1800),
          (1, 4, 16384, 1, 0x1200, 0x1800), (2, 4, 65535, 65535, 0x1200, 0x1800),
          (1, 1, 1, 1, 0x1200, 0x1200), (1, 1, 1, 1, 0x1201, 0x1200),
          (1, 1, 1, 1, 0xFFF8, 0xFFFF), (1, 1, 8, 1, 0xFFF0, 0xFFFF)]
success = 0
max_stack = 0
for irq in (False, True):
    for case in cases:
        m = ArenaMachine()
        m.i = irq
        success += allocate(m, *case)
        max_stack = max(max_stack, 0x1FFF-m.low_sp)

# Consecutive real allocations: compact sprite, LCD source and a pixel matrix.
# Preserve a nonzero marker in the first payload while subsequent arrays grow.
m = ArenaMachine()
cursor, limit = 0x1200, 0x1200 + 24 + 16 + 504
allocations = []
for rank, size, n0, n1 in ((1, 2, 8, 1), (1, 1, 8, 1), (2, 1, 16, 31)):
    assert allocate(m, rank, size, n0, n1, cursor, limit)
    allocations.append({"descriptor": cursor, "data": cursor+8, "payload": n0*n1*size})
    m.m[cursor+8] = 0x5A
    cursor = word(m, 21)
assert cursor == limit
assert not allocate(m, 1, 1, 1, 1, cursor, limit)
assert all(m.m[a["data"]] == 0x5A for a in allocations)

# Bind the allocated matrix to the checked access routine, then address its
# bottom-right pixel. The allocator's descriptor feeds the existing ABI.
last = allocations[-1]
descriptor = bytes(m.m[last["descriptor"]:last["descriptor"]+8])
m.m[JOB:JOB+6] = descriptor[:6]
m.m[JOB+6:JOB+12] = last["data"].to_bytes(2,"big") + bytes.fromhex("00 0F 00 1E")
m.call(symbols["ARRAY_ELEMENT"], x=JOB)
assert not m.c and word(m, 12) == limit-1
report = {"result": "PASS", "total_module_bytes": len(binary),
          "allocator_bytes": symbols["ARRAY_CREATE_END"]-symbols["ARRAY_CREATE"],
          "case_count": len(cases)*2+5, "success_shape_cases": success,
          "max_observed_call_stack_bytes": max_stack,
          "allocations": allocations, "sequence_bytes": limit-0x1200,
          "sha256": hashlib.sha256(binary).hexdigest(),
          "limits": "Synthetic arena only; no Canon coexistence, parser/DIM, per-object free, garbage collection or asynchronous allocation. Stack figure excludes IRQ/SWI frames."}
(OUT / "validation.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
print(f"PASS {len(binary)} bytes combined, {report['allocator_bytes']} allocator bytes; {report['case_count']} cases, sequence {limit-0x1200} bytes")
