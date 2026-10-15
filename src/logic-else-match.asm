; Non-consuming bounded lookahead; Z=1 only for ELSE, preserving B (length).
LECHECK PSHX
        INX
        INX
        INX
        CPX LERECORDEND
        PULX
        BCC LENO
        LDAA ,X
        ANDA #$DF
        CMPA #69
        BNE LERET
        LDAA 1,X
        ANDA #$DF
        CMPA #76
        BNE LERET
        LDAA 2,X
        ANDA #$DF
        CMPA #83
        BNE LERET
        LDAA 3,X
        ANDA #$DF
        CMPA #69
LERET RTS
LENO LDAA #1
        RTS
