from i18n import tr
"""Read-only CPU debugger snapshots; never perform peripheral reads."""
from capstone import Cs, CS_ARCH_M680X, CS_MODE_M680X_6301

def inspect_cpu(cpu, symbols, address):
    address=max(0,min(65535,int(address)))
    memory=bytes(cpu.m)  # Backing image, not read(): no I/O side effects.
    lines=[]
    for start in range(address,min(address+256,65536),16):
        chunk=memory[start:min(start+16,65536)]
        lines.append(f'{start:04X}  '+chunk.hex(' ').upper().ljust(47)+'  '+''.join(chr(b) if 32<=b<127 else '.' for b in chunk))
    labels={}
    for name,value in symbols.items():labels.setdefault(value,[]).append(name)
    decoder=Cs(CS_ARCH_M680X,CS_MODE_M680X_6301)
    pc=cpu.pc;assembly=[]
    for _ in range(20):
        if pc>=65536:break
        names=labels.get(pc,[])

        ins=next(decoder.disasm(memory[pc:pc+4],pc,count=1),None)
        size=ins.size if ins else 1
        code=(ins.mnemonic+' '+ins.op_str) if ins else f'FCB ${memory[pc]:02X}'
        label='/'.join(names)
        assembly.append(f'{pc:04X}  {memory[pc:pc+size].hex(" ").upper():<12} {code:<25} {label}')
        pc+=size
    assembly += ['']*(20-len(assembly))
    registers='  '.join(f'{name.upper()}=${getattr(cpu,name):0{width}X}' for name,width in [('pc',4),('sp',4),('x',4),('a',2),('b',2)])
    registers+=f'  D=${cpu.d:04X}'
    flags='Flags : '+ ' '.join(f'{n.upper()}={int(getattr(cpu,n))}' for n in ('i','n','z','v','c'))
    return dict(type='debug',registers=registers,flags=flags+tr('  H : non modélisé'),memory='\n'.join(lines),assembly='\n'.join(assembly))
