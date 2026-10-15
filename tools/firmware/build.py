"""Build HD6301 code and package a 32 KiB NH7 image. No flashing."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def half_swap(data):
    if len(data) != 32768:
        raise ValueError('NH7 image must be exactly 32768 bytes')
    return data[16384:] + data[:16384]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--a09', type=Path, default=ROOT.parents[1] / 'ROMReader/tmp/m680x-tools/a09.exe')
    parser.add_argument('--profile', choices=('basic', 'lcd-only', 'canon-basic'), default='canon-basic')
    args = parser.parse_args()
    out = ROOT / 'build' if args.profile == 'basic' else ROOT / 'build' / args.profile
    out.mkdir(exist_ok=True, parents=True)
    source = ROOT / 'src/basic.asm'
    identity = json.loads((ROOT / 'src/firmware.json').read_text(encoding='ascii'))
    banner = identity['name'] + ' ' + identity['version']
    if args.profile == 'canon-basic':
        text = source.read_text().replace('ORG $6800', 'ORG $5000').replace('S70 BASIC 0.2.2 / LCD KBD SERIAL', banner)
        text = text.replace('S70 BASIC 0.3E / LCD KBD SERIAL', 'S70 BASIC 0.3E')
        text = text.replace('src/keymaps.inc', 'src/keymaps-canon.inc')
        text = text.replace('BARELET JMP LET', '''BARELET LDX #KICON
        JSR MATCH
        BCS ICONLET
        JMP ICON
ICONLET JMP LET''')
        text = text.replace('CODEEND EQU', '        INCLUDE "src/lcd-indicators.inc"\nCODEEND EQU')
        start, end = text.index('BOOT    SEI'), text.index('READY   LDS')
        text = text[:start] + '''BOOT    SEI
        LDS #$1FFF
        JSR $4403
        JSR CONSOLEATTACH
        JSR CLEARVARS
        LDX #BANNER
        JSR PUTS
''' + text[end:]
        start, end = text.index('PUTC    PSHA'), text.index('PUTS    LDAA')
        text = text[:start] + '''; Transitional local console: do not reconfigure Canon ports or SCI.
PUTC    PSHA
        PSHB
        PSHX
        PSHA
        LDAA #1
        STAA OUTFLAG
        PULA
        JSR LCDPUT
        PULX
        PULB
        PULA
        RTS
GETC    JSR $4812
        JSR POLLIN
        TSTA
        BNE GETCRET
        TST BOOTFLAG
        BEQ GETC
        LDAA $32
        ANDA #$80
        CMPA WAITSHIFT
        BEQ GETC
        STAA WAITSHIFT
        TSTA
        BEQ GETC
BOOTKEY LDAA #13
GETCRET EQU *
        RTS
POLLIN  JMP KBDPOLL
''' + text[end:]
        text = text.replace('ERROR   LDS #$1FFF\n        JSR PUTS\n        JMP READY', 'ERROR   JMP ERRORWAIT')
        text = text.replace('BARELET LDX #KICON', """BARELET LDX #KMEM
        JSR MATCH
        BCS TRYSAVE
        JMP MEMORY
TRYSAVE LDX #KSAVE
        JSR MATCH
        BCS TRYLOAD
        JMP SAVECMD
TRYLOAD LDX #KLOAD
        JSR MATCH
        BCS TRYICON
        JMP LOAD
TRYICON LDX #KICON""")
        text = text.replace('CODEEND EQU', '        INCLUDE "src/basic-services.inc"\n        INCLUDE "src/basic-serial.inc"\nCODEEND EQU')
        start, end = text.index('EXPR    JSR ATOM'), text.index('ATOM    CLR SIGN')
        text = text[:start] + 'EXPR    JMP $4200\n' + text[end:]
        text = text.replace('ATOMBODY CMPA #$30', 'ATOMBODY CMPA #40\n        BNE ATOMBASE\n        JMP $4203\nATOMBASE CMPA #$30')
        text = text.replace('IF      JSR EXPR', 'IF      JSR $4818 ; Signed relational condition, or legacy nonzero expression')
        text = text.replace('        CLR RUNNING\nEXECRET', '        CLR RUNNING\n        CLR $1974\n        CLR $197F\nEXECRET')
        text = text.replace('RUNRET  RTS', 'RUNRET  JMP $440F')
        # Find the next occupied number directly; preserve its text pointer
        # across the nonblocking keyboard scan instead of looking it up twice.
        start, end = text.index('RUNNEXT JSR POLLIN'), text.index('GOTO    JSR EXPR')
        text = text[:start] + """RUNNEXT JSR $4418
        BCS RUNSTOP
        STX CUR
        JSR KBDFAST
        CMPA #3
        BNE RUNEXEC
        JMP BREAK
RUNEXEC JSR EXECUTE
        TST RUNNING
        BEQ RUNRET
        INC LINE
        BNE RUNNEXT
RUNSTOP CLR RUNNING
RUNRET  JMP $440F
""" + text[end:]

        text = text.replace('; 32 fixed slots of 64 bytes; source line number 1..32 maps to slot.', '; Compact records: line number 1..255 followed by NUL-terminated source.')
        text = text.replace('        CMPB #32\n        BHI BADLINE\n', '')
        text = text.replace('        CMPA #33\n        BNE RUNNEXT', '        BNE RUNNEXT')
        text = text.replace('PROGRAM EQU $1000', '; Program arena defined in program-store.inc')
        start, end = text.index('        JSR SLOT\n        STX DEST'), text.index('DIRECT  JSR EXECUTE')
        text = text[:start] + '        JSR STORELINE\n        BRA READY\n' + text[end:]
        start, end = text.index('SLOT    LDAB LINE'), text.index('CLEARVARS LDX')
        text = text[:start] + '        INCLUDE "src/program-store.inc"\n' + text[end:]
        text = text.replace('        JSR PUTS\nREADY', '''        JSR PUTS
BOOTWAIT JSR GETC
; Two explicit acknowledgements, no artificial delay. PEND was rebuilt by
; retention: report remaining record bytes, exactly as MEM does.
        LDD #PROGRAMEND
        SUBD PEND
        JSR OUTNUM
        LDX #MEMTEXT
        JSR PUTS
        JSR GETC
        CLR BOOTFLAG
READY''',1)
        text = text.replace('        LDX #PROMPT\n        JSR PUTS\n        JSR READLINE', '        JSR READLINE',1)
        text = text.replace('READY   LDS #$1FFF', 'READY   LDS #$1FFF\n        CLR OUTFLAG')
        text = text.replace('DIRECT  JSR EXECUTE\n        BRA READY', 'DIRECT  JSR EXECUTE\n        JSR RESULTWAIT\n        BRA READY')
        text = text.replace('CLEARVARS LDX', 'CLEARVARS CLR $1974\n        CLR $197F\n        LDX')
        text = text.replace('RUN     JSR DIRECTONLY', 'RUN     JSR DIRECTONLY\n        INC OUTFLAG')
        text = text.replace('BARELET LDX #KMEM', 'BARELET LDX #KPOKE\n        JSR MATCH\n        BCS TRYMEM\n        JMP POKECMD\nTRYMEM LDX #KMEM')
        text = text.replace('BARELET LDX #KPOKE', 'BARELET LDX #KCURSOR\n        JSR MATCH\n        BCS TRYPOKE\n        JMP CURSORCMD\nTRYPOKE LDX #KPOKE')
        text = text.replace('ATOMBASE CMPA #$30', 'ATOMBASE CMPA #37\n        BNE ATOMDECIMAL\n        JMP $4803\nATOMDECIMAL CMPA #$30')
        text = text.replace('ATOMVAR JSR VARADDR', 'ATOMVAR LDX #KPEEK\n        JSR MATCH\n        BCS ATOMPLAIN\n        JMP PEEKATOM\nATOMPLAIN JSR VARADDR')
        text = text.replace('ATOMPLAIN JSR VARADDR', """ATOMPLAIN LDX #KABS
        JSR MATCH
        BCC ABSATOM
        LDX #KSGN
        JSR MATCH
        BCS SCALARATOM
        LDAB #1
        JMP $4209
ABSATOM CLRB
        JMP $4209
SCALARATOM JSR VARADDR""")
        text = text.replace('CODEEND EQU', '        INCLUDE "src/basic-memory.inc"\nCODEEND EQU')
        text = text.replace('BARELET LDX #KCURSOR', 'BARELET JMP $4800\nTRYCURSOR LDX #KCURSOR')

        text = text.replace('PROMPT  FCC "READY> "', 'PROMPT  FCC ">"')
        start, end = text.index('LIST    JSR'), text.index('RUN     JSR')
        text = text[:start] + '        INCLUDE "src/list-console.inc"\n' + text[end:]
        start, end = text.index('READLINE LDX'), text.index('; Whitespace and keyword matching.')
        text = text[:start] + '        INCLUDE "src/console-editor.inc"\n' + text[end:]
        text = text.replace('        JSR CLEARVARS\n        LDX #BANNER', '        JSR CLEARVARS\n        JSR UIINIT\n        LDX #BANNER',1)
        # KEYS remains local; it can be exited using the raw break key.
        text = text.replace('INCLUDE "src/console.inc"', 'INCLUDE "src/console-canon.inc"')
        console = (ROOT / 'src/console.inc').read_text()
        console = console.replace('LCDBUF  EQU', 'KMODE   EQU $199F ; BASIC-owned I=0 / II=1, independent of Canon RAM\nLCDBUF  EQU')
        console = console.replace('        CLR LCDOK', '        CLR LCDOK\n        CLR KMODE ; Start in keyboard I at every BASIC boot', 1)
        console = console.replace('KBDNOTBREAK CMPA #$2C', '''; Original dispatch: $6849 + ($3A-$2C)*2 = $6865 -> $EE58.
; Canon $EE58 toggles $1805 bit 0. Keep our mode outside CLEARALL RAM.
; Debouncing above ensures a held I/II key toggles only once.
KBDNOTBREAK CMPA #$3A
        BNE KBDNOTMODE
        LDAA KMODE
        EORA #1
        STAA KMODE
        JSR LCDMODE
        BRA KBDNONE
KBDNOTMODE CMPA #$2C''')
        console = console.replace('KBDLOOKUP LDAA ,X', '''KBDLOOKUP TST KMODE
        BEQ KBDMODELOOKUP
        LDAB #88 ; Each I/II set contains 44 plain + 44 shifted entries.
        ABX
KBDMODELOOKUP LDAA ,X''')
        console = console.replace('KBREAK  EQU $3C', 'KBREAK  EQU $36')
        console = console.replace('        STAA KHELD\n        CMPA #$FF', '        STAA KHELD\n        CMPA #$FF\n        BEQ KBDNONE\n        TST BOOTFLAG\n        BEQ KBDPASTBOOT\n        LDAA #13\n        JMP KBDRETURN\nKBDPASTBOOT CMPA #$FF')
        console = console.replace('KBDNOTMODE CMPA #$2C', """KBDNOTMODE CMPA #$31
        BNE UINOTLEFT
        LDAA #$12
        BRA KBDRETURN
UINOTLEFT CMPA #$32
        BNE UINOTRIGHT
        LDAA #$13
        BRA KBDRETURN
UINOTRIGHT CMPA #$38
        BNE UINOTOLDER
        LDAA #$14
        BRA KBDRETURN
UINOTOLDER CMPA #$39
        BNE UINOTNEWER
        LDAA #$15
        BRA KBDRETURN
UINOTNEWER CMPA #$2C""")
        console = console.replace('        LDAA #32\nLCDNOTCR', '        JSR HISTSAVE\n        INC UIPENDING\n        RTS\nLCDNOTCR',1)
        console = console.replace('        PSHA\n        LDAA LCDPOS', '        PSHA\n        TST UIPENDING\n        BEQ UINOCLEAR\n        JSR UICLEAR\nUINOCLEAR LDAA LCDPOS',1)
        start, end = console.index('        LDX #LCDBUF\nLCDSCROLL'), console.index('LCDPLACE LDAB')
        console = console[:start] + '        JSR HISTSAVE\n        JSR UICLEAR\n' + console[end:]
        console = console.replace('CONSOLEINIT CLR LCDPOS' , 'CONSOLEATTACH CLR LCDPOS')
        start, end = console.index('        ; Long initial wait'), console.index('LCDDELAY PSHX')
        console = console[:start] + '        INC LCDOK\n        JSR LCDMODE\n        RTS\n' + console[end:]
        start, end = console.index('KEYDIAGLOOP LDAA'), console.index('KEYDIAGSCAN JSR')
        console = console[:start] + 'KEYDIAGLOOP\n' + console[end:]
        console = console.replace('        BRA KBDNONE', '        JMP KBDNONE')
        for i in range(console.count('        BEQ KBDNONE')):
            console = console.replace('        BEQ KBDNONE', f'        BNE KBDCONT{i}\n        JMP KBDNONE\nKBDCONT{i} EQU *', 1)
        generated_console = out / 'console-canon.inc'
        generated_console.write_text(console, encoding='ascii')
        text = text.replace('src/console-canon.inc', str(generated_console.relative_to(ROOT)).replace('\\', '/'))
        text = text.replace('        JSR UIINIT', '        JSR UIINIT\n        JSR $4806',1)
        source = out / 'source.asm'
        source.write_text(text, encoding='ascii')
    if args.profile == 'lcd-only':
        text = source.read_text()
        start, end = text.index('BOOT    SEI'), text.index('READY   LDS')
        text = text[:start] + (ROOT / 'src/lcd-diagnostic.inc').read_text() + '\n' + text[end:]
        source = out / 'diagnostic.asm'
        source.write_text(text, encoding='ascii')
    # This assembler interprets forward slashes as options on Windows.
    result = subprocess.run([str(args.a09.resolve()), '-W',
                             '-B'+str((out / 'basic.bin').relative_to(ROOT)),
                             '-L'+str((out / 'basic.lst').relative_to(ROOT)),
                             str(source.relative_to(ROOT))], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    listing = (out / 'basic.lst').read_text()
    if not re.search(r'\b0 error\(s\)', listing):
        raise SystemExit('Assembler listing contains errors')
    symbols = {name: int(value, 16) for name, value in
               re.findall(r'\b([A-Z][A-Z0-9]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',
                          listing.split('SYMBOL TABLE')[1])}
    code = (out / 'basic.bin').read_bytes()
    origin = 0x5000 if args.profile == 'canon-basic' else 0x6800
    assert symbols['BOOT'] == origin
    assert symbols['CODEEND'] == origin + len(code) <= (0x67C2 if args.profile == 'canon-basic' else 0xBF2F)
    cpu = bytearray([0xFF] * 32768)
    cpu[origin-0x4000:origin-0x4000 + len(code)] = code
    jump = bytes([0x7E]) + symbols['TRAP'].to_bytes(2, 'big')
    slots = list(range(0xBF2F, 0xBFB6, 3)) + list(range(0xBFB8, 0xBFE8, 3))
    slots += list(range(0xBFEC, 0xBFFC, 3))
    for address in slots:
        cpu[address - 0x4000:address - 0x4000 + 3] = jump
    cpu[0x7FB6:0x7FB8] = b'\x40\x00'
    if args.profile == 'canon-basic':
        original = (ROOT.parents[1] / 'ROMReader/dumps/256ROM_NH7_1181.bin').read_bytes()
        assert hashlib.sha256(original).hexdigest() == '5eb09f28e9e93989631544f1f13defe32679e86300702692e5c7d137f168f03c'
        original_cpu = half_swap(original)
        cpu = bytearray(original_cpu)
        cpu[0x1000:0x1000+len(code)] = code
        # A separately linked module in repurposed font data. Main entry and
        # the protected $67C2 boundary stay unchanged. No banking is involved.
        expr_source = out/'expressions.asm'
        expr_source.write_text('        OPT H01\n' + ''.join(
            f'{name} EQU ${value:04X}\n' for name,value in symbols.items()) +
            '        ORG $4200\n        INCLUDE "src/basic-expressions.inc"\n', encoding='ascii')
        result = subprocess.run([str(args.a09.resolve()), '-W',
            '-B'+str((out/'expressions.bin').relative_to(ROOT)),
            '-L'+str((out/'expressions.lst').relative_to(ROOT)),
            str(expr_source.relative_to(ROOT))], cwd=ROOT, capture_output=True, text=True)
        if result.returncode: raise SystemExit(result.stdout + result.stderr)
        expressions = (out/'expressions.bin').read_bytes()
        assert 0 < len(expressions) <= 0x200
        cpu[0x200:0x200+len(expressions)] = expressions
        module_source = out/'lcd-triangle.asm'
        module_source.write_text('        OPT H01\n' + ''.join(
            f'{name} EQU ${value:04X}\n' for name,value in symbols.items()) +
            '        ORG $4800\n        INCLUDE "src/lcd-triangle.inc"\n', encoding='ascii')
        result = subprocess.run([str(args.a09.resolve()), '-W',
            '-B'+str((out/'lcd-triangle.bin').relative_to(ROOT)),
            '-L'+str((out/'lcd-triangle.lst').relative_to(ROOT)),
            str(module_source.relative_to(ROOT))], cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise SystemExit(result.stdout + result.stderr)
        module = (out/'lcd-triangle.bin').read_bytes()
        assert 0 < len(module) <= 0x800
        cpu[0x800:0x800+len(module)] = module
        retention_source = out/'retention.asm'
        retention_source.write_text('        OPT H01\n' + ''.join(
            f'{name} EQU ${value:04X}\n' for name,value in symbols.items()) +
            '        ORG $4400\n        INCLUDE "src/basic-retention.inc"\n', encoding='ascii')
        result = subprocess.run([str(args.a09.resolve()), '-W',
            '-B'+str((out/'retention.bin').relative_to(ROOT)),
            '-L'+str((out/'retention.lst').relative_to(ROOT)),
            str(retention_source.relative_to(ROOT))], cwd=ROOT, capture_output=True, text=True)
        if result.returncode: raise SystemExit(result.stdout + result.stderr)
        retention = (out/'retention.bin').read_bytes()
        assert len(retention) <= 0x400
        cpu[0x400:0x400+len(retention)] = retention
        # Replay the six displaced entry bytes in RETPREP after protection.
        assert original_cpu[0x2800:0x2806] == bytes.fromhex('860497359732')
        cpu[0x2800:0x2806] = bytes.fromhex('7E4400010101')
        # Immediate handoff; preserve upstream Canon hardware startup.
        result = subprocess.run([str(args.a09.resolve()), '-W',
                                 '-B'+str((out/'hook.bin').relative_to(ROOT)),
                                 '-L'+str((out/'hook.lst').relative_to(ROOT)),
                                 'src\\canon-basic-hook.asm'], cwd=ROOT, capture_output=True, text=True)
        hook_listing = (out/'hook.lst').read_text()
        assert result.returncode == 0 and re.search(r'\b0 error\(s\)', hook_listing), hook_listing
        hook = (out/'hook.bin').read_bytes()
        assert len(hook) == 0x6859-0x6829
        cpu[0x2829:0x2829+len(hook)] = hook
        assert len(cpu) == 32768
        assert cpu[0x2806:0x2829] == original_cpu[0x2806:0x2829]
        assert cpu[0x2859:] == original_cpu[0x2859:]
    raw = half_swap(cpu)
    assert half_swap(raw) == cpu
    manifest = {'status': 'experimental-not-hardware-validated', 'entry': '0x6800',
                'code_bytes': len(code), 'assembler_sha256': hashlib.sha256(args.a09.read_bytes()).hexdigest(),
                'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'images': {}}
    manifest['version'] = identity['version'] if args.profile == 'canon-basic' else '0.2.2'
    manifest['name'] = identity['name'] if args.profile == 'canon-basic' else 'S70 BASIC legacy'
    manifest['dialect'] = identity['dialect']
    manifest['profile'] = args.profile
    if args.profile == 'canon-basic':
        manifest['entry'] = 'Canon $6800; BASIC takeover $5000'
        manifest['original_sha256'] = hashlib.sha256(original).hexdigest()
        manifest['replaced_cpu_regions'] = [[hex(0x5000), hex(origin+len(code)-1)], ['0x6829','0x6858']]
        manifest['modules'] = [{'name':'expressions','origin':0x4200,'bytes':len(expressions)}, {'name':'lcd-triangle','origin':0x4800,'bytes':len(module)}, {'name':'retention','origin':0x4400,'bytes':len(retention)}]
        manifest['replaced_cpu_regions'] += [['0x4200',hex(0x4200+len(expressions)-1)], ['0x4400',hex(0x4400+len(retention)-1)], ['0x6800','0x6805']]
        manifest['replaced_cpu_regions'].append(['0x4800',hex(0x4800+len(module)-1)])
        manifest['limitations'] = 'Printer font data repurposed; native startup retained after early protection trampoline; bounded cold-settings path forced; see startup-retention audit and hardware limits. Hardware trial required. No serial console.'
    manifest['source_files'] = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in sorted((ROOT / 'src').glob('*')) if path.is_file()}
    manifest['console'] = ('keyboard + 32-character LCD + optional polling serial 1200/8N1'
                           if args.profile == 'basic' else 'LCD-only animated diagnostic, no BASIC execution')
    if args.profile == 'canon-basic':
        manifest['console'] = 'Keyboard/LCD console; SAVE/LOAD 1200/7E1 validated on S-70 in 0.4.9; global IRQ masked; PEEK/POKE and startup validated in 0.4.10; LCD triangle mapping confirmed in 0.4.11; text/triangle composition validated in 0.4.13; LCDLINE validated in 0.4.14; full-height composition font and CLS validated in 0.4.15; BEEP/SOUND validated in 0.4.16; 60..750 Hz nominal modulation available; SOUND timing validated in 0.4.19; software block cursor mode 0 and CRC-checked RAM retention validated in 0.4.20; history keys 38/39 and signed IF comparisons added in 0.4.21'
    for name, data in [('s70-basic-cpu.bin', cpu), ('s70-basic-nh7.bin', raw)]:
        (out / name).write_bytes(data)
        manifest['images'][name] = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    (out / 'symbols.json').write_text(json.dumps(symbols, indent=2) + '\n')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    if args.profile == 'canon-basic':
        subprocess.run([sys.executable, str(ROOT/'tools/firmware/update_firmware_status.py')], check=True)
    print(f'Built {len(code)} bytes of HD6301 code; two 32768-byte images in {out}')


if __name__ == '__main__':
    main()
