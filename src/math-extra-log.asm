; Natural logarithm. Reduce x to [0.75,1.5) using powers of two, then
; ln(x)=2*(z+z^3/3+...), z=(x-1)/(x+1). Positive decimal inputs only.
XMLOG TST DW+8
        BMI XMLBAD
        JSR XMZERO
        BEQ XMLBAD
        CLR XMN
XMLNORMAL LDX #XMARG
        JSR XMSAVE
        LDX #XMLOGLOW
        JSR XMSUB
        TST DW+8
        BMI XMLSMALL
        LDX #XMARG
        JSR XMLOAD
        LDX #XMLOGHIGH
        JSR XMSUB
        TST DW+8
        BMI XMLREADY
        LDX #XMARG
        JSR XMLOAD
        LDX #XMTWO
        JSR XMDIV
        INC XMN
        BRA XMLNORMAL
XMLSMALL LDX #XMARG
        JSR XMLOAD
        LDX #XMTWO
        JSR XMMUL
        DEC XMN
        BRA XMLNORMAL
XMLBAD JMP XMRANGE
XMLREADY LDX #XMARG
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
        CLR XMFLAGS
        JSR XMODDS
        LDX #XMTWO
        JSR XMMUL
        LDAA XMN
        BEQ XMLRET
        BPL XMLPLUS
XMLMINUS LDX #XMLN2
        JSR XMSUB
        INC XMN
        BNE XMLMINUS
        RTS
XMLPLUS LDX #XMLN2
        JSR XMADD
        DEC XMN
        BNE XMLPLUS
XMLRET RTS
XMLOGEND EQU *
