"""Original reset/startup writes with explicit hardware completion stubs.
Not a cycle-accurate or interrupt-complete machine model. Never flash.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RESEARCH=ROOT.parents[1]/'ROMReader'
sys.path.insert(0,str(RESEARCH/'tools'))
from trace_s70_keyboard import KeyboardMachine
from disassemble_hd6301 import make_disassembler,absolute_target,CONDITIONAL_BRANCHES
class BootMachine(KeyboardMachine):
    def __init__(self,m,cartridge=False):
        super().__init__(m);self.writes=[];self.skips=[];self.internal_program_writes=[]
        self.cartridge=cartridge;self.banks={1:bytearray(8192),2:bytearray(8192)}
    def write(self,a,v):
        self.writes.append((self.executing,a,v&255))
        if 0x20C0<=a<0x3800 and self.m[0x36]==0:
            self.internal_program_writes.append((self.executing,a,v&255))
        if 0x2000<=a<0x4000 and self.m[0x36] in (1,2):
            if self.cartridge:self.banks[self.m[0x36]][a-0x2000]=v&255
            return
        super().write(a,v)
    def read(self,a):
        if a==8:return super().read(a)|0x40 # output compare completes immediately
        if 0x2000<=a<0x4000 and self.m[0x36] in (1,2):
            return self.banks[self.m[0x36]][a-0x2000] if self.cartridge else 255
        return super().read(a)
    def step(self):
        if self.pc==0xF2DA:
            self.skips.append(self.pc) # carriage homing: no motor/IRQ model
            self.pc=self.pop()*256+self.pop();return
        super().step()
def memory():
    m=bytearray(65536)
    m[0x4000:0xC000]=(ROOT/'build/canon-basic/s70-basic-cpu.bin').read_bytes()
    m[0xC000:]=(RESEARCH/'dumps/dump_hd6301_v3_fast_1.bin').read_bytes()
    return m
def until(c,target,budget=300000):
    for n in range(budget):
        if c.pc==target:return n
        c.step()
    raise AssertionError(f'timeout {c.pc:04X}')
def ranges(values):
    result=[]
    for a in sorted(set(values)):
        if result and result[-1][1]+1==a:result[-1][1]=a
        else:result.append([a,a])
    return [[f'{a:04X}',f'{b:04X}'] for a,b in result]
def static_inventory():
    m=memory()
    raw=(RESEARCH/'dumps/256ROM_NH7_1181.bin').read_bytes()
    m[0x4000:0xC000]=raw[16384:]+raw[:16384]
    md=make_disassembler();todo=[0xFFE0,0x6800];seen={};indirect=[];stores=[]
    while todo:
        pc=todo.pop()
        if pc==0x6829 or pc in seen:continue
        ins=next(md.disasm(bytes(m[pc:pc+4]),pc,1));seen[pc]=ins
        op=ins.mnemonic;target=absolute_target(ins)
        if op.startswith('st') or op in ('clr','inc','dec','aim','oim','eim'):
            stores.append(dict(pc=f'{pc:04X}',instruction=f'{op} {ins.op_str}'))
        if op in ('jsr','bsr','jmp','bra') or op in CONDITIONAL_BRANCHES:
            if target is not None:todo.append(target)
            elif op in ('jsr','jmp'):indirect.append(f'{pc:04X}: {op} {ins.op_str}')
        if op not in ('rts','rti','jmp','bra','swi','wai','slp','fcb'):todo.append(pc+ins.size)
    return dict(instructions=len(seen),stores=sorted(stores,key=lambda x:x['pc']),
                unresolved_indirect=indirect,
                scope='Original synchronous startup closure, both conditional arms; stops at 6829. Not IRQ-complete.')
def main():
    cases=[]
    for cartridge in (False,True):
        for fill in (0,0xA5,0xFF):
            m=memory();m[0x1800:0x1F00]=bytes([fill])*0x700
            c=BootMachine(m,cartridge);c.pc=0xFFE0
            until(c,0x6829)
            native=[(pc,a,v) for pc,a,v in c.writes if pc>=0x6800]
            # The selected backup ranges are never native write destinations
            # on these traces; exclude the two alternate buffer headers.
            assert not any(0x1902<=a<=0x1A8E or 0x1A92<=a<=0x1AB4 or 0x1B00<=a<=0x1B08 for pc,a,v in native)
            cases.append(dict(cartridge=cartridge,initial_fill=fill,
                native_ram_writes=ranges(a for pc,a,v in native if 0x1800<=a<0x2000),
                program_writes=ranges(a for pc,a,v in c.internal_program_writes if pc>=0x6800),
                mechanical_stubs=[f'{a:04X}' for a in c.skips]))
    report=dict(static=static_inventory(),traces=cases,
        limits='Output-compare completes immediately; F2DA carriage homing stubbed; asynchronous IRQ/NMI/HALT and power retention NOT simulated. CRC validates bounded occupied records after real startup.')
    out=ROOT/'_local/development/analysis/startup-retention-audit.json'
    out.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',len(cases),'startup traces; static instructions',report['static']['instructions'])
if __name__=='__main__':main()
