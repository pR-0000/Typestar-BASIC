; Quoted DATA strings have literal contents, including commas and colons.
; No expression evaluation. Commit is still owned by READ after allocation.
STDAVALUE TST STDATA
        BNE STDSTRING
        LDD #BUF
        JMP DAVALUE+3
STDSTRING CMPA #34
        BNE STDBAD
        INX
        CLR STLEN
STDCOPY CPX DASTOP
        BHS STDBAD
        LDAA ,X
        INX
        CMPA #34
        BEQ STDQUOTED
        PSHX
        LDX #BUF
        LDAB STLEN
        CMPB #63
        BHS STDBAD
        ABX
        STAA ,X
        PULX
        INC STLEN
        BRA STDCOPY
STDQUOTED JSR DAWHITE
        CPX DASTOP
        BHS STDEND
        CMPA #58
        BEQ STDEND
        CMPA #44
        BNE STDBAD
        INX
        JSR DAWHITE
        CPX DASTOP
        BHS STDBAD
        CMPA #58
        BEQ STDBAD
        CMPA #44
        BEQ STDBAD
STDEND STX DATRIAL
        RTS
STDBAD JMP SYNTAX
STDATAEND EQU *
