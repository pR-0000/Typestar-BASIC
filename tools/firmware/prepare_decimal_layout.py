"""Prepare an OFFLINE decimal-engine layout experiment. Never package or flash.
Preserves the current build/release and records the Canon API sacrificed.
The boot model does not cover mechanical homing or asynchronous interrupts.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
RESEARCH=ROOT.parents[1]/'ROMReader'
sys.path.insert(0,str(RESEARCH/'tools'))
from disassemble_hd6301 import make_disassembler,absolute_target,CONDITIONAL_BRANCHES
START,END=0x9C00,0xAC00

def sha(data):return hashlib.sha256(data).hexdigest()

def original_memory():
    raw=(RESEARCH/'dumps/256ROM_NH7_1181.bin').read_bytes()
    assert sha(raw)=='5eb09f28e9e93989631544f1f13defe32679e86300702692e5c7d137f168f03c'
    mask=(RESEARCH/'dumps/dump_hd6301_v3_fast_1.bin').read_bytes()
    m=bytearray(65536);m[0x4000:0xC000]=raw[16384:]+raw[:16384];m[0xC000:]=mask
    return m

def startup_closure(m):
    md=make_disassembler();todo=[0xFFE0,0x6800];seen={};indirect=[]
    while todo:
        pc=todo.pop()
        if pc==0x6829 or pc in seen:continue
        assert 0x4000<=pc<65536,hex(pc)
        ins=next(md.disasm(bytes(m[pc:pc+4]),pc,1));seen[pc]=ins
        op=ins.mnemonic;t=absolute_target(ins)
        if op in ('jsr','bsr','jmp','bra') or op in CONDITIONAL_BRANCHES:
            if t is not None:todo.append(t)
            elif op in ('jsr','jmp'):indirect.append(f'{pc:04X}: {op} {ins.op_str}')
        if op not in ('rts','rti','jmp','bra','swi','wai','slp','fcb'):todo.append(pc+ins.size)
    hits=[]
    for pc,ins in sorted(seen.items()):
        addresses=[int(x,16) for x in re.findall(r'\$([0-9a-fA-F]+)',ins.op_str)]
        if any(START<=a<END for a in addresses) or any(START<=a<END for a in range(pc,pc+ins.size)):
            hits.append(f'{pc:04X}: {ins.mnemonic} {ins.op_str}')
    return dict(instructions=len(seen),candidate_direct_references=hits,unresolved_indirect=indirect,
                scope='Original synchronous reset closure, both conditional arms; stops at 6829; no inference for unlisted paths/IRQ/data pointers.')

def main():
    base=ROOT/'build/canon-basic';out=ROOT/'build/decimal-layout';out.mkdir(exist_ok=True)
    manifest=json.loads((base/'manifest.json').read_text());symbols=json.loads((base/'symbols.json').read_text())
    for name,digest in manifest['source_files'].items():assert sha((ROOT/name).read_bytes())==digest,name
    current=(base/'s70-basic-cpu.bin').read_bytes();assert sha(current)==manifest['images']['s70-basic-cpu.bin']['sha256']
    original=original_memory();closure=startup_closure(original)
    assert not closure['candidate_direct_references'],closure
    asm=out/'expressions-relocated.asm'
    asm.write_text('        OPT H01\n'+''.join(f'{n} EQU ${v:04X}\n' for n,v in symbols.items())+
                   f'        ORG ${START:04X}\n        INCLUDE "src/basic-expressions.inc"\n',encoding='ascii')
    subprocess.run([str(RESEARCH/'tmp/m680x-tools/a09.exe'),'-W','-B'+str(out/'expressions-relocated.bin'),
                    '-L'+str(out/'expressions-relocated.lst'),str(asm)],cwd=ROOT,check=True,capture_output=True)
    payload=(out/'expressions-relocated.bin').read_bytes();assert len(payload)<END-START
    candidate=bytearray(current)
    candidate[0x200:0x400]=bytes(0x200) # reserved area, not stale old instructions
    for offset in (0,3,6,9):
        target=START+offset;candidate[0x200+offset:0x203+offset]=bytes([0x7E,target>>8,target&255])
    candidate[START-0x4000:END-0x4000]=payload+bytes(END-START-len(payload))
    # All bytes outside the two declared experiment windows remain identical.
    assert all(a==b or 0x200<=i<0x400 or START-0x4000<=i<END-0x4000 for i,(a,b) in enumerate(zip(current,candidate)))
    (out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(candidate)
    # Deliberately no NH7 half-swapped/OneROM release file for this experiment.
    apis=[]
    for slot in list(range(0xBF2F,0xBFB4,3))+list(range(0xBFB8,0xBFE6,3)):
        assert original[slot]==0x7E
        target=original[slot+1]*256+original[slot+2]
        if START<=target<END:apis.append(dict(slot=f'{slot:04X}',target=f'{target:04X}'))
    report=dict(status='OFFLINE EXPERIMENT; NOT HARDWARE VALIDATED; NOT FOR FLASH',base_version=manifest['version'],
        base_cpu_sha256=sha(current),candidate_cpu_sha256=sha(candidate),
        reservation=dict(start=START,end_exclusive=END,capacity=END-START,payload_bytes=len(payload),
                         contiguous_remaining=END-START-len(payload)),
        old_window=dict(start=0x4200,end_exclusive=0x4400,trampoline_bytes=12,remaining=500),
        sacrificed_native_apis=apis,static_startup=closure,
        limitations=['No decimal arithmetic yet; current integer calculator relocated only.',
          'Original editor/format routines in 9C00..ABFF and listed native APIs are invalidated.',
          'Printer path, NMI/IRQ and computed/data references still require a full dependency audit.',
          'A free region in this candidate is not free in the released firmware.'])
    (out/'layout.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
