; Return one string atom as X -> bytes, B = explicit length. DPTR follows it.
; Views avoid a second text buffer: LPRINT can keep its 72-byte output intact.
; STR$ uses DTEXT only until the caller consumes this atom. CHR$ uses STCHAR.
STPART JSR DSPACE
        CMPA #34
        BNE STPNAME
        INX
        PSHX
        CLRB
STQUOTE LDAA ,X
        BEQ STBAD
        CMPA #34
        BEQ STQUOTED
        INCB
        CMPB #63
        BHI STLONG
        INX
        BRA STQUOTE
STQUOTED INX
        STX DPTR
        PULX
        RTS
STPNAME LDAA 1,X
        CMPA #36
        BNE STPFUNC
        LDAA ,X
        JSR UPPER
        CMPA #65
        BLO STBAD
        CMPA #90
        BHI STBAD
        ORAA #$80
        PSHA
        INX
        INX
        STX DPTR
        PULA
        JSR STFIND
        BCS STABSENT
        LDAB ,X
        INX
        RTS
STABSENT CLRB
        RTS
STBAD JMP SYNTAX
STLONG JMP RANGEERROR
; Only the exact four-character function names select a string atom.
STPFUNC JSR STKIND
        BCC STBAD
        CMPB #3
        BLO STSIMPLE
        JMP STSUB
STSIMPLE
        ; STKIND: B=1 CHR$, B=2 STR$, X points after the dollar sign.
        PSHB
        STX DPTR
        JSR DSPACE
        CMPA #40
        BNE STBAD
        JSR DADVANCE
        JSR DEXPR
        LDAA DERR
        BNE STDECFAIL
        JSR DSPACE
        CMPA #41
        BNE STBAD
        JSR DADVANCE
        PULB
        CMPB #1
        BNE STFORMAT
        JSR $A400
        BCS STLONG
        TSTA
        BNE STLONG
        STAB STCHAR
        LDX #STCHAR
        LDAB #1
        RTS
STFORMAT JSR $A003
        PSHX
        CLRB
STMEASURE TST ,X
        BEQ STMEASURED
        INCB
        INX
        BRA STMEASURE
STMEASURED PULX
        RTS
STDECFAIL JMP $A518
STVIEWEND EQU *
