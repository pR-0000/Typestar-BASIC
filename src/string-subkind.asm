; Exact case-insensitive LEFT$, RIGHT$, MID$ names. Miss leaves X unchanged.
STSUBKIND LDD ,X
        ANDA #$DF
        ANDB #$DF
        SUBD #$4C45
        BNE STKRIGHT
        LDD 2,X
        ANDA #$DF
        ANDB #$DF
        SUBD #$4654
        BNE STKMISS
        LDAA 4,X
        CMPA #36
        BNE STKMISS
        LDAB #3
        INX
        BRA STKFOUR
STKRIGHT LDD ,X
        ANDA #$DF
        ANDB #$DF
        SUBD #$5249
        BNE STKMID
        LDD 2,X
        ANDA #$DF
        ANDB #$DF
        SUBD #$4748
        BNE STKMISS
        LDAA 4,X
        ANDA #$DF
        CMPA #84
        BNE STKMISS
        LDAA 5,X
        CMPA #36
        BNE STKMISS
        LDAB #4
        INX
        INX
        BRA STKFOUR
STKMID LDD ,X
        ANDA #$DF
        ANDB #$DF
        SUBD #$4D49
        BNE STKMISS
        LDAA 2,X
        ANDA #$DF
        CMPA #68
        BNE STKMISS
        LDAA 3,X
        CMPA #36
        BNE STKMISS
        LDAB #5
STKFOUR INX
        INX
        INX
        INX
        SEC
        RTS
STKMISS CLC
        RTS
STSUBKINDEND EQU *
