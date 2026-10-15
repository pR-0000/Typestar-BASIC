        ORG $9E80
; Copy helpers: source X, destination DFDST, byte count B. Native DW at 1E94.
DFSTASH STX DFDST
        LDX #$1E94
        LDAB #9
        BRA DFCOPY
DFLOAD LDD #$1E94
        STD DFDST
        LDAB #9
DFCOPY LDAA ,X
        INX
        STX DFSRC
        LDX DFDST
        STAA ,X
        INX
        STX DFDST
        LDX DFSRC
        DECB
        BNE DFCOPY
        RTS
DFPACK PSHX
        LDX #$1E94
        JSR $9E00
        PULX
        STX DFDST
        LDX #$1E94
        LDAB #5
        BRA DFCOPY
DFUNPACK LDD #$1E94
        STD DFDST
        LDAB #5
        JSR DFCOPY
        LDX #$1E94
        JMP $9E03
DFSTOREVAR LDAA FVAR
        STAA $1EC3
        CLR $1EA9
        JSR $A00C
        TSTA
        BEQ DFSTORERET
        JMP $A518
DFSTORERET RTS
; Compare DW against the saved limit, respecting the saved step sign.
DFCOMPARE LDX #CLHS
        JSR DFSTASH
        LDX #DFLIMIT
        JSR DFLOAD
        LDAA #3 ; <= for positive step, >= for negative step.
        TST DFSTEP+8
        BPL DFMASK
        LDAA #6
DFMASK STAA CMASK
        JMP CCMPVALUE
; Skip a zero-trip loop, nesting-aware, without executing any statement.
DFSKIP CLR DFDEPTH
        CLR DFDEPTH+1
DFSCAN LDX RNEXT
        CPX PEND
        BCS DFSREAD
        JMP FORPAIRERROR
DFSREAD STX RECORD
        JSR KBDFAST
        CMPA #3
        BNE DFSDECODE
        JMP BREAK
DFSDECODE LDX RECORD
        JSR $574C ; Skip individual statements, including same-line NEXT.
        JSR $58A1 ; Unwrap skipped IF ... THEN prefixes without evaluating them.
        LDX #KFOR
        JSR MATCH
        BCS DFSNEXT
        LDD DFDEPTH
        ADDD #1
        STD DFDEPTH
        BRA DFSCAN
DFSNEXT LDX #KNEXT
        JSR MATCH
        BCS DFSCAN
        LDD DFDEPTH
        BEQ DFSEND
        SUBD #1
        STD DFDEPTH
        BRA DFSCAN
DFSEND JSR SPACE
        TSTA
        BEQ DFSRET
        JSR VARADDR
        LSRB
        ADDB #65
        CMPB FVAR
        BEQ DFSVALID
        JMP FORPAIRERROR
DFSVALID JSR EOS
DFSRET RTS
