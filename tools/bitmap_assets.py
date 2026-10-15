"""Compact source sprites, exact integer zoom and LCD row conversion (PC).

No peripheral is driven. Paper tiles have logical positions; their physical
placement and completion protocol are still to be integrated into BASIC.
"""
import argparse
import json
from pathlib import Path

from glyph_definition import parse_values, pixels_to_columns, pack_columns


def read_bitmap(text, width, height, layout="rows"):
    if type(width) is not int or type(height) is not int or not (1 <= width <= 31 and 1 <= height <= 16):
        raise ValueError("Source dimensions must be 1..31 by 1..16")
    values = parse_values(text, width if layout == "rows" else 1)
    if layout == "rows":
        if len(values) != height or any(type(v) is not int for v in values):
            raise ValueError("Wrong number of source rows")
        return [[(row >> (width-1-x)) & 1 for x in range(width)] for row in values]
    if layout == "pixels":
        if (len(values) != height or any(not isinstance(row, list) or len(row) != width
                or any(type(v) is not int or v not in (0, 1) for v in row) for row in values)):
            raise ValueError("Pixel matrix does not match declared dimensions")
        return values
    raise ValueError("Unknown bitmap layout")


def validate_pixels(pixels):
    if (not pixels or not isinstance(pixels[0], (list, tuple)) or not pixels[0]
            or any(not isinstance(row, (list, tuple)) or len(row) != len(pixels[0])
                   or any(type(v) is not int or v not in (0, 1) for v in row) for row in pixels)):
        raise ValueError("Expected a nonempty rectangular 0/1 matrix")


def pack_source(pixels):
    """Pack each row in ceil(width/8) bytes, unused HIGH bits zero."""
    validate_pixels(pixels)
    width = len(pixels[0])
    stride = (width + 7) // 8
    return b"".join(sum(v << (width-1-x) for x, v in enumerate(row)).to_bytes(stride, "big")
                    for row in pixels)


def zoom_pixels(pixels, factor):
    validate_pixels(pixels)
    if type(factor) is not int or factor not in (1, 2):
        raise ValueError("Supported zoom factors are 1 and 2")
    return [[v for v in row for _ in range(factor)]
            for row in pixels for _ in range(factor)]


def paper_tiles(pixels, factor=1):
    """Exact zoom, then tile into 31x16 native buffers. Never clip an edge.

    x/y are uncalibrated logical dot coordinates, NOT Canon movement units.
    Padding in the final tile is not part of the requested sprite extent.
    """
    enlarged = zoom_pixels(pixels, factor)
    height, width = len(enlarged), len(enlarged[0])
    tiles = []
    for top in range(0, height, 16):
        for left in range(0, width, 31):
            used_w, used_h = min(31, width-left), min(16, height-top)
            tile = [[0] * 31 for _ in range(16)]
            for y in range(used_h):
                tile[y][:used_w] = enlarged[top+y][left:left+used_w]
            tiles.append({"x": left, "y": top, "width": used_w, "height": used_h,
                          "data": pack_columns(pixels_to_columns(tile))})
    return tiles


def lcd_rows(pixels):
    """Canonical eight CGRAM row bytes, bit4 left. Seven rows pad with zero."""
    validate_pixels(pixels)
    if len(pixels[0]) != 5 or len(pixels) not in (7, 8):
        raise ValueError("LCD bitmap must be 5x7 or 5x8")
    return pack_source(pixels) + bytes(8-len(pixels))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--layout", choices=("rows", "pixels"), default="rows")
    parser.add_argument("--target", choices=("paper", "lcd"), default="paper")
    parser.add_argument("--zoom", type=int, choices=(1, 2), default=1)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    pixels = read_bitmap(args.source.read_text(encoding="utf-8-sig"), args.width, args.height, args.layout)
    source = pack_source(pixels)
    # Validate target and complete all conversions before creating files.
    if args.target == "lcd":
        if args.zoom != 1:
            parser.error("LCD character import has no zoom option")
        converted = lcd_rows(pixels)
        files = {"lcd-cgram.bin": converted}
        metadata = {"target": "lcd", "width": 5, "height": 8,
                    "source_height": args.height, "limits": "Row data only; no slot allocation or hardware upload."}
    else:
        tiles = paper_tiles(pixels, args.zoom)
        files = {f"tile-{i}.bin": tile["data"] for i, tile in enumerate(tiles)}
        metadata = {"target": "paper", "width": args.width * args.zoom,
                    "height": args.height * args.zoom, "zoom": args.zoom,
                    "tiles": [{k: v for k, v in tile.items() if k != "data"} for tile in tiles],
                    "limits": "Logical positions only; physical tile placement is not implemented. Expanded files are PC artifacts, not persistent target-RAM requirements."}
    metadata["source_bytes"] = len(source)
    files["source.bin"] = source
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (args.output_dir / name).write_bytes(data)
    (args.output_dir / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
