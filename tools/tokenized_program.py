"""Reference codec for the NEXT RAM format, not accepted by released firmware.

Record: total length:u8, line:u16 big endian, token bytes (no terminator).
One zero length terminates the sorted arena. Text transport stays ASCII.
Token ids are persisted ABI: append to basic_tokens.json, never reorder.
The retired HELP slot $8A is reassigned to LLIST from .88; other ids are stable.
"""
import argparse
import json
import re
from pathlib import Path

SPEC = json.loads(Path(__file__).with_name('basic_tokens.json').read_text())
WORDS = SPEC['keywords']
ENCODE = {word: SPEC['first_token'] + i for i, word in enumerate(WORDS)}
DECODE = {value: key for key, value in ENCODE.items()}
CAPACITY = 5952
MAX_SOURCE = 63
IDENT = re.compile(r'[A-Za-z][A-Za-z0-9$]*')


def tokenize(source):
    source.encode('ascii')
    if len(source) > MAX_SOURCE or any(not 32 <= ord(c) <= 126 for c in source):
        raise ValueError('Source must contain at most 63 printable ASCII bytes')
    out = bytearray()
    pos = 0
    while pos < len(source):
        if source[pos] == '"':
            end = source.find('"', pos + 1)
            end = len(source) if end < 0 else end + 1
            out.extend(source[pos:end].encode('ascii'))
            pos = end
            continue
        match = IDENT.match(source, pos)
        if match:
            word = match.group()
            token = ENCODE.get(word.upper())
            out.extend(bytes([token]) if token else word.encode('ascii'))
            pos = match.end()
            if word.upper() == 'REM':
                out.extend(source[pos:].encode('ascii'))
                break
        else:
            out.append(ord(source[pos]))
            pos += 1
    return bytes(out)


def detokenize(payload):
    parts = []
    for byte in payload:
        if byte in DECODE:
            parts.append(DECODE[byte])
        elif 32 <= byte <= 126:
            parts.append(chr(byte))
        else:
            raise ValueError('Invalid token or source byte')
    source = ''.join(parts)
    if len(source) > MAX_SOURCE or tokenize(source) != payload:
        raise ValueError('Noncanonical token stream or expanded line too long')
    return source


def pack(lines, capacity=CAPACITY):
    """Validate everything before constructing an arena; reject duplicate lines."""
    records = {}
    for number, source in lines:
        if not 1 <= number <= 65535 or number in records:
            raise ValueError('Line numbers must be unique, in 1..65535')
        if not source.strip():
            raise ValueError('Empty statement is an edit/delete, not a stored record')
        payload = tokenize(source)
        records[number] = bytes([len(payload) + 3]) + number.to_bytes(2, 'big') + payload
    arena = b''.join(records[n] for n in sorted(records)) + b'\0'
    if len(arena) > capacity:
        raise ValueError('Program RAM full')
    return arena


def unpack(arena):
    pos = 0
    previous = 0
    lines = []
    while pos < len(arena):
        length = arena[pos]
        if length == 0:
            if pos != len(arena) - 1:
                raise ValueError('Bytes after sentinel')
            return lines
        if not 4 <= length <= MAX_SOURCE + 3 or pos + length >= len(arena):
            raise ValueError('Truncated or invalid record length')
        number = int.from_bytes(arena[pos+1:pos+3], 'big')
        if number <= previous:
            raise ValueError('Unsorted or duplicate line number')
        source = detokenize(arena[pos+3:pos+length])
        if not source.strip():
            raise ValueError('Empty stored statement')
        lines.append((number, source))
        previous = number
        pos += length
    raise ValueError('Missing sentinel')


def edit(arena, number, source, capacity=CAPACITY):
    """Reference atomic insert/replace/delete: original bytes are never mutated."""
    if not 1 <= number <= 65535:
        raise ValueError('Line number out of range')
    lines = dict(unpack(arena))
    if source.strip():
        lines[number] = source
    else:
        lines.pop(number, None)
    return pack(lines.items(), capacity)


def read_source(text):
    lines = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        match = re.fullmatch(r'\s*([0-9]+)\s+(.*)', raw)
        if not match:
            raise ValueError('Expected line number and statement')
        lines.append((int(match[1]), match[2]))
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, help='Offline RAM arena, NEVER a flash image')
    args = parser.parse_args()
    lines = read_source(args.source.read_text(encoding='utf-8-sig'))
    arena = pack(lines)
    old_size = 1 + sum(2 + len(source) for _, source in lines)
    print(json.dumps(dict(status='offline format candidate', lines=len(lines),
                          source_record_bytes=old_size, token_record_bytes=len(arena),
                          saved_bytes=old_size-len(arena), free_bytes=CAPACITY-len(arena)), indent=2))
    if args.output:
        args.output.write_bytes(arena)


if __name__ == '__main__':
    main()
