"""Build/test native rectangle rasterizer; does not generate a flash ROM."""

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
OUT = ROOT / "build/graphics-shapes"
OUT.mkdir(parents=True, exist_ok=True)
r = subprocess.run([str(READER / "tmp/m680x-tools/a09.exe"), "-W",
                    "-Bbuild/graphics-shapes/module.bin", "-Lbuild/graphics-shapes/module.lst",
                    "src/graphics-shapes.asm"], cwd=ROOT, capture_output=True, text=True)
listing = (OUT / "module.lst").read_text()
assert r.returncode == 0 and re.search(r"\b0 error\(s\)", listing), listing
symbols = {name: int(value, 16) for name, value in re.findall(r"\b(GFX_\w+)\s+02\s+([0-9A-F]{4})", listing)}
binary = (OUT / "module.bin").read_bytes()
sys.path.insert(0, str(READER / "tools"))
from trace_s70_keyboard import KeyboardMachine
from trace_s70_glyph_extent import trace

MASKS = (0x1000, 0x2000, 0x4000, 0x8000, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048)


class ShapeMachine(KeyboardMachine):
    def write(self, address, value):
        assert (0x1000 <= address < 0x1040 or 0x1108 <= address < 0x110A
                or 0x1F00 <= address < 0x2000), hex(address)
        super().write(address, value)


def check(box, thickness, fill, irq):
    mem = bytearray(65536)
    mem[0x6000:0x6000+len(binary)] = binary
    # Existing pixels must survive: rectangles are additive, not clearing.
    mem[0x1000:0x103E] = bytes([0x10, 0]) * 31
    job = bytes.fromhex("10 00") + bytes(box) + bytes([thickness, fill])
    mem[0x1100:0x1108] = job
    m = ShapeMachine(mem)
    m.i = irq
    x0, y0, x1, y1 = box
    valid = 0 <= x0 <= x1 <= 30 and 0 <= y0 <= y1 <= 15 and 1 <= thickness <= 16 and fill in (0, 1)
    expected = bytearray(mem[0x1000:0x1040])
    if valid:
        for x in range(x0, x1+1):
            for y in range(y0, y1+1):
                interior = x0+thickness <= x <= x1-thickness and y0+thickness <= y <= y1-thickness
                if fill or not interior:
                    word = int.from_bytes(expected[2*x:2*x+2], "big") | MASKS[y]
                    expected[2*x:2*x+2] = word.to_bytes(2, "big")
    m.call(symbols["GFX_RECT"], x=0x1100, budget=40000)
    assert m.c == (not valid) and m.x == 0x1100 and m.i == irq
    assert m.m[0x1100:0x1108] == job
    assert m.m[0x1000:0x1040] == expected, (box, thickness, fill)
    if not valid:
        assert m.m[0x1108:0x110A] == b"\0\0"
    return bytes(expected)


count = 0
for irq in (False, True):
    for box in ((0,0,30,15), (2,3,10,8), (15,7,15,7), (0,0,0,15),
                (0,0,30,0), (0,15,30,15), (30,0,30,15), (4,4,12,12)):
        for thickness in (1, 2, 4, 16):
            for fill in (0, 1):
                check(box, thickness, fill, irq)
                count += 1
invalid = [(box, t, f) for box, t, f in (
    ((0,0,31,15),1,0), ((0,0,30,16),1,0), ((255,0,30,15),1,0),
    ((0,255,30,15),1,0), ((10,0,9,15),1,0), ((0,9,30,8),1,0),
    ((0,0,30,15),0,0), ((0,0,30,15),17,0), ((0,0,30,15),1,2))]
for box,t,f in invalid:
    check(box,t,f,True)
    count += 1
payload = check((2,2,28,13),2,0,True)
count += 1
(OUT / "outlined-rectangle.bin").write_bytes(payload)
extent = trace(READER / "dumps/256ROM_NH7_1181.bin", ram_patterns={"R": payload}, characters="R")
for i, unit in enumerate(extent["glyphs"][0]["units"]):
    a,b = payload[2*i:2*i+2]
    assert unit["lanes"] == [a & 240,b,a & 15]
report = {"result": "PASS", "module_bytes": len(binary),
          "rectangle_bytes": symbols["GFX_SHAPES_END"]-symbols["GFX_RECT"],
          "cases": count, "sha256": hashlib.sha256(binary).hexdigest(),
          "native_decoder": extent,
          "limits": "Raw non-square 31x16 grid; no motor output, calibrated stroke width, multi-tile clipping or BASIC command integration."}
(OUT / "validation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(f"PASS {count} rectangle cases; {report['rectangle_bytes']} new bytes, {len(binary)} combined; 31 native decoder columns")
