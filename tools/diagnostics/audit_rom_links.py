"""Audit reachable direct HD6301 branches against the final ROM allocation map.

Only real entry points seed traversal. Stale labels in historical symbol maps
are deliberately not assumed executable. Indirect transfers are listed for
separate runtime coverage rather than guessed from bytes that may be data.
"""
from pathlib import Path
from collections import defaultdict
import argparse,hashlib,json,re,sys
from capstone import Cs,CS_ARCH_M680X,CS_MODE_M680X_6301

ROOT=Path(__file__).resolve().parents[2]
BRANCHES={'bcc','bcs','beq','bge','bgt','bhi','ble','bls','blt','bmi','bne','bpl','bvc','bvs','brn'}
TARGET=re.compile(r'^\$([0-9a-fA-F]{1,4})$')


def audit(image,symbols,manifest):
    memory=bytes(0x4000)+image
    decoder=Cs(CS_ARCH_M680X,CS_MODE_M680X_6301)
    owners={a:g['name'] for g in manifest['allocations'] for a in range(g['origin'],g['origin']+g['bytes'])}
    free={a for lo,hi in manifest['explicit_free_regions'] for a in range(lo,hi)}
    roots={symbols[k]:k for k in ('BOOT','READY','EXECUTE','DIRECT','KBDPOLL','KBDFAST','GETC','LCDPUT') if k in symbols}
    roots.update({row['handler']:'command '+row['name'] for row in manifest['command_dispatch']})
    # GPCALL dispatches to these three fixed Canon motor entries through X.
    # They are real callable entries, unlike nearby phase tables and stale
    # labels left over from retired BASIC implementations.
    roots.update({0x7154:'native carriage setup',0x716f:'native carriage move',
                  0x728b:'native paper move'})
    pending=list(roots);seen={};incoming=defaultdict(set);bad=[];indirect=[];mask_calls=defaultdict(set)
    while pending:
        pc=pending.pop()
        if pc in seen:continue
        if pc>=0xc000:continue # Canon services remain opaque in this IC8 audit.
        if not 0x4000<=pc<0xc000:
            bad.append(dict(pc=pc,reason='direct target outside ROM',from_pc=sorted(incoming[pc])));continue
        owner=owners.get(pc,'')
        if pc in free or owner and not owner.startswith('code-'):
            bad.append(dict(pc=pc,reason='executable target in '+(owner or 'explicit free ROM'),from_pc=sorted(incoming[pc])));continue
        ins=next(decoder.disasm(memory[pc:pc+4],pc,count=1),None)
        if ins is None or ins.mnemonic=='fcb':
            bad.append(dict(pc=pc,reason='invalid opcode',from_pc=sorted(incoming[pc])));continue
        seen[pc]=dict(size=ins.size,op=ins.mnemonic,args=ins.op_str,bytes=bytes(ins.bytes).hex())
        match=TARGET.fullmatch(ins.op_str.strip());target=int(match[1],16) if match else None
        if ins.mnemonic in BRANCHES|{'jsr','bsr','jmp','bra'}:
            if target is not None:
                incoming[target].add(pc)
                if target>=0xc000:mask_calls[target].add(pc)
                else:pending.append(target)
            elif ins.mnemonic in ('jsr','jmp'):
                indirect.append(dict(pc=pc,instruction=ins.mnemonic+' '+ins.op_str))
        if ins.mnemonic not in ('rts','rti','jmp','bra','swi','wai','slp','fcb'):
            pending.append(pc+ins.size)
    occupied={};overlaps=[]
    for pc,ins in sorted(seen.items()):
        for a in range(pc,pc+ins['size']):
            if a in occupied:overlaps.append([occupied[a],pc,a])
            occupied[a]=pc
    return dict(result='PASS' if not bad and not overlaps else 'REVIEW',
                sha256=hashlib.sha256(image).hexdigest(),roots=roots,instructions=len(seen),
                reachable_bytes=len(occupied),findings=bad,overlaps=overlaps,
                indirect=indirect,mask_services={f'{k:04X}':sorted(v) for k,v in sorted(mask_calls.items())},
                decoded={f'{k:04X}':v for k,v in sorted(seen.items())})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',default='paper-grid');args=parser.parse_args()
    folder=ROOT/'build'/args.build
    image=(folder/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    s=json.loads((folder/'symbols.json').read_text());m=json.loads((folder/'manifest.json').read_text())
    assert hashlib.sha256(image).hexdigest()==m['sha256']
    result=audit(image,s,m)
    dest=ROOT/'build'/('release-audit-'+m['version'].removesuffix('-dev'));dest.mkdir(exist_ok=True)
    (dest/'rom-links.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:v for k,v in result.items() if k not in ('decoded','roots','mask_services')})
    if result['result']!='PASS':raise SystemExit(1)


if __name__=='__main__':main()
