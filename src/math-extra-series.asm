; Odd series: z + sign*z^3/3 + z^5/5 ... through power 17.
; XMFLAGS bit0: alternate signs (ATN) or positive terms (LOG).
; |z|<=0.414214 for ATN, <=0.2 for normalized LOG.
XMODDS LDX #XMTERM
        JSR XMSAVE
        LDX #XMSUM
        JSR XMSAVE
        LDX #XMTERM
        JSR XMMUL
        LDX #XMSQUARE
        JSR XMSAVE
        LDAA #3
        STAA XMCOUNT
XMOSLOOP LDX #XMTERM
        JSR XMLOAD
        LDX #XMSQUARE
        JSR XMMUL
        LDAA XMFLAGS
        BITA #1
        BEQ XMOSPOS
        LDAA DW+8
        EORA #$80
        STAA DW+8
XMOSPOS LDX #XMTERM
        JSR XMSAVE
        JSR XMDIVCOUNT
        LDX #XMSUM
        JSR XMADD
        LDX #XMSUM
        JSR XMSAVE
        INC XMCOUNT
        INC XMCOUNT
        LDAA XMCOUNT
        CMPA #19
        BLO XMOSLOOP
        RTS
XMODDSEND EQU *
