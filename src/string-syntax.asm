; Nondestructive type lookahead at DPTR. Carry set for a string expression.
; Every path restores X to the first non-space character except STKIND.
STISSTR JSR DSPACE
        CMPA #34
        BEQ STYES
        LDAB 1,X
        CMPB #36
        BEQ STYES
        PSHX
        JSR STKIND
        PULX
        RTS
STYES SEC
        RTS
STKIND LDD ,X
        ANDA #$DF
        ANDB #$DF
        SUBD #$4348 ; CH
        BEQ STCHR
        LDD ,X
        ANDA #$DF
        ANDB #$DF
        SUBD #$5354 ; ST
        BNE STNO
        LDAB #2
        BRA STSUFFIX
STCHR LDAB #1
STSUFFIX LDAA 2,X
        ANDA #$DF
        CMPA #82
        BNE STNO
        LDAA 3,X
        CMPA #36
        BNE STNO
        INX
        INX
        INX
        INX
        SEC
        RTS
STNO JMP STSUBKIND
STSYNTAXEND EQU *
