; Save SIN input/result outside the existing shared trigonometric workspace.
XMTAN LDX #XMARG
        JSR XMSAVE
        LDAB #10
        JSR TRDISPATCH
        TST DERR
        BNE XMTANERR
        LDX #XMSUM
        JSR XMSAVE
        LDX #XMARG
        JSR XMLOAD
        LDAB #11
        JSR TRDISPATCH
        TST DERR
        BNE XMTANERR
        LDX #XMARG
        JSR XMSAVE
        JSR XMABS
        LDX #XMEPS
        JSR XMSUB
        TST DW+8
        BMI XMTANRANGE
        LDX #XMSUM
        JSR XMLOAD
        LDX #XMARG
        JMP XMDIV
XMTANERR JMP XMFAIL
XMTANRANGE JMP XMRANGE
XMTANEND EQU *
