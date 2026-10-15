; Table-driven operator recognition, longest relation spellings first.
; DPTR is untouched on return; X is the consumed end only on a match.
LXOP JSR DSPACE
        LDX #LXOPTABLE
LXTRY LDAB ,X
        BEQ LXNONE
        STAB DDIG
        INX
        STX DSTART
        LDX DPTR
        STX DCOPY
LXCHAR LDX DSTART
        LDAA ,X
        STAA DCH
        INX
        STX DSTART
        LDX DCOPY
        LDAA ,X
        JSR UPPER
        CMPA DCH
        BNE LXFAIL
        INX
        STX DCOPY
        DEC DDIG
        BNE LXCHAR
        LDX DSTART
        LDAA ,X
        LDAB 1,X
        LDX DCOPY
        RTS
LXFAIL LDX DSTART
        LDAB DDIG
        INCB
        ABX
        BRA LXTRY
LXNONE CLRA
        CLRB
        LDX DPTR
        RTS
