"""Prepare a 31x16 paper glyph from BASIC-style lists or matrices (PC tool).

This is not a BASIC interpreter extension. &H and &B are the proposed public
notation; bit15 is the top paper row. Native Canon words have a different order.
"""
import argparse
from pathlib import Path
import re

from pattern_codec import SCAN_ROW_BITS, encode_columns

WIDTH, HEIGHT = 31, 16


def parse_unsigned(token, bits):
    token = token.strip()
    if re.fullmatch(r"&[hH][0-9a-fA-F]+", token):
        value = int(token[2:], 16)
    elif re.fullmatch(r"&[bB][01]+", token):
        value = int(token[2:], 2)
    elif re.fullmatch(r"[0-9]+", token):
        value = int(token, 10)
    else:
        raise ValueError(f"Expected unsigned decimal, &H hex or &B binary: {token!r}")
    if value >= 1 << bits:
        raise ValueError(f"Value exceeds {bits} bits: {token!r}")
    return value


def parse_word(token):
    return parse_unsigned(token, 16)


def parse_values(text, bits):
    """Read a flat list or rectangular matrix; never eval source text.

    Unbracketed files retain the original whitespace/comma-separated format.
    Bracketed lists require commas, reject missing elements and rank > 2.
    """
    text = "\n".join(line.split("#", 1)[0] for line in text.splitlines()).strip()
    if not text.startswith("["):
        return [parse_unsigned(s, bits) for s in re.split(r"[\s,]+", text) if s]
    tokens = re.findall(r"\[|\]|,|[^\s\[\],]+", text)
    pos = 0

    def array(depth):
        nonlocal pos
        if depth > 2 or pos >= len(tokens) or tokens[pos] != "[":
            raise ValueError("Expected a list or a two-dimensional matrix")
        pos += 1
        result = []
        if pos < len(tokens) and tokens[pos] == "]":
            pos += 1
            return result
        while pos < len(tokens):
            if tokens[pos] == "[":
                result.append(array(depth + 1))
            else:
                result.append(parse_unsigned(tokens[pos], bits))
                pos += 1
            if pos < len(tokens) and tokens[pos] == "]":
                pos += 1
                return result
            if pos >= len(tokens) or tokens[pos] != ",":
                raise ValueError("Expected a comma or closing bracket")
            pos += 1
        raise ValueError("Unclosed list")

    result = array(1)
    if pos != len(tokens):
        raise ValueError("Unexpected text after list")
    nested = [isinstance(value, list) for value in result]
    if any(nested) and not all(nested):
        raise ValueError("Cannot mix scalar values and rows")
    if any(nested) and len({len(row) for row in result}) != 1:
        raise ValueError("Matrix must be rectangular")
    return result


def parse_columns(text):
    # Comments and whitespace are a PC import convenience, not BASIC grammar.
    columns = parse_values(text, 16)
    if len(columns) != WIDTH or any(type(v) is not int for v in columns):
        raise ValueError(f"Expected a flat list of exactly {WIDTH} columns")
    return columns


def rows_to_columns(rows):
    """Sixteen unsigned 31-bit rows; bit30 is the leftmost point."""
    if len(rows) != HEIGHT or any(type(v) is not int or not 0 <= v < 1 << WIDTH for v in rows):
        raise ValueError("Expected 16 rows in range 0..2147483647")
    return [sum(1 << (15-y) for y, row in enumerate(rows) if row & (1 << (30-x)))
            for x in range(WIDTH)]


def pixels_to_columns(pixels):
    """Sixteen rows of 31 individual pixels, indexed [y][x]."""
    if (len(pixels) != HEIGHT or
            any(not isinstance(row, (list, tuple)) or len(row) != WIDTH or
                any(type(v) is not int or v not in (0, 1) for v in row) for row in pixels)):
        raise ValueError("Expected a 16x31 matrix containing only 0 and 1")
    return [sum(pixels[y][x] << (15-y) for y in range(HEIGHT)) for x in range(WIDTH)]


def compile_definition(text, layout="columns"):
    if layout == "columns":
        columns = parse_columns(text)
    elif layout == "rows":
        columns = rows_to_columns(parse_values(text, 31))
    elif layout == "pixels":
        columns = pixels_to_columns(parse_values(text, 1))
    else:
        raise ValueError("Unknown layout")
    return pack_columns(columns)


def pack_columns(columns):
    if len(columns) != WIDTH:
        raise ValueError("Expected exactly 31 columns")
    native = []
    for word in columns:
        if type(word) is not int or not 0 <= word <= 65535:
            raise ValueError("Column must be an unsigned 16-bit integer")
        native.append(sum(1 << bit for y, bit in enumerate(SCAN_ROW_BITS)
                          if word & (1 << (15 - y))))
    return encode_columns(native, 0, 32)  # Column 31 is always a blank guard.


def unpack_columns(data):
    if len(data) != 64 or data[-2:] != b"\0\0":
        raise ValueError("Expected 64 bytes ending with a blank guard word")
    return [sum(1 << (15 - y) for y, bit in enumerate(SCAN_ROW_BITS)
                if int.from_bytes(data[x * 2:x * 2 + 2], "big") & (1 << bit))
            for x in range(WIDTH)]


def preview(columns):
    return "\n".join("".join("#" if word & (1 << (15-y)) else "."
                              for word in columns) for y in range(HEIGHT)) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--layout", choices=("columns", "rows", "pixels"), default="columns")
    args = parser.parse_args()
    data = compile_definition(args.source.read_text(encoding="utf-8-sig"), args.layout)
    columns = unpack_columns(data)  # Validate everything before writing output.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(preview(columns), end="")
    print(f"Wrote {len(data)} bytes (31 columns + blank guard): {args.output}")


if __name__ == "__main__":
    main()
