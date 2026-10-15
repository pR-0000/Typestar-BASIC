; Autonomous multi-row drawing in original Canon context. One short I/II press.
; 64 rows from a ROM bitmap: circle, diamond and crossed diagonals.
; Each row uses B + RETURN and the validated 4-unit feed.
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
        ; Each row is a 32-bit ROM bitmap, MSB first; column 31 is blank.
        ; Reconstruct the 31-unit Canon buffer using the native point routine.
        LDX #XY_BITMAP
        LDAB $1FFF
        ASLB
        ASLB
        ABX
        CLR $1FFE        ; Current horizontal coordinate, independent of row.
XY_BYTE LDAA 0,X
        LDAB #8
XY_BIT  ASLA
        BCC XY_SKIP
        PSHA             ; PSET may destroy A/B; preserve bitmap and counter.
        PSHB
        PSHX
        LDAA $1FFE
        LDAB #7          ; Same physical head channel as the validated line.
        LDX #$1FC0
        JSR $600D
        PULX
        PULB
        PULA
XY_SKIP INC $1FFE
        DECB
        BNE XY_BIT
        INX
        LDAB $1FFE
        CMPB #32
        BNE XY_BYTE
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
LONG_DONE_TEXT FCC "XY ROWS OK"
        FCB $20
LONG_STOP_TEXT FCC "STOP"
        INCLUDE "build/xy-drawing/bitmap.inc"
LONG_END EQU *
