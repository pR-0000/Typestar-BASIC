; PI is a constant, not a variable or function. Preserve P/PEEK fallback.
; Reuse two unreachable parts of the retired native-font substitution.
        ORG $4934
PIENTRY LDX DPTR
        LDAA ,X
        ANDA #$DF
        CMPA #80
        BNE PIMISS
        LDAA 1,X
        ANDA #$DF
        CMPA #73
        BNE PIMISS
        INX
        INX
        STX DPTR
        JMP PIVALUE
PIMISS JMP SQENTRY
PIPARSEEND EQU *
        ORG $9015
; Eight significant digits: 3.1415927, rounded from pi.
PIVALUE LDD #DW
        STD DOUT
        LDX #PIDIGITS
        JMP SQCOPY
PIDIGITS FCB 3,1,4,1,5,9,2,7,7
PIEND EQU *
