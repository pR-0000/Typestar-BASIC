"""Exact functional shortcuts for two pure-RAM BASIC raster subroutines.

No motor, heat, keyboard or BASIC parser shortcuts. Byte guards include the
vertical-pitch helper: other ROM code falls back to instruction execution.
The CPU and scratch/stack effects match the interpreter, including stale stack
bytes. Timing remains functional, as in the rest of the BASIC adapter.
"""

def _return(c):
    c.pc=c.pop()*256+c.pop()

def _near(c,address):
    c.nz(c.a);c.c=0
    if c.z:c.sub(c.b,c.read(address))

def _call_near(c,address,return_pc):
    c.push(return_pc&255);c.push(return_pc>>8)
    _near(c,address)
    _return(c)

def rectangle_hit(c,offset=0):
    for left,right in ((0x1cf6,0x1ce8),(0x1cea,0x1cf6),
                       (0x1cf8,0x1cec),(0x1cee,0x1cf8)):
        c.d=c.nz(c.word(left),16)
        c.d=c.sub(c.d,c.word(right),16)
        if c.c:
            c.c=0;_return(c);return
    c.nz(c.read(0x1cf5));c.c=0
    if not c.z:
        c.c=1;_return(c);return
    _call_near(c,0x1d7a,0x40ce+offset)
    if c.c:
        c.c=1;_return(c);return
    c.d=c.nz(c.word(0x1cf8),16)
    c.d=c.sub(c.d,c.word(0x1cec),16)
    _call_near(c,0x1d7a,0x40d9+offset)
    if c.c:
        c.c=1;_return(c);return
    c.d=c.nz(c.word(0x1cf6),16)
    c.d=c.sub(c.d,c.word(0x1ce8),16)
    _call_near(c,0x1cf4,0x40e3+offset)
    if c.c:
        c.c=1;_return(c);return
    c.d=c.nz(c.word(0x1cea),16)
    c.d=c.sub(c.d,c.word(0x1cf6),16)
    _near(c,0x1cf4)
    _return(c)

def line_dot(c):
    c.d=c.nz(c.word(0x1d97),16)
    c.nz(c.a);c.c=0
    if not c.z:_return(c);return
    c.sub(c.b,247)
    if not(c.c or c.z):_return(c);return
    c.b=c.sub(c.b,c.read(0x1d85))
    if c.c:_return(c);return
    c.sub(c.b,31)
    if not c.c:_return(c);return
    c.write(0x1d9f,c.b);c.nz(c.b)
    c.d=c.nz(c.word(0x1d9b),16)
    c.nz(c.a);c.c=0
    if not c.z:_return(c);return
    old=c.b;c.b=c.nz(old>>1);c.c=bool(old&1);c.v=c.c
    c.b=c.sub(c.b,c.read(0x1d86))
    if c.c:_return(c);return
    c.sub(c.b,16)
    if not c.c:_return(c);return
    c.b=c.add(c.b,c.b)
    c.x=c.nz(0x60cd,16);c.x=(c.x+c.b)&65535
    c.d=c.nz(c.word(c.x),16)
    c.putword(0x1da0,c.d);c.nz(c.d,16)
    c.b=c.nz(c.read(0x1d9f));c.b=c.add(c.b,c.b)
    c.x=c.nz(0x1bc0,16);c.x=(c.x+c.b)&65535
    c.a=c.nz(c.read(c.x));c.a=c.nz(c.a|c.read(0x1da0))
    c.write(c.x,c.a);c.nz(c.a)
    c.a=c.nz(c.read(c.x+1));c.a=c.nz(c.a|c.read(0x1da1))
    c.write(c.x+1,c.a);c.nz(c.a)
    _return(c)

def kernels(memory):
    hit=bytes.fromhex('fc1cf6b31ce82541fc1ceab31cf62539fc1cf8b31cec2531fc1ceeb31cf825297d1cf52622bd56e8251dfc1cf8b31cecbd56e82512fc1cf6b31ce88d0e2508fc1ceab31cf620040d390c394d26fbf11cf439')
    dot=bytes.fromhex('fc1d974d2640c1f7223cf01d852537c11f2433f71d9ffc1d9b4d262a54f01d862524c110242058ce60cd3aec00fd1da0f61d9f58ce1bc03aa600ba1da0a700a601ba1da1a70139')
    near=bytes.fromhex('4d2604f11d7a390c39')
    result={}
    if memory[0x40a6:0x40a6+len(hit)]==hit and memory[0x56e8:0x56e8+len(near)]==near:
        result[0x40a6]=rectangle_hit
    if memory[0x4098:0x4098+len(hit)]==hit and memory[0x56e8:0x56e8+len(near)]==near:
        result[0x4098]=lambda c:rectangle_hit(c,-14)
    if memory[0x6086:0x6086+len(dot)]==dot:
        result[0x6086]=line_dot
    return result
