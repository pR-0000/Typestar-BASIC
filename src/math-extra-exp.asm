; exp(x): positive Taylor argument <=1, then repeated squaring.
; Negative arguments take the reciprocal; x<-18 underflows to zero.
XMEXP LDAA DW+8
        ANDA #$80
        STAA XMSIGN
        JSR XMABS
        LDX #XMARG
        JSR XMSAVE
        LDX #XM18
        JSR XMSUB
        TST DW+8
        BMI XMEVALID
        TST XMSIGN
        BEQ XMEBAD
        LDX #DW
        JMP SQZERO
XMEBAD JMP XMRANGE
XMEVALID LDX #XMARG
        JSR XMLOAD
        CLR XMN
XMEREDUCE LDX #XMARG
        JSR XMSAVE
        LDX #TRONE
        JSR XMSUB
        TST DW+8
        BMI XMEREADY
        LDX #XMARG
        JSR XMLOAD
        LDX #XMTWO
        JSR XMDIV
        INC XMN
        BRA XMEREDUCE
XMEREADY LDX #TRONE
        JSR XMLOAD
        LDX #XMTERM
        JSR XMSAVE
        LDX #XMSUM
        JSR XMSAVE
        LDAA #1
        STAA XMCOUNT
XMETERM LDX #XMTERM
        JSR XMLOAD
        LDX #XMARG
        JSR XMMUL
        JSR XMDIVCOUNT
        LDX #XMTERM
        JSR XMSAVE
        LDX #XMSUM
        JSR XMADD
        LDX #XMSUM
        JSR XMSAVE
        INC XMCOUNT
        LDAA XMCOUNT
        CMPA #12
        BLO XMETERM
XMESQUARE TST XMN
        BEQ XMEINVERSE
        LDX #XMSUM
        JSR XMMUL
        LDX #XMSUM
        JSR XMSAVE
        DEC XMN
        BRA XMESQUARE
XMEINVERSE TST XMSIGN
        BEQ XMERET
        LDX #TRONE
        JSR XMLOAD
        LDX #XMSUM
        JSR XMDIV
XMERET RTS
XMEXPEND EQU *
