"""Build an OFFLINE integrated PRINT/LET/retention candidate. Never package/flash."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib,json,re,subprocess,argparse
ROOT=Path(__file__).resolve().parents[2];RESEARCH=ROOT.parents[1]/'ROMReader'
OUT=ROOT/'build/decimal-candidate'

def assemble(source,name):
    dest=OUT/(name+'.bin');listing=OUT/(name+'.lst')
    r=subprocess.run([str(RESEARCH/'tmp/m680x-tools/a09.exe'),'-W','-B'+str(dest),
        '-L'+str(listing),str(source)],cwd=ROOT,capture_output=True,text=True)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    return dest.read_bytes(),listing.read_text()

def main():
    global OUT, ROOT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--document-ram',action='store_true',help='Offline bank-zero arena experiment, not hardware validated')
    document=parser.parse_args().document_ram
    # Keep the historical decimal experiment reproducible after the production
    # store/retention ABI changes. This is not the production build command.
    if json.loads((ROOT/'src/firmware.json').read_text())['version']!='0.4.27-dev':
        ROOT=ROOT/'tmp/pre-0.4.28'
        if not (ROOT/'build/canon-basic/manifest.json').exists():
            raise SystemExit('Historical decimal experiment requires the archived 0.4.27 baseline; use tools/firmware/build.py for current firmware.')
        OUT=ROOT/'build/decimal-candidate'
        print('Historical decimal baseline:',ROOT)

    if document:OUT=ROOT/'build/decimal-document-candidate'
    OUT.mkdir(exist_ok=True)
    (OUT/"validation.json").unlink(missing_ok=True) # Never carry a PASS across image rebuilds.
    base=ROOT/'build/canon-basic'
    original=(base/'s70-basic-cpu.bin').read_bytes()
    baseline=json.loads((base/'manifest.json').read_text())
    assert hashlib.sha256(original).hexdigest()==baseline['images']['s70-basic-cpu.bin']['sha256']
    for name,digest in baseline['source_files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, 'Baseline source changed: '+name
    old=json.loads((base/'symbols.json').read_text())
    store=(ROOT/'src/program-store.inc').read_text().replace('PROGRAMEND EQU $1EFF','PROGRAMEND EQU $1DCA')
    if document:store=store.replace('PROGRAM EQU $1B80','PROGRAM EQU $20C0').replace('PROGRAMEND EQU $1DCA','PROGRAMEND EQU $37FF')
    (OUT/'program-store.inc').write_text(store,encoding='ascii')
    source=(base/'source.asm').read_text().replace('src/program-store.inc',str((OUT/'program-store.inc').relative_to(ROOT)).replace('\\','/'))
    if document:
        # Keep entry addresses stable while lifting the old 32-line ceiling.
        source=source.replace('        CMPB #32\n        BHI BADLINE','        NOP\n        NOP\n        NOP\n        NOP')
        source=source.replace('        CMPA #33','        TSTA\n        NOP')
        local_list=(ROOT/'src/list-console.inc').read_text().replace('LDAA #32','LDAA #255',1)
        (OUT/'list-console.inc').write_text(local_list)
        source=source.replace('src/list-console.inc',str((OUT/'list-console.inc').relative_to(ROOT)).replace('\\','/'))
    main_source=OUT/'source.asm';main_source.write_text(source,encoding='ascii')
    code,listing=assemble(main_source,'main')
    symbols={n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',listing.split('SYMBOL TABLE')[1])}
    assert all(symbols[n]==v for n,v in old.items() if n not in ('PROGRAMEND','PROGRAM'))
    assert symbols['PROGRAMEND']==(0x37FF if document else 0x1DCA)
    cpu=bytearray(original);cpu[0x1000:0x1000+len(code)]=code
    equ='        OPT H01\n'+''.join(f'{n} EQU ${v:04X}\n' for n,v in symbols.items())
    modules=[]
    def link(source,name,origin):
        payload,_=assemble(source,name)
        cpu[origin-0x4000:origin-0x4000+len(payload)]=payload
        modules.append(dict(name=name,origin=origin,bytes=len(payload)))
    for name,origin in [('native-decimal-reserved',0x9C00),('native-decimal-codec',0x9E00),
                        ('decimal-expressions',0xA000),('decimal-program-crc',0xA400)]:
        module_source=ROOT/'src'/(name+'.asm')
        if document and name in ('decimal-expressions','decimal-program-crc'):
            text=module_source.read_text().replace('$1B80','$20C0').replace('$1DCA','$37FF').replace('$1DCB','$3800')
            if name=='decimal-program-crc':text=text.replace('        CMPA #32\n        BHI PC_BAD','        NOP\n        NOP\n        NOP\n        NOP')
            module_source=OUT/(name+'.asm');module_source.write_text(text)
        link(module_source,name,origin)
    bridge=OUT/'bridge.asm';bridge.write_text(equ+'        INCLUDE "src/decimal-basic-bridge.inc"\n',encoding='ascii')
    link(bridge,'bridge',0xA500)
    retention=(ROOT/'src/basic-retention.inc').read_text()
    start=retention.index('RETCRC16 LDX');end=retention.index('; Publish the signature',start)
    retention=retention[:start]+'RETCRC16 JMP $A400\n'+retention[end:]
    retention=retention.replace('$5420','$5422' if document else '$5421')
    if document:
        retention=retention.replace('RETPREP SEI','RETPREP SEI\n        CLR $36 ; Bank zero BEFORE reading retained records, even on warm reset')
        retention=retention.replace('RETNATIVE CLR $1C25','RETNATIVE JSR $A600\n        CLR $1C25')
        retention=retention.replace('        CMPA #32\n        BHI RETEMPTY','        NOP\n        NOP\n        NOP\n        NOP')
        # Canon owns header bytes; keep its descriptor table empty, so native
        # validation never interprets BASIC source as document metadata.
        header=OUT/'document-header.asm'
        header.write_text('        OPT H01\n        ORG $A600\n        CLR $36\n        LDX #$2000\nDHLOOP CLR ,X\n        INX\n        CPX #$20C0\n        BNE DHLOOP\n        RTS\n')
        link(header,'document-header',0xA600)
    retention=retention.replace('        JSR RETCRC16\n        SUBD RETEXPECT','        JSR RETCRC16\n        BCS RETNATIVE\n        SUBD RETEXPECT',1)
    # The restore path must reject malformed structure before comparing CRC.
    pos=retention.index('RETRESTORE LDAA')
    retention=retention[:pos]+retention[pos:].replace('        JSR RETCRC16\n        SUBD RETEXPECT','        JSR RETCRC16\n        BCS RETEMPTY\n        SUBD RETEXPECT',1)
    retention=retention.replace('        STX RETMAGIC\n        RTS','        STX RETMAGIC\n        JMP $A509',1)
    rsrc=OUT/'retention.asm';rsrc.write_text(equ+'        ORG $4400\n'+retention,encoding='ascii')
    link(rsrc,'retention',0x4400)
    assert modules[-1]['bytes']<=1024
    def jump(label,target):
        offset=symbols[label]-0x4000
        cpu[offset:offset+3]=bytes([0x7E,target>>8,target&255])
    jump('LET',0xA503);jump('CLEARVARS',0xA506);jump('MEMORY',0xA50C)
    if document:
        # The legacy LIST renderer only handled two digits. Keep its old
        # addresses but replace its entry with a three-digit renderer.
        list_source=OUT/'list-number.asm'
        list_source.write_text(equ+"""        ORG $A620
        LDX #LBUFFER
        LDAB LINE
        CLRA
LHUNDRED CMPB #100
        BCS LHUNDONE
        SUBB #100
        INCA
        BRA LHUNDRED
LHUNDONE TSTA
        BEQ LTENINIT
        ADDA #48
        STAA ,X
        INX
LTENINIT CLRA
LTEN CMPB #10
        BCS LTENDONE
        SUBB #10
        INCA
        BRA LTEN
LTENDONE TSTA
        BNE LTENWRITE
        CPX #LBUFFER
        BEQ LUNITS
LTENWRITE ADDA #48
        STAA ,X
        INX
LUNITS ADDB #48
        STAB ,X
        INX
        LDAA #32
        STAA ,X
        INX
        STX HDEST
        JSR SLOT
        JMP LISTCOPY
""",encoding='ascii')
        link(list_source,'list-number',0xA620)
        jump('LISTPRESENT',0xA620)

    jump('EXPR',0xA50F) # all unmigrated numeric commands fail explicitly
    offset=symbols['PRINTNUM']-0x4000
    assert cpu[offset:offset+6]==bytes([0xBD,old['EXPR']>>8,old['EXPR']&255,0xBD,old['OUTNUM']>>8,old['OUTNUM']&255])
    cpu[offset:offset+6]=bytes.fromhex('BDA500010101')
    assert len(cpu)==32768
    intervals=sorted((m['origin'],m['origin']+m['bytes']) for m in modules)
    assert all(b<=c for (_,b),(c,_) in zip(intervals,intervals[1:]))
    assert all(0x4000<=a<b<=0xC000 for a,b in intervals)
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(symbols,indent=2)+'\n')
    report=dict(status='OFFLINE ONLY: PRINT/LET/MEM/storage integration; not a release',
        base_sha256=hashlib.sha256(original).hexdigest(),candidate_sha256=hashlib.sha256(cpu).hexdigest(),
        program_arena=5952 if document else 587,retention_signature='5422' if document else '5421',modules=modules,
        limits=['No NH7 image. IC8 test placement not printer-audited.',
                'Legacy numeric commands return DECIMAL TODO, no silent integer/decimal mixing.',
                'Old 5420 retention signature intentionally rejected; migration not implemented.',
                'Published firmware and release untouched.',
                'Document option: bank-zero physical mapping unverified; serial record limits not migrated.'])
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
