; atan(-x)=-atan(x). Reduce to |z|<=sqrt(2)-1 before the odd series.
; Flags bit1: reciprocal, bit2: pi/4 shift. Original sign is separate.
XMATN LDAA DW+8
        ANDA #$80
        STAA XMSIGN
        JSR XMABS
        LDAA #1
        STAA XMFLAGS
        LDX #XMARG
        JSR XMSAVE
        LDX #TRONE
        JSR XMSUB
        TST DW+8
        BMI XMARESTORE
        LDX #TRONE
        JSR XMLOAD
        LDX #XMARG
        JSR XMDIV
        LDAA #3
        STAA XMFLAGS
        BRA XMATHRESH
XMARESTORE LDX #XMARG
        JSR XMLOAD
XMATHRESH LDX #XMARG
        JSR XMSAVE
        LDX #XMTHRESH
        JSR XMSUB
        TST DW+8
        BMI XMANOSHIFT
        LDAA XMFLAGS
        ORAA #4
        STAA XMFLAGS
        LDX #XMARG
        JSR XMLOAD
        LDX #TRONE
        JSR XMADD
        LDX #XMTERM
        JSR XMSAVE
        LDX #XMARG
        JSR XMLOAD
        LDX #TRONE
        JSR XMSUB
        LDX #XMTERM
        JSR XMDIV
        BRA XMASERIES
XMANOSHIFT LDX #XMARG
        JSR XMLOAD
XMASERIES JSR XMODDS
        LDAA XMFLAGS
        BITA #4
        BEQ XMAINVERSE
        LDX #XMQUARTERPI
        JSR XMADD
XMAINVERSE LDAA XMFLAGS
        BITA #2
        BEQ XMASIGN
        LDX #TRHALFPI
        JSR XMSUB
        JSR XMABS
XMASIGN LDAA DW+8
        EORA XMSIGN
        STAA DW+8
        RTS
XMATNEND EQU *
