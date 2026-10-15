        ORG $A600
        JMP DNEXT
DNEXT JSR FORRUNONLY
        TST FCOUNT
        BNE DNHASFRAME
        JMP FORPAIRERROR
DNHASFRAME LDAB GCOUNT
        BEQ DNOWNFRAME
        DECB
        LDX #GCDEPTH
        ABX
        LDAA FCOUNT
        CMPA ,X
        BHI DNOWNFRAME
        JMP FORPAIRERROR ; A callee cannot consume its caller's loop.
DNOWNFRAME LDAB FCOUNT
        DECB
        LDAA #13
        MUL
        ADDD #DFRAMES
        XGDX
        STX FPTR
        LDAA ,X
        STAA FVAR
        JSR SPACE
        TSTA
        BEQ DNVALID
        JSR VARADDR
        LSRB
        ADDB #65
        CMPB FVAR
        BEQ DNVALID
        JMP FORPAIRERROR
DNVALID JSR EOS
        LDX FPTR
        INX
        JSR DFUNPACK
        LDX #DFLIMIT
        JSR DFSTASH
        LDX FPTR
        LDAB #6
        ABX
        JSR DFUNPACK
        LDX #DFSTEP
        JSR DFSTASH
; Place the step in native RHS and evaluate the current loop variable as LHS.
        LDX #$1E9D
        JSR DFSTASH
        LDAA FVAR
        STAA DFTEXT
        CLR DFTEXT+1
        LDX #DFTEXT
        JSR $A000
        TSTA
        BNE DNFAIL
        LDX #DFSTART
        JSR DFSTASH
        LDX #$1E94
        CLRA
        JSR $9C00
        TSTA
        BNE DNFAIL
; Eight-digit native arithmetic can round away an extremely small step.
; Refuse a non-progressing NEXT before changing the scalar or repeating.
        LDX #CLHS
        JSR DFSTASH
        LDX #DFSTART
        JSR DFLOAD
        LDAA #2
        STAA CMASK
        JSR CCMPVALUE
        TSTB
        BEQ DNADVANCED
        JMP RANGEERROR
DNADVANCED LDX #CLHS
        JSR DFLOAD
        JSR DFSTOREVAR
        JSR DFCOMPARE
        TSTB
        BEQ DNPOP
        LDX FPTR
        LDX 11,X
        STX RNEXT
        RTS
DNPOP DEC FCOUNT
        RTS
DNFAIL JMP $A518
