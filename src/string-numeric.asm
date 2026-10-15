; LEN/ASC accept concatenated string expressions. Their counters are stacked
; so STR$(LEN(...)) and LEN(STR$(...)) do not corrupt an enclosing expression.
STNUMENTRY LDX DPTR
        LDD ,X
        ANDA #$DF
        ANDB #$DF
        SUBD #$4C45
        BNE STTRYASC
        LDAA 2,X
        ANDA #$DF
        CMPA #78
        BNE STNUMOLD
        CLRB
        BRA STNUMFOUND
STTRYASC LDD ,X
        ANDA #$DF
        ANDB #$DF
        SUBD #$4153
        BNE STNUMOLD
        LDAA 2,X
        ANDA #$DF
        CMPA #67
        BNE STNUMOLD
        LDAB #1
STNUMFOUND PSHB
        LDAA STMODE
        PSHA
        LDAA STLEN
        PSHA
        LDAA STFIRST
        PSHA
        INX
        INX
        INX
        STX DPTR
        JSR DSPACE
        CMPA #40
        BNE STNUMBAD
        JSR DADVANCE
        LDAA #3
        STAA STMODE
        JSR STEXPR
        JSR DSPACE
        CMPA #41
        BNE STNUMBAD
        JSR DADVANCE
        ; Saved selector is above first/count/mode in the CPU stack.
        TSX
        LDAB 3,X
        TSTB
        BEQ STGETLEN
        TST STLEN
        BEQ STNUMRANGE
        LDAB STFIRST
        BRA STNUMVALUE
STGETLEN LDAB STLEN
STNUMVALUE CLRA
        STD DOUT
        PULA
        STAA STFIRST
        PULA
        STAA STLEN
        PULA
        STAA STMODE
        PULB
        JMP RDVALUE
STNUMOLD JMP STVALENTRY
STNUMBAD JMP SYNTAX
STNUMRANGE JMP RANGEERROR
STNUMEND EQU *
