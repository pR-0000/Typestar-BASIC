; Shift+Backspace deletes the prefix, keeps the suffix and returns to column 0.
; P27 ($32 bit7) is the same Shift level used by the validated keyboard map.
; Normal Backspace and printable input rejoin their original handlers.
        ORG $9DCB
EDCLEARLEFT CMPA #8
        BNE EDCLEARPRINT
        TST $32
        BPL EDCLEARONE
        LDAA EDLEN
        SUBA EDPOS
        STAA EDLEN
        LDAB EDPOS
        CLR EDPOS
        LDX #BUF
; X is destination; B is the constant source displacement. Copy the NUL too.
EDCLEARCOPY PSHX
        ABX
        LDAA ,X
        PULX
        STAA ,X
        INX
        TSTA
        BNE EDCLEARCOPY
        JMP EDRESTORE
EDCLEARPRINT JMP EDPRINTABLE
EDCLEARONE JMP EDNOTRIGHT+4
EDCLEAREND EQU *
