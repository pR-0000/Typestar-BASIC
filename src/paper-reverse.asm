; .77 signed paper travel. Keep the Canon phase rings, acceleration, short
; travel counters, timer stages and power-off path. Normalize BEFORE short
; preparation, which must receive a positive magnitude even when reversing.
; Only PMFEED calls this entry. Original $7154 keeps its glyph compensation.
PRPREP LDAA #$AC
        STAA $41
        LDD $B8
        BPL PRPOSITIVE
        COMA
        COMB
        ADDD #1
        STD $B8
        OIM #$10,$41
PRPOSITIVE JSR PRSHORT
        LDX #$6EF9
        JMP $71B1
; EXPR's signed decimal flag distinguishes -1 from positive 65535. Do not
; accept a wrapped positive integer as a negative motion. PMMOVE separately
; checks that the final absolute position remains within 0..448.
PRFEED JSR EXPR
        TST DW+8
        BMI PRNEGATIVE
        SUBD #448
        BHI PRRANGE
        ADDD #448
        RTS
PRNEGATIVE SUBD #$FE40
        BCS PRRANGE
        ADDD #$FE40
        RTS
PRRANGE JMP RANGEERROR
; Only a PMMOVE transaction owns PMVALID=2. The native glyph path still needs
; its original -32/+32 compensation and the $18F7=$80 completion marker.
PRCOMPLETE LDAA PMVALID
        CMPA #2
        BEQ PRDIRECT
        LDAA #$80
        STAA $18F7
        LDD #32
        STD $B8
        JMP $7154
PRDIRECT JMP $7257
PRREVEND EQU *
