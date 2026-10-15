; IF compares complete string expressions lexicographically, unsigned bytes.
; Keep two scratch views alive while nested string functions use deeper slots.
STCONDITION LDX CUR
        STX DPTR
        CLR DERR
        JSR STISSTR
        BCS STCMP
        JSR CEVAL
        JMP DCONDITION+3
STCMP JSR STCAPTURE
        PSHX
        PSHB
        JSR DSPACE
        CMPA #61
        BEQ STEQOP
        CMPA #60
        BEQ STLESSOP
        CMPA #62
        BEQ STGREATEROP
        JMP SYNTAX
STEQOP LDAB #2
        BRA STCMPMASK
STLESSOP LDAB #1
        JSR DADVANCE
        LDAA ,X
        CMPA #62
        BNE STCMPEQUAL
        LDAB #5
        BRA STCMPMASK
STGREATEROP LDAB #4
        JSR DADVANCE
        LDAA ,X
STCMPEQUAL CMPA #61
        BNE STCMPREADY
        ORAB #2
STCMPMASK JSR DADVANCE
STCMPREADY STAB CMASK
        JSR STCAPTURE
        STX STRIGHTPTR
        STAB STRIGHTLEN
        PULB
        STAB STLEFTLEN
        PULX
        STX STLEFTPTR
STCMPLOOP TST STLEFTLEN
        BEQ STLEFTEMPTY
        TST STRIGHTLEN
        BEQ STGREATER
        LDX STLEFTPTR
        LDAA ,X
        INX
        STX STLEFTPTR
        LDX STRIGHTPTR
        CMPA ,X
        BLO STLESS
        BHI STGREATER
        INX
        STX STRIGHTPTR
        DEC STLEFTLEN
        DEC STRIGHTLEN
        BRA STCMPLOOP
STLEFTEMPTY TST STRIGHTLEN
        BNE STLESS
        LDAA #2
        BRA STCMPRESULT
STLESS LDAA #1
        BRA STCMPRESULT
STGREATER LDAA #4
STCMPRESULT DEC STDEPTH
        DEC STDEPTH
        LDX DPTR
        STX CUR
        ANDA CMASK
        JMP CBOOL
STCAPTURE JSR STSCRATCH
        INX
        STX STDEST
        LDAA #4
        STAA STMODE
        JSR STEXPR
        LDX STDEST
        LDAB STLEN
        RTS
STCONDITIONEND EQU *
