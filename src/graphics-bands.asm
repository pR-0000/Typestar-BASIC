; Four full-height bands: circle, diamond, then a two-band rectangle.
; One short I/II press; original Canon completion service before RAM writes.
; Paper RETURN requests 64 units: nominally 16 times the validated fine step.
        OPT H01
        ORG $6300
BANDS_WAIT JSR $616E       ; RAM_KEY_WAIT: native wait plus stack guard.
        PSHA
        ANDA #$7F
        CMPA #$3A
        BEQ BANDS_START
        PULA
        RTS
BANDS_START PULA
        PSHX
        CLR $1FFF
BANDS_ROW JSR $F33B        ; Finish pending Canon requests before drawing.
        LDX #$1F58
        LDAB #8
BANDS_GUARD LDAA 0,X
        CMPA #$A5
        BNE BANDS_STACK
        INX
        DECB
        BNE BANDS_GUARD
        JSR $6A58        ; Any queued key cancels between rows.
        TSTB
        BEQ BANDS_STOP
        ; Four pre-encoded bands, 62 bytes each, all 16 head channels.
        ; Last two RAM bytes remain metadata, never part of the glyph.
        LDX #BAND_DATA
        LDAA #62
        LDAB $1FFF
        MUL              ; offsets 0,62,124,186 fit B; A is zero.
        ABX
        CLRB
BAND_COPY LDAA 0,X
        PSHX
        LDX #$1FC0
        ABX
        STAA 0,X
        PULX
        INX
        INCB
        CMPB #62
        BNE BAND_COPY
BANDS_SUBMIT LDAA #$81     ; Native B translation, same as validated probe.
        STAA $FA
        LDX #$6841
        JSR $6875
        TSTB
        BNE BANDS_STOP
        LDAA #$2D        ; Actual native RETURN handler submits the row.
        STAA $FA
        LDX #$6841
        JSR $6875
        TSTB
        BNE BANDS_STOP
        JSR $F33B        ; Buffer remains immutable until mechanism completes.
        INC $1FFF
        LDAA $1FFF
        CMPA #4
        BNE BANDS_ROW
        LDAA #10
        LDX #BANDS_DONE_TEXT
        BRA BANDS_MESSAGE
BANDS_STACK LDAA #11
        LDX #$6199       ; RAM_ERROR = "STACK LIMIT" in the base image.
        BRA BANDS_MESSAGE
BANDS_STOP JSR $F33B
        LDAA #4
        LDX #BANDS_STOP_TEXT
BANDS_MESSAGE JSR $DDD1
        PULX
        LDAA #$3D        ; Already handled: suppress outer-loop dispatch.
        LDAB #$3D
        STAA $FA
        RTS
BANDS_DONE_TEXT FCC "4 BANDS OK"
        FCB $20
BANDS_STOP_TEXT FCC "STOP"
        INCLUDE "build/bands/bands.inc"
BANDS_END EQU *
