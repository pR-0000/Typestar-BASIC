; Byte-oriented access to the 16-bit CPU address space. No banking implied.
; Reads of I/O registers may have side effects; writes are intentionally raw.
KPEEK FCC "PEEK"
        FCB 0
KPOKE FCC "POKE"
        FCB 0
POKECMD JSR EXPR
        STD DEST
        JSR SPACE
        CMPA #44
        BNE MEMSYNTAX
        INX
        STX CUR
        JSR EXPR
        TSTA
        BNE MEMRANGE
        PSHB
        JSR EOS       ; No write until the entire statement is valid.
        PULB
        LDX DEST
        STAB ,X
        RTS
MEMSYNTAX JMP SYNTAX
MEMRANGE JMP RANGEERROR
; Nested expression evaluation uses global TOTAL/OP/SIGN. Preserve the
; outer expression, including the unary sign, around PEEK(address expr).
PEEKATOM LDD TOTAL
        PSHB
        PSHA
        LDAA OP
        PSHA
        LDAA SIGN
        PSHA
        JSR SPACE
        CMPA #40
        BNE MEMSYNTAX
        INX
        STX CUR
        JSR EXPR
        STD VALUE
        JSR SPACE
        CMPA #41
        BNE MEMSYNTAX
        INX
        STX CUR
        LDX VALUE
        LDAB ,X
        STAB TEMP
        PULA
        STAA SIGN
        PULA
        STAA OP
        PULA
        PULB
        STD TOTAL
        CLRA
        LDAB TEMP
        JMP ATOMSIGN

KABS FCC "ABS"
        FCB 0
KSGN FCC "SGN"
        FCB 0
