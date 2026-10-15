; VAL converts a complete signed decimal/%binary/&Hhex literal. It does not
; evaluate BASIC statements/expressions contained in the string.
STVALENTRY LDX DPTR
        LDD ,X
        ANDA #$DF
        ANDB #$DF
        SUBD #$5641
        BNE STVALFALLBACK
        LDAA 2,X
        ANDA #$DF
        CMPA #76
        BEQ STVALOPEN
STVALFALLBACK LDX #NFTABLE
        JMP FNENTRY+3
STVALOPEN
        INX
        INX
        INX
        STX DPTR
        JSR DSPACE
        CMPA #40
        BNE STVALBAD
        JSR DADVANCE
        LDAA STMODE
        PSHA
        LDAA STLEN
        PSHA
        LDAA STFIRST
        PSHA
        LDX STDEST
        PSHX
        JSR STSCRATCH
        INX
        STX STDEST
        LDAA #4
        STAA STMODE
        JSR STEXPR
        JSR DSPACE
        CMPA #41
        BNE STVALBAD
        JSR DADVANCE
        PSHX ; Decimal argument source resumes after the closing parenthesis.
        LDX STDEST
        LDAB STLEN
        ABX
        CLR ,X
        PSHX ; Expected end: an embedded CHR$(0) is not the end of the string.
        LDX STDEST
        STX DPTR
        CLR DASIGN
        JSR DSPACE
        CMPA #45
        BNE STVALPLUS
        LDAA #$80
        STAA DASIGN
        BRA STVALSIGN
STVALPLUS CMPA #43
        BNE STVALNUMBER
STVALSIGN JSR DADVANCE
        JSR DSPACE
STVALNUMBER JSR DALITERAL
        PULX
        CPX DPTR
        BNE STVALBAD
        PULX
        STX DPTR
        PULX
        STX STDEST
        PULA
        STAA STFIRST
        PULA
        STAA STLEN
        PULA
        STAA STMODE
        DEC STDEPTH
        RTS
STVALBAD JMP SYNTAX
STVALEND EQU *
