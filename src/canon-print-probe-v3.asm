; Original-Canon-context experiment: I/II prints B and submits the line.
; No second physical RETURN is needed. This does not add LPRINT to BASIC.
; Original fonts, ISR state, stack and editor RAM remain available.
        OPT H01
        ORG $67C2
PRINTPROBE JSR $69B2
        PSHA
        ANDA #$7F
        CMPA #$3A
        BEQ PROBEB
        PULA
        RTS
PROBEB  PULA
        PSHX
        LDAA #$81
        STAA $FA
        LDX #$6841 ; Same acceptance bitmap as the foreground loop.
        JSR $6875  ; Insert/process B using the real Canon dispatcher.
        PULX
        TSTB       ; Dispatcher returns B=0 on its ordinary success exit.
        BNE PROBEFAIL
        LDAA #$2D  ; Submit through the normal outer dispatcher on return.
        LDAB #$2D
        STAA $FA
        RTS
PROBEFAIL LDAA #$3D ; No-event handler; do not submit a failed insertion.
        LDAB #$3D
        STAA $FA
        RTS
PROBEEND EQU *
