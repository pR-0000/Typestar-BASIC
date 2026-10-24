"""Build the HD6301 opcode table once, rather than decode it at every step.

The templates below describe CPU instructions only. They contain no ROM
addresses or firmware shortcuts. Generated handlers still use the machine's
read/write methods, so peripheral access, interrupts and RAM code remain live.
Only these fixed internal templates are compiled; ROM bytes are never Python
source. The reference interpreter remains in hd6301.py for comparison.
"""


def _handler(opcode, body):
    name = f'op_{opcode:02x}'
    source = f'def {name}(c):\n' + '\n'.join('    ' + line for line in body.splitlines())
    namespace = {}
    exec(compile(source, __file__, 'exec'), namespace)
    return namespace[name]


def _address(mode, wide=False):
    if mode == 0:
        return f'address = c.pc\nc.pc += {2 if wide else 1}\n'
    return ('address = c.fetch()\n' if mode == 1 else
            'address = (c.x + c.fetch()) & 65535\n' if mode == 2 else
            'address = c.fetchword()\n')


def build_dispatch():
    table = [None] * 256
    for op in range(256):
        table[op] = _handler(op, f"raise AssertionError('unsupported opcode ${op:02X} at $' + f'{{c.pc-1:04X}}')")

    # Inherent instructions. PC already points past the opcode.
    inherent = {
        0x01: 'pass',
        0x04: 'c.c = bool(c.d & 1)\nc.d >>= 1\nc.n = False\nc.z = c.d == 0\nc.v = c.c',
        0x05: 'c.d = c.add(c.d, c.d, 16)',
        0x06: 'c.c,c.v,c.z,c.n,c.i = [bool(c.a & bit) for bit in (1,2,4,8,16)]',
        0x07: 'c.a = 0xc0 | int(c.c) | (int(c.v)<<1) | (int(c.z)<<2) | (int(c.n)<<3) | (int(c.i)<<4)',
        0x08: 'c.x = (c.x + 1) & 65535\nc.z = c.x == 0',
        0x09: 'c.x = (c.x - 1) & 65535\nc.z = c.x == 0',
        0x0a: 'c.v = False',
        0x0b: 'c.v = True',
        0x0c: 'c.c = 0',
        0x0d: 'c.c = 1',
        0x0e: 'c.i = False',
        0x0f: 'c.i = 1',
        0x10: 'c.a = c.sub(c.a, c.b)',
        0x11: 'c.sub(c.a, c.b)',
        0x16: 'c.b = c.nz(c.a)',
        0x17: 'c.a = c.nz(c.b)',
        0x18: 'c.d,c.x = c.x,c.d',
        0x1b: 'c.a = c.add(c.a, c.b)',
        0x30: 'c.x = (c.sp + 1) & 65535',
        0x31: 'c.sp = (c.sp + 1) & 65535',
        0x32: 'c.a = c.pop()',
        0x33: 'c.b = c.pop()',
        0x34: 'c.sp = (c.sp - 1) & 65535',
        0x35: 'c.sp = (c.x - 1) & 65535',
        0x36: 'c.push(c.a)',
        0x37: 'c.push(c.b)',
        0x38: 'c.x = c.pop() * 256 + c.pop()',
        0x39: 'c.pc = c.pop() * 256 + c.pop()',
        0x3a: 'c.x = (c.x + c.b) & 65535',
        0x3b: ('c.frames.append(bytes(c.m[c.sp+1:c.sp+8]))\n'
               'cc = c.pop()\nc.b = c.pop()\nc.a = c.pop()\n'
               'c.x = c.pop() * 256 + c.pop()\nc.pc = c.pop() * 256 + c.pop()\n'
               'c.c,c.v,c.z,c.n,c.i = [bool(cc & bit) for bit in (1,2,4,8,16)]'),
        0x3c: 'c.push(c.x & 255)\nc.push(c.x >> 8)',
        0x3d: 'c.d = c.a * c.b\nc.c = bool(c.b & 128)',
        0x3f: ('cc = 0xc0 | int(c.c) | (int(c.v)<<1) | (int(c.z)<<2) | (int(c.n)<<3) | (int(c.i)<<4)\n'
               'for value in (c.pc & 255,c.pc >> 8,c.x & 255,c.x >> 8,c.a,c.b,cc):\n'
               '    c.push(value)\nc.i = True\nc.pc = c.word(0xfffa)'),
        0x8d: ('offset = c.fetch()\nc.push(c.pc & 255)\nc.push(c.pc >> 8)\n'
               'c.pc = (c.pc + (offset if offset < 128 else offset - 256)) & 65535'),
    }

    # Each branch evaluates its own condition, rather than building all sixteen.
    conditions = ('True', 'False', 'not (c.c or c.z)', 'c.c or c.z',
                  'not c.c', 'c.c', 'not c.z', 'c.z', 'not c.v', 'c.v',
                  'not c.n', 'c.n', 'c.n == c.v', 'c.n != c.v',
                  'not c.z and c.n == c.v', 'c.z or c.n != c.v')
    for index, condition in enumerate(conditions):
        table[0x20 + index] = _handler(0x20 + index,
            'offset = c.fetch()\n' + f'if {condition}:\n' +
            '    c.pc = (c.pc + (offset if offset < 128 else offset - 256)) & 65535')

    unary = {
        0: 'result = c.sub(0, value)',
        3: 'result = c.nz(value ^ 255)\nc.c = True',
        4: 'result = c.nz(value >> 1)\nc.c = bool(value & 1)\nc.v = c.c',
        6: ('carry = bool(c.c)\nresult = c.nz((value >> 1) | (128 if carry else 0))\n'
            'c.c = bool(value & 1)\nc.v = c.n != c.c'),
        7: 'result = c.nz((value >> 1) | (value & 128))\nc.c = bool(value & 1)\nc.v = c.n != c.c',
        8: 'result = c.add(value, value)',
        9: ('carry = bool(c.c)\nresult = c.nz((value << 1) | int(carry))\n'
            'c.c = bool(value & 128)\nc.v = c.n != c.c'),
        10: 'result = c.nz(value - 1)\nc.v = value == 128',
        12: 'result = c.nz(value + 1)\nc.v = value == 127',
        13: 'c.nz(value)\nc.c = 0',
        15: 'result = c.nz(0)\nc.c = 0',
    }
    for mode in range(4, 8):
        prefix = ('' if mode < 6 else _address(2 if mode == 6 else 3))
        register = 'a' if mode == 4 else 'b'
        value = f'c.{register}' if mode < 6 else 'c.read(address)'
        store = f'c.{register} = result' if mode < 6 else 'c.write(address, result)'
        for operation, body in unary.items():
            op = mode * 16 + operation
            table[op] = _handler(op, prefix + f'value = {value}\n' + body +
                                 ('\n' + store if operation != 13 else ''))
        if mode >= 6:
            op = mode * 16 + 14
            table[op] = _handler(op, prefix + 'c.pc = address')

    for op in range(0x80, 0x100):
        mode, operation = (op >> 4) & 3, op & 15
        bank_b = op >= 0xc0
        wide = operation in (3, 12, 14, 15) or (bank_b and operation == 13)
        prefix = _address(mode, wide)
        register = 'b' if bank_b else 'a'
        if operation == 13 and not bank_b:
            body = 'c.push(c.pc & 255)\nc.push(c.pc >> 8)\nc.pc = address'
        elif operation in (7, 15) or (bank_b and operation == 13):
            value = (('c.x' if bank_b else 'c.sp') if operation == 15 else
                     'c.d' if operation == 13 else f'c.{register}')
            body = (f'value = {value}\n' +
                    ('c.putword(address, value)\n' if wide else 'c.write(address, value)\n') +
                    f'c.nz(value, {16 if wide else 8})')
        else:
            prefix += 'value = c.word(address)\n' if wide else 'value = c.read(address)\n'
            body = {
                0: f'c.{register} = c.sub(c.{register}, value)',
                1: f'c.sub(c.{register}, value)',
                2: (f'acc = c.{register}\nborrow = int(c.c)\nresult = c.nz(acc - value - borrow)\n'
                    'c.c = acc < value + borrow\nc.v = bool((acc ^ value) & (acc ^ result) & 128)\n'
                    f'c.{register} = result'),
                3: f'c.d = c.{"add" if bank_b else "sub"}(c.d, value, 16)',
                4: f'c.{register} = c.nz(c.{register} & value)',
                5: f'c.nz(c.{register} & value)',
                6: f'c.{register} = c.nz(value)',
                8: f'c.{register} = c.nz(c.{register} ^ value)',
                9: (f'acc = c.{register}\ntotal = acc + value + int(c.c)\nresult = c.nz(total)\n'
                    'c.c = total > 255\nc.v = bool((~(acc ^ value)) & (acc ^ result) & 128)\n'
                    f'c.{register} = result'),
                10: f'c.{register} = c.nz(c.{register} | value)',
                11: f'c.{register} = c.add(c.{register}, value)',
                12: 'c.d = c.nz(value, 16)' if bank_b else 'c.sub(c.x, value, 16)',
                14: f'c.{"x" if bank_b else "sp"} = c.nz(value, 16)',
            }.get(operation, f"raise AssertionError('unsupported ALU ${op:02X}')")
        table[op] = _handler(op, prefix + body)

    # HD6301 immediate masks override the indexed/extended unary encodings.
    for op in (0x61, 0x62, 0x65, 0x6b, 0x71, 0x72, 0x75, 0x7b):
        kind = op & 15
        expression = 'value | mask' if kind == 2 else 'value ^ mask' if kind == 5 else 'value & mask'
        table[op] = _handler(op,
            'mask,address = c.m[c.pc:c.pc+2]\nc.pc += 2\n' +
            ('address = (c.x + address) & 65535\n' if op < 0x70 else '') +
            f'value = c.read(address)\nvalue = {expression}\n' +
            ('c.write(address, value)\n' if kind != 11 else '') +
            'c.n = bool(value & 128)\nc.z = value == 0\nc.v = False')

    for op, body in inherent.items():
        table[op] = _handler(op, body)
    return tuple(table)
