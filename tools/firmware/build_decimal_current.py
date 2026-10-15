"""Rebase decimal commands on current BASIC; CPU experiment ONLY, never flash.
Keeps validated native startup and retention byte-identical. ROM placement
9C00..ABFF is still experimental and NOT audited for printer service reuse.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[2];RESEARCH=ROOT.parents[1]/'ROMReader'
OUT=ROOT/'build/decimal-current'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    OUT.mkdir(exist_ok=True);(OUT/'validation.json').unlink(missing_ok=True)
    base=ROOT/'build/canon-basic';manifest=json.loads((base/'manifest.json').read_text())
    original=(base/'s70-basic-cpu.bin').read_bytes()
    assert sha(original)==manifest['images']['s70-basic-cpu.bin']['sha256']
    for name,digest in manifest['source_files'].items():assert sha((ROOT/name).read_bytes())==digest,name
    s=json.loads((base/'symbols.json').read_text())
    for listing in ('retention.lst','lcd-triangle.lst'):
        text=(base/listing).read_text().split('SYMBOL TABLE')[1]
        s.update({n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',text)})
    cpu=bytearray(original);modules=[];patches=[]
    def link(name,origin,text):
        source=OUT/(name+'.asm');source.write_text(text,encoding='ascii')
        binary=OUT/(name+'.bin');listing=OUT/(name+'.lst')
        r=subprocess.run([str(RESEARCH/'tmp/m680x-tools/a09.exe'),'-W','-B'+str(binary),'-L'+str(listing),str(source)],cwd=ROOT,capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        payload=binary.read_bytes();cpu[origin-0x4000:origin-0x4000+len(payload)]=payload
        modules.append(dict(name=name,origin=origin,bytes=len(payload)))
    for name,origin in [('native-decimal-reserved',0x9C00),('native-decimal-codec',0x9E00),('decimal-expressions',0xA000),('decimal-integer',0xA400)]:
        source_name='decimal-current-expressions' if name=='decimal-expressions' else name
        text=(ROOT/'src'/(source_name+'.asm')).read_text()
        if name=='decimal-expressions':text=text.replace('$1B80','$20C0').replace('$1DCB','$3800')
        link(name,origin,text)
        if name=='decimal-integer':
            # Native flag query A45E is called from the motion scheduler.
            # Keep its address and exact bytes; the converter branches over it.
            span=modules.pop()
            listing=(OUT/'decimal-integer.lst').read_text().split('SYMBOL TABLE')[1]
            head=re.search(r'\bDIHEADEND\s+[0-9A-F]{2}\s+([0-9A-F]{4})',listing)
            assert head and int(head[1],16)<=0xA45E
            assert original[0x645E:0x6467]==bytes.fromhex('7D012E27037D1DA439')
            cpu[0x645E:0x6467]=original[0x645E:0x6467]
            modules.extend([dict(name=name+'-head',origin=origin,bytes=0xA45E-origin),
                            dict(name=name+'-tail',origin=0xA467,bytes=origin+span['bytes']-0xA467)])
    equ='        OPT H01\n'+''.join(f'{name} EQU ${value:04X}\n' for name,value in s.items())
    link('bridge',0xA500,equ+(ROOT/'src/decimal-current-bridge.inc').read_text())
    link('decimal-input',0xA700,equ+(ROOT/'src/decimal-input.inc').read_text())
    # Link the next-format storage engine for placement checks, but do NOT
    # switch records while RUN/CRC/serial still use the legacy 8-bit ABI.
    from tokenized_program import WORDS
    assert WORDS[2]=='REM' and len(WORDS)<=128
    table='\nTOKENCOUNT EQU '+str(len(WORDS))+'\nTOKENPTRS\n'
    table+=''.join(f'        FDB TW{i}\n' for i in range(len(WORDS)))
    table+=''.join(f'TW{i} FCC "{word}"\n        FCB 0\n' for i,word in enumerate(WORDS))
    link('token-records',0xA800,(ROOT/'src/token-records.asm').read_text()+table)
    def patch(label,data):
        offset=s[label]-0x4000;cpu[offset:offset+len(data)]=data;patches.append((label,s[label],len(data)))
    def jump(label,target):patch(label,bytes([0x7E,target>>8,target&255]))
    jump('LET',0xA503);jump('CLEARVARS',0xA506);jump('MEMORY',0xA50C);jump('EXPR',0xA50F)
    assert original[s['PCAPOK']-0x4000:s['PCAPOK']-0x4000+3]==bytes.fromhex('BD4409')
    patch('PCAPOK',bytes.fromhex('BDA512'))
    assert original[s['PRINTNUM']-0x4000:s['PRINTNUM']-0x4000+6]==bytes([0xBD,s['EXPR']>>8,s['EXPR']&255,0xBD,s['OUTNUM']>>8,s['OUTNUM']&255])
    patch('PRINTNUM',bytes.fromhex('BDA500010101'))
    # These commands store/read legacy VARS or compare signed integer words.
    # Fail explicitly until migrated; never mix the two variable representations.
    for label in ('FORCOMMAND','NEXTCOMMAND','IF'):jump(label,0xA515)
    jump('ICOMMAND',0xA700)
    intervals=sorted((m['origin'],m['origin']+m['bytes']) for m in modules)
    assert all(b<=c for (_,b),(c,_) in zip(intervals,intervals[1:]))
    assert intervals[-1][1]<=0xAC00
    # FOR/INPUT entry hooks are in the retention allocation, but reset, CRC,
    # restore and their data remain untouched through the start of FOR dispatch.
    for a,b in ((0x6800,0x6859),(0x4400,s['FORDISPATCH'])):
        assert cpu[a-0x4000:b-0x4000]==original[a-0x4000:b-0x4000]
    assert len(cpu)==32768
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    report=dict(status='OFFLINE ONLY; not a published firmware',base_version=manifest['version'],base_sha256=sha(original),candidate_sha256=sha(cpu),modules=modules,patches=patches,program_arena=5952,retention_signature='5423',
        limits=['No NH7 image; printer dependencies of overwritten IC8 code remain unaudited.',
                'Token storage engine linked but not dispatched; current candidate still uses source/8-bit records.',
                'FOR/NEXT and IF return DECIMAL TODO until migrated.',
                'Binary literals and numeric functions not yet implemented by decimal parser.',
                'Variables cleared on RUN/NEW and successful program edits; 6 bytes per allocated scalar.'])
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
