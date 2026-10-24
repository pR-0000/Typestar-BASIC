"""Optional, byte-guarded shortcuts for known BASIC paper routines.

Patterns and compressed fonts come from the selected ROM and program RAM.
Equivalent host operations collapse raster loops, motor bookkeeping and device
waits, preserving native phase rings and coordinates. BASIC statements, sound
waits and keyboard waits still execute. Unknown code uses the CPU interpreter.
"""
import hashlib


def _return(c):
    c.pc = c.pop() * 256 + c.pop()


def _call(c, address, return_pc):
    c.push(return_pc & 255)
    c.push(return_pc >> 8)
    c.pc = address


def _phase(c):
    # $7563: exactly one observed motor phase, including the native ring pointer.
    c.xy[bool(c.m[0x41] & 32)] += -1 if c.m[0x41] & 16 else 1
    c.push(c.x & 255)
    c.push(c.x >> 8)
    c.a = c.nz(c.read(0x41))
    c.nz(c.a & 32)
    address, first = (0x50, 0x6ef1) if not c.z else (0x4e, 0x6ee9)
    c.x = c.nz(c.word(address), 16)
    c.nz(c.a & 16)
    reverse = not c.z
    c.sub(c.x, first if reverse else first + 7, 16)
    if c.z:
        c.x = c.nz(first + 7 if reverse else first, 16)
    else:
        c.x = (c.x + (-1 if reverse else 1)) & 65535
        c.z = c.x == 0
    c.putword(address, c.x)
    c.nz(c.x, 16)
    c.x = c.pop() * 256 + c.pop()
    _return(c)


def _advance(c):
    # $752C: countdown and phase advancement. Keep the native helper call frame.
    c.x = c.nz(c.word(0x4a), 16)
    c.a = c.nz(c.read(0x56))
    if c.z:
        c.d = c.nz(c.word(0x54), 16)
        if not c.z:
            c.d = c.sub(c.d, 1, 16)
            c.putword(0x54, c.d)
            c.nz(c.d, 16)
    c.d = c.nz(c.word(0x52), 16)
    c.d = c.sub(c.d, 1, 16)
    c.putword(0x52, c.d)
    c.nz(c.d, 16)
    if c.z:
        c.x = (c.x + 2) & 65535
        c.z = c.x == 0
        c.nz(c.read(0x41) & 64)
        if c.z:
            _call(c, 0x7563, 0x7561)
            _phase(c)
        c.c = 1
    else:
        old = c.read(0x49)
        value = c.nz(old - 1)
        c.v = old == 128
        c.write(0x49, value)
        if c.z:
            c.a = c.nz(2)
            c.write(0x49, c.a)
            _call(c, 0x7563, 0x754f)
            _phase(c)
            c.nz(c.read(0x41) & 128)
            if not c.z:
                c.x = (c.x + 2) & 65535
                c.z = c.x == 0
        c.c = 0
    _return(c)


def _schedule(c):
    c.putword(0x4a, c.x)
    c.nz(c.x, 16)
    c.x = c.nz(c.word(0x4e), 16)
    c.nz(c.read(0x41) & 32)
    if not c.z:
        c.x = c.nz(c.word(0x50), 16)
    c.a = c.nz(c.read(c.x))
    c.write(0x17, c.a)
    # Run the real auxiliary service; its effects depend on machine state.
    _call(c, 0x6c79, 0x7513)


def _schedule_tail(c):
    c.x = c.nz(c.word(0x4a), 16)
    c.d = c.nz(c.word(9), 16)
    c.d = c.add(c.d, c.word(c.x), 16)
    c.putword(0x0b, c.d)
    c.nz(c.d, 16)
    c.nz(c.read(0x41) & 8)
    if not c.z:
        c.write(8, c.nz(c.read(8) | 8))
    c.a = c.nz(c.read(0x108))
    c.a = c.nz(c.a & 254)
    c.write(0x108, c.a)
    _return(c)


def _dispatch(c):
    c.write(8, c.nz(c.read(8) & 245))
    c.write(0x123, c.nz(0))
    c.c = 0
    c.x = c.nz(0x7800, 16)
    c.b = c.nz(c.read(0x44))
    c.b = c.add(c.b, c.b)
    c.x = (c.x + c.b) & 65535
    c.x = c.nz(c.word(c.x), 16)
    c.pc = c.x


def _asic(c):
    # The BASIC bus reports the byte-transfer peripheral ready immediately.
    c.push(c.a)
    c.push(c.x & 255)
    c.push(c.x >> 8)
    c.x = c.nz(256, 16)
    c.a = c.nz(c.read(0x34))
    c.nz(c.a & 128)
    c.x = c.pop() * 256 + c.pop()
    c.a = c.pop()
    c.write(0x33, c.a)
    c.nz(c.a)
    c.a = c.nz(c.read(0x1801))
    c.a = c.nz(c.a | 128)
    c.write(0x34, c.a)
    _return(c)


def _phase_wait(c):
    c.push(c.a)
    c.push(c.x & 255)
    c.push(c.x >> 8)
    c.x = c.nz(256, 16)
    c.a = c.nz(c.read(0x0f))
    c.nz(c.a & 32)
    c.x = c.pop() * 256 + c.pop()
    c.a = c.pop()
    _return(c)


def _heat_mask(c):
    # Native three-lane heat mask; retain $76E7 so normal paper capture runs.
    c.x = c.nz(0x58, 16)
    c.d = c.nz(c.word(c.x + 3), 16)
    c.a = c.nz((c.a ^ c.read(0x66)) & c.read(0x66))
    c.b = c.nz((c.b ^ c.read(0x67)) & c.read(0x67))
    c.putword(c.x, c.d)
    c.nz(c.d, 16)
    c.a = c.nz((c.read(c.x + 5) ^ c.read(0x68)) & c.read(0x68))
    c.b = c.nz(c.read(0x6e))
    if c.z:
        c.a = c.nz(c.a & 127)
    c.write(0x6e, c.nz(0))
    c.c = 0
    c.write(c.x + 2, c.a)
    c.nz(c.a)
    c.d = c.nz(c.word(0x66), 16)
    c.putword(c.x + 3, c.d)
    c.nz(c.d, 16)
    c.a = c.nz(c.read(0x68))
    c.write(c.x + 5, c.a)
    c.pc = 0x76e7


def _travel(c, s):
    # Constant-speed, non-heating travel: fold all but the last timer stage.
    # Acceleration, deceleration and the last phase still use the native code.
    remaining = c.word(0x52)
    cadence = c.read(0x49)
    skip = remaining - 1
    if (remaining > 2 and cadence in (1, 2) and c.m[0x41] & 0xc0 == 0x40
            and c.word(0x54) == 0 and c.read(0x56) == 0
            and not c.read(0x32) & 32 and c.read(0xc3) == 0
            and c.word(s['GPTICKS']) > skip):
        moves, partial = divmod(skip + 2 - cadence, 2)
        axis = bool(c.m[0x41] & 32)
        direction = -1 if c.m[0x41] & 16 else 1
        address, first = (0x50, 0x6ef1) if axis else (0x4e, 0x6ee9)
        phase = c.word(address)
        if first <= phase < first + 8:
            phase = first + (phase - first + direction * moves) % 8
            c.putword(address, phase)
            c.xy[axis] += direction * moves
            c.write(0x49, 2 - partial)
            c.putword(0x52, 1)
            c.write(0x17, c.read(phase))
            c.putword(0x0b, (c.word(9) + c.word(c.word(0x4a))) & 65535)
            if c.m[0x41] & 8:
                c.write(8, c.read(8) | 8)
            c.write(0x108, c.read(0x108) & 254)
            c.putword(s['GPTICKS'], c.word(s['GPTICKS']) - skip)
    _call(c, 0x752c, 0x7211)
    _advance(c)


def _settle(c, s):
    # Fixed pre-print motor settling delay, without movement or heating.
    skip = c.word(0x6c) - 1
    if skip > 0 and c.word(s['GPTICKS']) > skip:
        c.putword(0x6c, 1)
        c.putword(s['GPTICKS'], c.word(s['GPTICKS']) - skip)
    c.d = c.nz(c.word(0x6c), 16)
    c.pc = 0x732c


def _loop(c, s):
    # Collapse the synchronous foreground scheduler, keeping native timer stages.
    _call(c, s['PRINT_REPAIR_PAPER_CONTINUATION'], s['GPLOOP'] + 3)
    c.push(c.x & 255)
    c.push(c.x >> 8)
    c.x = c.nz(c.word(0x45), 16)
    c.sub(c.x, 0x70d6, 16)
    if c.z:
        c.x = c.nz(s['PRINT_RAW_PAPER_DONE'], 16)
        c.putword(0x45, c.x)
        c.nz(c.x, 16)
    c.x = c.pop() * 256 + c.pop()
    _return(c)
    c.nz(c.read(s['PRINT_GLYPH_BUSY']))
    c.c = 0
    if c.z:
        c.pc = s['GPDONE']
        return
    c.x = c.nz(c.word(s['GPTICKS']), 16)
    c.x = (c.x - 1) & 65535
    c.z = c.x == 0
    c.putword(s['GPTICKS'], c.x)
    c.nz(c.x, 16)
    if c.z:
        c.pc = s['GPTOOMANY']
        return
    c.x = c.nz(65535, 16)
    c.a = c.nz(c.read(8))
    c.nz(c.a & 64)
    c.pc = s['GPWAIT'] + 6 if c.z else s['GPTICK']


def _glyph(c, s):
    start, tiles, band = c.x, c.b, (c.a << 4) & 255
    if 'TMDECODE' in s:
        c.putword(s['SGDEST'],start)
    for address in range(start, start + ((tiles << 6) & 255 or 256)):
        c.write(address, 0)
    c.write(s['SGBAND'], band)
    out, column = start, 0
    mode = c.m[s['SGZOOM']]
    width, height = c.m[s['SGOUTWIDTH']], c.m[s['SGOUTHEIGHT']]
    while True:
        for row in range(16):
            source_y = (row + band) & 255
            if source_y >= height:
                continue
            if not mode & 1:
                source_y >>= 1
            source_x = column >> (0 if mode == 1 else 2 if mode == 4 else 1)
            # Preserve the scratch stack byte written by the native PSHB/PULB.
            c.push(source_x)
            c.pop()
            address = s['GXPATTERN'] + ((source_y << 2) & 255) + (source_x >> 3)
            if c.read(address) & (128 >> (source_x & 7)):
                value = c.word(out) | c.word(s['PBMASKS'] + 2 * row)
                c.putword(out, value)
        out += 2
        column += 1
        wide_driver = 'SGPAIR' in s
        if wide_driver:
            c.push(out & 255);c.push(out >> 8);c.pop();c.pop()
        c.b = ((out-start) & 63) if wide_driver else column & 31
        if c.b == (62 if wide_driver else 31):
            out += 2
            c.b = mode
            if mode == 4:
                column += 1
        if column >= width:
            break
    c.putword(s['SGOUT'], out)
    c.write(s['SGCOL'], column)
    c.write(s['SGROW'], 16)
    c.x = out
    c.a = c.nz(column)
    c.sub(c.a, width)
    c.c = 0
    _return(c)


def _font_level(c, s):
    # Decode canonical Huffman bits from the selected ROM, never a host font.
    while True:
        _call(c, s['HFGETBIT'], s['HFLEVEL'] + 3)
        _return(c)
        bits = c.m[s['HFBITS']]
        if not bits:
            ptr = c.word(s['HFSRC'])
            if ptr < c.word(s['HFSTOP']):
                c.write(s['HFBYTE'], c.read(ptr))
                c.putword(s['HFSRC'], ptr + 1)
                bits = 8
        bit = 0
        if bits:
            byte = c.m[s['HFBYTE']]
            bit = byte >> 7
            c.write(s['HFBYTE'], byte << 1)
            c.write(s['HFBITS'], bits - 1)
        code = ((c.word(s['HFCODE']) << 1) | bit) & 65535
        c.putword(s['HFCODE'], code)
        ptr = c.word(s['HFCPTR'])
        count = c.read(ptr)
        c.putword(s['HFCOUNT'], count)
        c.putword(s['HFCPTR'], ptr + 1)
        first = c.word(s['HFFIRST'])
        c.x = ptr
        c.d = c.sub(code, first, 16)
        if c.c:
            c.pc = s['HFBAD']
            return
        c.d = c.sub(c.d, count, 16)
        if c.c:
            c.pc = s['HFFOUND']
            return
        c.putword(s['HFSPTR'], (c.word(s['HFSPTR']) + count) & 65535)
        c.putword(s['HFFIRST'], ((first + count) << 1) & 65535)
        old = c.m[s['HFLEN']]
        c.write(s['HFLEN'], c.nz(old - 1))
        c.v = old == 128
        if c.z:
            c.pc = s['HFBAD']
            return


def kernels(memory, symbols):
    """Enable each block only for its exact native instruction bytes."""
    blocks = {
        0x7563: (_phase, '3c964185202622de4e8510260d8c6ef02703082003ce6ee9200b8c6ee92703092003ce6ef0df4e3839de508510260d8c6ef82703082003ce6ef1200b8c6ef12703092003ce6ef8df503839'),
        0x752c: (_advance, 'de4a96562609dc542705830001dd54dc52830001dd5227147a0049260d860297498d147b8041270208080c3908087b404126028d020d39'),
        0x7501: (_schedule, 'df4ade4e7b20412702de50a6009717bd6c79'),
        0x7513: (_schedule_tail, 'de4adc09e300dd0b7b08412703720808b6010884feb7010839'),
        0x77ef: (_dispatch, '71f5087f0123ce7800d644583aee006e00'),
        0x76bf: (_heat_mask, 'ce0058ec0398669466d867d467ed00a60598689468d66e2602847f7f006ea702dc66ed039668a705'),
    }
    result = {pc: fn for pc, (fn, code) in blocks.items()
              if memory[pc:pc + len(bytes.fromhex(code))] == bytes.fromhex(code)}
    # The countdown calls the phase helper internally; guard both as a unit.
    if 0x7563 not in result:
        result.pop(0x752c, None)
    s = symbols
    for name, fn, code in (
        ('GPASIC', _asic, '363cce01009634858027080926f786017e'),
        ('GPPHASEWAIT', _phase_wait, '363cce0100960f852026080926f786057e'),
    ):
        if name in s and 'GPABORT' in s:
            prefix = bytes.fromhex(code) + s['GPABORT'].to_bytes(2, 'big')
            tail = (bytes.fromhex('38329733b618018a80973439')
                    if name == 'GPASIC' else bytes.fromhex('383239'))
            pc = s[name]
            if memory[pc:pc + len(prefix + tail)] == prefix + tail:
                result[pc] = fn
    required = ('GPLOOP', 'GPDONE', 'GPTOOMANY', 'GPWAIT', 'GPTICK',
                'PRINT_GLYPH_BUSY', 'GPTICKS', 'PRINT_REPAIR_PAPER_CONTINUATION',
                'PRINT_RAW_PAPER_DONE')
    if all(name in s for name in required):
        word = lambda value: value.to_bytes(2, 'big')
        prefix = (b'\xbd' + word(s['PRINT_REPAIR_PAPER_CONTINUATION']) +
                  b'\x7d' + word(s['PRINT_GLYPH_BUSY']) +
                  bytes([0x27, (s['GPDONE'] - s['GPLOOP'] - 8) & 255]) +
                  b'\xfe' + word(s['GPTICKS']) + b'\x09\xff' + word(s['GPTICKS']) +
                  bytes([0x27, (s['GPTOOMANY'] - s['GPLOOP'] - 17) & 255]) +
                  bytes.fromhex('ceffff96088540'))
        repair = (bytes.fromhex('3cde458c70d62605ce') +
                  word(s['PRINT_RAW_PAPER_DONE']) + bytes.fromhex('df453839'))
        pc, r = s['GPLOOP'], s['PRINT_REPAIR_PAPER_CONTINUATION']
        if (memory[pc:pc + len(prefix)] == prefix and
                memory[r:r + len(repair)] == repair):
            result[pc] = lambda c: _loop(c, s)
            if (0x752c in result and
                    memory[0x720a:0x7213] == bytes.fromhex('bd75013bbd752c24f7')):
                result[0x720e] = lambda c: _travel(c, s)
            if memory[0x7324:0x7335] == bytes.fromhex('ce6f757e74f7dc6c8300012704dd6c20ef'):
                result[0x732a] = lambda c: _settle(c, s)
    # The larger pure-RAM routines have split ROM islands. Hash their exact
    # instruction blocks; their pattern/mask/font data is still read at runtime.
    groups = [
        ([(0xa5e0, 0xa5ff, '16ff8732f6fd891ff6eaedce4719ab23e0e83b144480c7ec3148710e2d196a22'),
          (0xb448, 0xb4d7, 'f2dbb239896f4dd19218949ee618a1ce5d12816c817cecee9d01131505f3c3a4')],
         'SGRENDER', _glyph),
        ([(0x85db, 0x85f7, 'fd1e0de834f72d2d01ac926e5ae8c619bdd826a8178fa14c1ad2464d2fbc52af'),
          (0xb448, 0xb4d7, '9b40200652dad1ad7ebbc81e087c7467aa4e6458bbdfbb3363a8f0b4694eb246')],
         'SGRENDER', _glyph),
        ([(0xb33d, 0xb35c, '16ff8732f6fd891ff6eaedce4719ab23e0e83b144480c7ec3148710e2d196a22'),
          (0xb448, 0xb4d7, 'f2dbb239896f4dd19218949ee618a1ce5d12816c817cecee9d01131505f3c3a4')],
         'SGRENDER', _glyph),
        ([(0x85db, 0x85f7, 'fd1e0de834f72d2d01ac926e5ae8c619bdd826a8178fa14c1ad2464d2fbc52af'),
          (0xb448, 0xb4d7, '775daa015a392b8002f78caaa27894f7f2aa14959a41f3df68c98bb1e39b7230')],
         'SGRENDER', _glyph),
        ([(0x84fe, 0x853d, '4e87846e89c89851e66e51871f4cc4f9d186f00ddf2fcbb4584abe9086e45578'),
          (0x857c, 0x85a3, 'a0be52ba2e60708d27c1cd5fbeb73d9c57f8cf3b46232c69ca8e4d878634464f')],
         'HFLEVEL', _font_level),
    ]
    for guards, name, fn in groups:
        if name in s and all(hashlib.sha256(memory[a:b]).hexdigest() == digest
                             for a, b, digest in guards):
            result[s[name]] = lambda c, fn=fn: fn(c, s)
    return result
