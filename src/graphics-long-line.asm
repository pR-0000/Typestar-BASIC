; Autonomous multi-row drawing in original Canon context. One short I/II press.
; 64 rows, each submitted as B + RETURN, using the validated 4-unit feed.
; F33B runs the original double mechanism service before each RAM mutation.
; Buffer 1FC0..1FFD = 31 columns. Unconsumed bytes 1FFE/1FFF = x temp / row.
; This ownership differs from the earlier unused final blank guard word.
        OPT H01
        ORG $6300
LONG_WAIT JSR $616E       ; RAM_KEY_WAIT: native wait plus stack guard.
        PSHA
        ANDA #$7F
        CMPA #$3A
        BEQ LONG_START
        PULA
        RTS
LONG_START PULA
        PSHX
        CLR $1FFF
LONG_ROW JSR $F33B        ; Finish pending Canon requests before drawing.
        LDX #$1F58
        LDAB #8
LONG_GUARD LDAA 0,X
        CMPA #$A5
        BNE LONG_STACK
        INX
        DECB
        BNE LONG_GUARD
        JSR $6A58        ; Any queued key cancels between rows.
        TSTB
        BEQ LONG_STOP
        LDX #$1FC0
        CLRA
        LDAB #62
LONG_CLEAR STAA 0,X
        INX
        DECB
        BNE LONG_CLEAR
        LDX #$1FC0
        LDAA $1FFF
        BEQ LONG_CAP
        CMPA #63
        BEQ LONG_CAP
        LDAA #15
        LDAB #7
        JSR $600D        ; GFX_PSET, one dot in the central column.
        BRA LONG_SUBMIT
LONG_CAP LDAA #5
        STAA $1FFE
LONG_CAP_DOT LDAA $1FFE
        LDAB #7
        JSR $600D
        INC $1FFE
        LDAA $1FFE
        CMPA #26
        BNE LONG_CAP_DOT
LONG_SUBMIT LDAA #$81     ; Native B translation, same as validated probe.
        STAA $FA
        LDX #$6841
        JSR $6875
        TSTB
        BNE LONG_STOP
        LDAA #$2D        ; Actual native RETURN handler submits the row.
        STAA $FA
        LDX #$6841
        JSR $6875
        TSTB
        BNE LONG_STOP
        JSR $F33B        ; Buffer remains immutable until mechanism completes.
        INC $1FFF
        LDAA $1FFF
        CMPA #64
        BNE LONG_ROW
        LDAA #10
        LDX #LONG_DONE_TEXT
        BRA LONG_MESSAGE
LONG_STACK LDAA #11
        LDX #$6199       ; RAM_ERROR = "STACK LIMIT" in the base image.
        BRA LONG_MESSAGE
LONG_STOP JSR $F33B
        LDAA #4
        LDX #LONG_STOP_TEXT
LONG_MESSAGE JSR $DDD1
        PULX
        LDAA #$3D        ; Already handled: suppress outer-loop dispatch.
        LDAB #$3D
        STAA $FA
        RTS
LONG_DONE_TEXT FCC "64 ROWS OK"
        FCB $20
LONG_STOP_TEXT FCC "STOP"
LONG_END EQU *
