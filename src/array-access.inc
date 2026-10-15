; Decimal array access. CPU prototype, with the existing scalar/function parser.
; ARADDRESS parses name(indices) at DPTR and returns X=cell, DERR=status.
; Name and indices live on the stack while nested expressions execute; the
; shared DIMJOB is populated only after the entire subscript was evaluated.
ARATOM PSHX
        JSR DADVANCE
        JSR DSPACE
        CMPA #40
        BEQ ARISARRAY
        PULX
        STX DPTR
        JSR DSPACE
        JMP DVARIABLE
ARISARRAY PULX
        STX DPTR
ARREAD JSR ARADDRESS
        TST DERR
        BNE ARRETURN
        STX DCOPY
        LDX #DW
        LDAB #5
ARREADLOOP PSHX
        LDX DCOPY
        LDAA ,X
        INX
        STX DCOPY
        PULX
        STAA ,X
        INX
        DECB
        BNE ARREADLOOP
        LDX #DW
        JMP $9E03
ARRETURN RTS

ARADDRESS JSR DSPACE
        PSHA ; ASCII array name.
        JSR DADVANCE
        JSR DSPACE
        CMPA #40
        BEQ AROPEN
        LDAA #1
        STAA DERR
        PULA
        RTS
AROPEN JSR DADVANCE
        JSR ARINDEX
        TST DERR
        BEQ ARFIRSTOK
        PULA
        RTS
ARFIRSTOK
        PSHB
        PSHA ; index0, retained while index1 may access another array.
        JSR DSPACE
        CMPA #44
        BNE ARONE
        JSR DADVANCE
        JSR ARINDEX
        TST DERR
        BNE ARFAILFIRST
        PSHB
        PSHA
        LDAA #2
        BRA ARCLOSE
ARONE CLRA
        CLRB
        PSHB
        PSHA
        LDAA #1
ARCLOSE PSHA ; Requested rank is stacked across whitespace handling.
        JSR DSPACE
        CMPA #41
        BEQ ARCLOSED
        LDAA #1
        STAA DERR
        BRA ARPOP
ARCLOSED JSR DADVANCE
ARPOP PULA
        STAA DIMJOB+20
        PULA
        PULB
        STD DIMJOB+10
        PULA
        PULB
        STD DIMJOB+8
        PULA
        STAA DIMJOB+29
        TST DERR
        BNE ARINDEXRET ; Local RTS: do not depend on the movable read gateway.
        LDX #DIMJOB
        JSR ARRAY_NAMED_FIND
        BCS ARRANGE
        LDX DIMJOB+25
        LDAA ,X
        CMPA DIMJOB+20
        BNE ARRANGE
        LDD ,X
        STD DIMJOB
        LDD 2,X
        STD DIMJOB+2
        LDD 4,X
        STD DIMJOB+4
        LDD DIMJOB+25
        ADDD #8
        STD DIMJOB+6
        LDX #DIMJOB
        JSR ARRAY_ELEMENT
        BCS ARRANGE
        LDX 12,X
        RTS
ARFAILFIRST PULA
        PULA
ARFAILNAME PULA
        RTS
ARRANGE LDAA #4
        STAA DERR
        RTS
ARINDEX JSR DEXPR
        TST DERR
        BNE ARINDEXRET
        JSR $A400
        BCS ARRANGE
        STD DIMJOB+14
        BEQ ARINDEXRET
        TST DW+8
        BMI ARRANGE
ARINDEXRET RTS

; A006 assignment gateway: retain the legacy scalar path unchanged.
ARLET STX DPTR
        CLR DERR
        PSHX
        JSR DSPACE
        CMPA #65
        BCS ARSCALAR
        CMPA #90
        BHI ARSCALAR
        JSR DADVANCE
        JSR DSPACE
        CMPA #40
        BNE ARSCALAR
        PULX
        STX DPTR
        JSR ARADDRESS
        TST DERR
        BNE ARLETRETURN
        PSHX ; Destination survives nested RHS accesses and native arithmetic.
        JSR DSPACE
        CMPA #61
        BNE ARLETSYNTAX
        JSR DADVANCE
        JSR DEXPR
        TST DERR
        BNE ARLETDISCARD
        JSR DSPACE
        TSTA
        BNE ARLETSYNTAX
        LDX #DW
        JSR $9E00
        PULX
        STX DCOPY
        LDX #DW
        LDAB #5
ARWRITE LDAA ,X
        PSHX
        LDX DCOPY
        STAA ,X
        INX
        STX DCOPY
        PULX
        INX
        DECB
        BNE ARWRITE
        LDX #DW
        JSR $9E03
ARLETRETURN LDX DPTR
        LDAA DERR
        RTS
ARLETSYNTAX LDAA #1
        STAA DERR
ARLETDISCARD PULX
        BRA ARLETRETURN
ARSCALAR PULX
        JMP DECIMAL_LET
ARACCESSEND EQU *
