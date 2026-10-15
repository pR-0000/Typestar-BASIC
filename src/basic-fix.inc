; FIX(x): truncate toward zero. INT keeps its existing floor semantics.
; Function id 9 is selected by the shared parser after recursive evaluation.
        ORG $8E9B
FXDISPATCH CMPB #9
        BEQ FXVALUE
        CMPB #5
        JMP NFAPPLY+2 ; replay the displaced comparison before its BCS
FXVALUE LDAA DW+8
        PSHA
        ANDA #7
        STAA DW+8
        JSR FNINT ; floor of the absolute value equals truncation
        LDX #DW
        LDAB #8
        CLRA
FXZERO ORAA ,X
        INX
        DECB
        BNE FXZERO
        TAB
        PULA
        TSTB
        BEQ FXRETURN ; zero stays unsigned
        ANDA #$80
        STAA DW+8
FXRETURN RTS
FXEND EQU *
