"""HD6301 instruction interpreter and shared functional bus primitives.

CPUBase.step is the reference decoder; HD6301CPU.step uses an opcode table.
The reference path includes extended opcodes and interrupt frames for tests.
Functional timing, not cycle accurate.
Unknown opcodes fail explicitly. No firmware addresses or BASIC hooks.
"""
from collections import deque


class CPUBase:
    def __init__(self, image):
        self.m = bytearray([0xA5] * 65536)
        self.m[0x4000:0xC000] = image
        self.a = self.b = self.x = 0
        self.sp = 0x1FFF
        self.pc = 0x6800
        self.c = self.z = self.n = self.v = 0
        self.i = 1
        self.rx = deque()
        self.tx = bytearray()
        self.writes = set()
        self.min_sp = self.sp
        self.keys = set()
        self.modifier = False
        self.lcd_busy = False
        self.lcd_control = 12
        self.tx_ready = True
        self.lcd_address = 0
        self.lcd = bytearray(b' ' * 128)
        self.lcd_commands = []
        self.cgram = bytearray(64)
        self.cgram_selected = False

    @property
    def d(self):
        return self.a * 256 + self.b

    @d.setter
    def d(self, value):
        self.a, self.b = (value >> 8) & 255, value & 255

    def lcd_advance(self):
        if self.cgram_selected:
            self.lcd_address = (self.lcd_address + 1) & 127
        else:
            self.lcd_address = (0x40 if self.lcd_address == 0x27 else
                                0 if self.lcd_address == 0x67 else
                                (self.lcd_address + 1) & 127)

    def read(self, address):
        if address == 0x11:
            return (0x20 if self.tx_ready else 0) | (0x80 if self.rx else 0) | (self.m[0x11] & 0x1F)
        if address == 0x12:
            return self.rx.popleft() if self.rx else 0
        if address == 0x38:
            return (0x80 if self.lcd_busy else 0) | self.lcd_address
        if address == 0x39:
            value = (self.cgram[self.lcd_address & 63] if self.cgram_selected
                     else self.lcd[self.lcd_address])
            self.lcd_advance()
            return value
        if address == 0x30:
            selector = self.m[0x31]
            value = 255
            for key in self.keys:
                if selector == (255 ^ (1 << (key//8))):
                    value &= ~(1 << (key % 8))
            return value
        if address == 0x32:
            return (self.m[address] & 0x7F) | (0x80 if self.modifier else 0)
        return self.m[address]

    def write(self, address, value):
        assert (address < 0x100 or 0x1000 <= address < 0x1800 or
                0x1800 <= address <= 0x1802 or 0x1900 <= address <= 0x19FF or
                0x1A00 <= address <= 0x1B7F or 0x1B80 <= address <= 0x1EFF or
                0x1F00 <= address <= 0x1FFF or 0x2000 <= address <= 0x37FF), f'unexpected write ${address:04X}'
        self.writes.add(address)
        self.m[address] = value & 255
        if address == 0x13:
            self.tx.append(value & 255)
        if address == 0x38:
            self.lcd_commands.append(value & 255)
            if value & 0x80:
                self.lcd_address = value & 0x7F
                self.cgram_selected = False
            elif value & 0x40:
                self.lcd_address = value & 0x7F
                self.cgram_selected = True
            elif 8 <= value <= 15:
                self.lcd_control = value
            elif value in (1, 2):
                self.cgram_selected = False
                self.lcd_address = 0
                if value == 1:
                    self.lcd[:] = b' ' * 128
        if address == 0x39:
            if self.cgram_selected:
                self.cgram[self.lcd_address & 63] = value & 255
            else:
                self.lcd[self.lcd_address] = value & 255
            self.lcd_advance()

    def word(self, address):
        return self.read(address) * 256 + self.read(address + 1)

    def putword(self, address, value):
        self.write(address, value >> 8)
        self.write(address + 1, value)

    def fetch(self):
        value = self.read(self.pc)
        self.pc = (self.pc + 1) & 65535
        return value

    def fetchword(self):
        return self.fetch() * 256 + self.fetch()

    def push(self, value):
        self.write(self.sp, value)
        self.sp -= 1
        self.min_sp = min(self.min_sp, self.sp)

    def pop(self):
        self.sp += 1
        return self.read(self.sp)

    def nz(self, value, bits=8):
        value &= (1 << bits) - 1
        self.n = bool(value & (1 << (bits - 1)))
        self.z = value == 0
        self.v = 0
        return value

    def sub(self, left, right, bits=8):
        result = self.nz(left - right, bits)
        self.c = left < right
        self.v = bool((left ^ right) & (left ^ result) & (1 << (bits - 1)))
        return result

    def add(self, left, right, bits=8):
        result = self.nz(left + right, bits)
        self.c = left + right >= (1 << bits)
        self.v = bool(~(left ^ right) & (left ^ result) & (1 << (bits - 1)))
        return result

    def step(self):
        location = self.pc
        op = self.fetch()
        if op == 0x0F:
            self.i = 1
        elif op == 0x0C:
            self.c = 0
        elif op == 0x0D:
            self.c = 1
        elif op == 0x01:
            pass
        elif op == 0x11:  # CBA: compare without changing either accumulator.
            self.sub(self.a, self.b)
        elif op == 0x16:
            self.b = self.nz(self.a)
        elif op == 0x17:
            self.a = self.nz(self.b)
        elif op == 0x3A:
            self.x = (self.x + self.b) & 65535
        elif op == 0x05:
            self.d = self.add(self.d, self.d, 16)
        elif op in (0x08, 0x09):
            self.x = (self.x + (1 if op == 8 else -1)) & 65535
            self.z = self.x == 0
        elif op == 0x30:  # TSX: stack top, condition codes unchanged.
            self.x = (self.sp + 1) & 65535
        elif op == 0x36:
            self.push(self.a)
        elif op == 0x37:
            self.push(self.b)
        elif op == 0x3C:
            self.push(self.x & 255)
            self.push(self.x >> 8)
        elif op == 0x38:
            self.x = self.pop() * 256 + self.pop()
        elif op == 0x33:
            self.b = self.pop()
        elif op == 0x32:
            self.a = self.pop()
        elif op == 0x39:
            self.pc = self.pop() * 256 + self.pop()
        elif 0x20 <= op <= 0x2F:
            offset = self.fetch()
            conditions = [True, False, not (self.c or self.z), self.c or self.z,
                          not self.c, self.c, not self.z, self.z, not self.v,
                          self.v, not self.n, self.n, self.n == self.v,
                          self.n != self.v, not self.z and self.n == self.v,
                          self.z or self.n != self.v]
            if conditions[op - 0x20]:
                self.pc = (self.pc + (offset if offset < 128 else offset - 256)) & 65535
        elif op == 0x7B:  # HD6301 TIM immediate,direct (mask-ROM reset)
            mask, address = self.fetch(), self.fetch()
            self.nz(self.read(address) & mask)
        elif 0x40 <= op <= 0x7F:
            mode, operation = op >> 4, op & 15
            address = None
            if mode == 6:
                address = (self.x + self.fetch()) & 65535
            elif mode == 7:
                address = self.fetchword()
            if operation == 14 and address is not None:
                self.pc = address
                return
            value = self.a if mode == 4 else self.b if mode == 5 else self.read(address)
            if operation == 15:
                result = self.nz(0)
                self.c = 0
            elif operation == 13:
                self.nz(value)
                self.c = 0
                return
            elif operation == 12:
                result = self.nz(value + 1)
                self.v = value == 127
            elif operation == 10:
                result = self.nz(value - 1)
                self.v = value == 128
            elif operation == 8:
                result = self.add(value, value)
            elif operation == 0:  # NEG
                result = self.sub(0, value)
            elif operation == 7:  # ASR: retain the sign bit.
                result = self.nz((value >> 1) | (value & 128))
                self.c = bool(value & 1)
                self.v = self.n != self.c
            elif operation == 3:  # COM
                result = self.nz(value ^ 255)
                self.c = True
            elif operation == 6:  # ROR
                carry = bool(self.c)
                result = self.nz((value >> 1) | (128 if carry else 0))
                self.c = bool(value & 1)
                self.v = self.n != self.c
            elif operation == 9:  # ROL
                carry = bool(self.c)
                result = self.nz((value << 1) | int(carry))
                self.c = bool(value & 128)
                self.v = self.n != self.c
            elif operation == 4:
                result = self.nz(value >> 1)
                self.c = bool(value & 1)
                self.v = self.c
            else:
                raise AssertionError(f'unsupported unary ${op:02X} at ${location:04X}')
            if mode == 4:
                self.a = result
            elif mode == 5:
                self.b = result
            else:
                self.write(address, result)
        elif op >= 0x80:
            mode, operation = (op >> 4) & 3, op & 15
            bank_b = op >= 0xC0
            wide = operation in (3, 12, 14, 15) or (bank_b and operation == 13)
            if mode == 0:
                address = self.pc
                self.pc += 2 if wide else 1
            elif mode == 1:
                address = self.fetch()
            elif mode == 2:
                address = (self.x + self.fetch()) & 65535
            else:
                address = self.fetchword()
            if operation == 13 and not bank_b:
                self.push(self.pc & 255)
                self.push(self.pc >> 8)
                self.pc = address
                return
            if operation in (7, 15) or (bank_b and operation == 13):
                value = (self.x if bank_b else self.sp) if operation == 15 else self.d if operation == 13 else self.b if bank_b else self.a
                if wide:
                    self.putword(address, value)
                else:
                    self.write(address, value)
                self.nz(value, 16 if wide else 8)
                return
            value = self.word(address) if wide else self.read(address)
            acc = self.b if bank_b else self.a
            if operation == 14:
                value = self.nz(value, 16)
                if bank_b:
                    self.x = value
                else:
                    self.sp = value
            elif operation == 12:
                if bank_b:
                    self.d = self.nz(value, 16)
                else:
                    self.sub(self.x, value, 16)
            elif operation == 3:
                self.d = self.add(self.d, value, 16) if bank_b else self.sub(self.d, value, 16)
            elif operation == 1:
                self.sub(acc, value)
            elif operation == 5:
                self.nz(acc & value)
            elif operation == 2:  # SBCA/SBCB: C is the incoming borrow.
                borrow = int(self.c)
                result = self.nz(acc - value - borrow)
                self.c = acc < value + borrow
                self.v = bool((acc ^ value) & (acc ^ result) & 128)
                if bank_b:
                    self.b = result
                else:
                    self.a = result
            elif operation == 9:  # ADCA/ADCB: preserve incoming carry for the sum.
                total = acc + value + int(self.c)
                result = self.nz(total)
                self.c = total > 255
                self.v = bool((~(acc ^ value)) & (acc ^ result) & 128)
                if bank_b:
                    self.b = result
                else:
                    self.a = result
            elif operation in (0, 4, 6, 8, 10, 11):
                result = self.sub(acc, value) if operation == 0 else self.nz(acc & value) if operation == 4 else self.nz(value) if operation == 6 else self.nz(acc ^ value) if operation == 8 else self.add(acc, value) if operation == 11 else self.nz(acc | value)
                if bank_b:
                    self.b = result
                else:
                    self.a = result
            else:
                raise AssertionError(f'unsupported ALU ${op:02X} at ${location:04X}')
        else:
            raise AssertionError(f'unsupported opcode ${op:02X} at ${location:04X}')

    def until_idle(self, getc, budget=500_000):
        start = len(self.tx)
        for _ in range(budget):
            if self.pc == getc and not self.rx:
                return bytes(self.tx[start:]).decode('ascii')
            self.step()
        raise TimeoutError(f'instruction budget exhausted at ${self.pc:04X}')


class HD6301CPU(CPUBase):
    def __init__(self, image):
        super().__init__(image)
        self.frames = []

    def fetch(self):
        pc = self.pc
        value = self.m[pc] if pc >= 0x100 else self.read(pc)
        self.pc = (pc + 1) & 65535
        return value

    def step(self):
        pc = self.pc
        if 0x100 <= pc < 0xfffd:
            op = self.m[pc]
            self.pc = pc + 1
            self._opcode_handlers[op](self)
        else:
            # Preserve bus-side instruction fetches and unusual wraparound cases.
            self.step_reference()

    def step_reference(self):
        if self.m[self.pc] in (0x61,0x62,0x65,0x6B,0x71,0x72,0x75,0x7B):
            # HD6301 AIM/OIM/EIM/TIM; direct or indexed, C unchanged.
            op=self.m[self.pc]
            mask,address=self.m[self.pc+1:self.pc+3];self.pc+=3
            if op<0x70:address=(self.x+address)&65535
            kind=op&15;value=self.read(address)
            value=(value|mask) if kind==2 else (value^mask) if kind==5 else (value&mask)
            if kind!=11:self.write(address,value)
            self.n=bool(value&128);self.z=value==0;self.v=False
            return
        if self.m[self.pc]==0x3B:
            self.frames.append(bytes(self.m[self.sp+1:self.sp+8]))
            cc=self.pop();self.b=self.pop();self.a=self.pop()
            self.x=self.pop()*256+self.pop();self.pc=self.pop()*256+self.pop()
            self.c,self.v,self.z,self.n,self.i=[bool(cc&bit) for bit in (1,2,4,8,16)]
            return
        self._extended_step()

    def _extended_step(self):
        op = self.m[self.pc]
        if op == 0x3f:  # SWI: save the pre-interrupt CCR, then mask IRQs.
            self.pc = (self.pc + 1) & 65535
            cc = 0xc0 | int(self.c) | (int(self.v)<<1) | (int(self.z)<<2) | (int(self.n)<<3) | (int(self.i)<<4)
            for value in (self.pc & 255, self.pc >> 8, self.x & 255,
                          self.x >> 8, self.a, self.b, cc):self.push(value)
            self.i = True
            self.pc = self.word(0xfffa)
            return
        if op in (0x0a, 0x0b, 0x0e, 0x34, 0x35):
            self.pc = (self.pc + 1) & 65535
            if op == 0x0a:self.v = False
            elif op == 0x0b:self.v = True
            elif op == 0x0e:self.i = False
            elif op == 0x34:self.sp = (self.sp - 1) & 65535
            else:self.sp = (self.x - 1) & 65535
            return
        op=self.m[self.pc]
        if op==0x31: # INS: discard one stack byte, condition codes unchanged.
            self.pc+=1;self.sp=(self.sp+1)&65535;return
        if op==0x04: # HD6301 LSRD: logical right shift, V=N xor C, N=0.
            self.pc+=1
            self.c=bool(self.d&1);self.d>>=1
            self.n=False;self.z=self.d==0;self.v=self.c
            return
        if op not in (0x06,0x07,0x18,0x3D,0x8D,0x10,0x1B,0x40,0x50):
            return super().step()
        self.pc+=1
        if op==0x06:self.c,self.v,self.z,self.n,self.i=[bool(self.a&m) for m in (1,2,4,8,16)]
        elif op==0x07:self.a=0xC0|int(self.c)|(int(self.v)<<1)|(int(self.z)<<2)|(int(self.n)<<3)|(int(self.i)<<4)
        elif op==0x18:self.d,self.x=self.x,self.d
        elif op==0x3D:
            self.d=self.a*self.b;self.c=bool(self.b&128)
        elif op==0x8D:
            offset=self.fetch();self.push(self.pc&255);self.push(self.pc>>8)
            self.pc=(self.pc+(offset if offset<128 else offset-256))&65535
        elif op==0x10:self.a=self.sub(self.a,self.b)
        elif op==0x1B:self.a=self.add(self.a,self.b)
        else:
            reg='a' if op==0x40 else 'b';setattr(self,reg,self.sub(0,getattr(self,reg)))


from hd6301_dispatch import build_dispatch
HD6301CPU._opcode_handlers = build_dispatch()
