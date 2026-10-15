; PSET x,y[,size]: a square brush in the same logical units as LINE.
; Size defaults to one. A zero-length LINE shares the validated rasterizer,
; clipping rules and eight-byte scene record, with no additional RAM state.
; Even brush sizes extend one more coordinate towards the positive side.
; Evaluate all expressions and EOS before SHLINE can allocate/append/print.
PTDISPATCH LDX #PTNAME
        JSR MATCH
        BCC PTPARSE
        JMP CCDISPATCH
PTNAME FCC "PSET"
        FCB 0
PTPARSE CLR PXINDEX
PTARG JSR EXPR
        TSTA
        BNE PTBAD
        TST DW+8
        BMI PTBAD
        PSHB
        LDX #PXSTATE
        LDAB PXINDEX
        ABX
        PULB
        STAB ,X
        INC PXINDEX
        LDAA PXINDEX
        CMPA #2
        BEQ PTOPTION
        JSR PTCOMMA
        BRA PTARG
PTOPTION LDAA #1
        STAA PXSTATE+4
        JSR SPACE
        CMPA #44
        BNE PTREADY
        INX
        STX CUR
        JSR EXPR
        TSTA
        BNE PTBAD
        TST DW+8
        BMI PTBAD
        STAB PXSTATE+4
PTREADY LDD PXSTATE
        STD PXSTATE+2
        ; LNCHECK validates EOS, X<=247 and size 1..16 before committing.
        JMP LNCHECK
PTCOMMA JSR SPACE
        CMPA #44
        BNE PTSYNTAX
        INX
        STX CUR
        RTS
PTBAD JMP RANGEERROR
PTSYNTAX JMP SYNTAX
PTEND EQU *
