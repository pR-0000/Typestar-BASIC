; Native Canon-context buzzer API. No tone frequency control is established.
; This relocatable-by-reassembly module is NOT a standalone OneROM image.
; Requires the original periodic service 6B60 and its RAM ownership.
        OPT H01
        ORG $6000
; A=duration 2..255 Canon ticks. B=0 accepted, 1 busy, 2 invalid.
; Preserve X and original CC, including interrupt mask. A is scratch.
; Requests never replace a pending/current beep. Duration 1 is deliberately
; rejected because the original service starts and stops in the same call.
BEEP_REQUEST TAB
        TPA
        PSHA
        SEI
        TBA
        CMPA #2
        BCS BEEP_INVALID
        TST $18F6
        BNE BEEP_BUSY
        TST $18F5
        BNE BEEP_BUSY
        STAA $18F6
        INC $18F5
        CLRB
        BRA BEEP_RETURN
BEEP_BUSY LDAB #1
        BRA BEEP_RETURN
BEEP_INVALID LDAB #2
BEEP_RETURN PULA
        TAP
        RTS
; Immediate stop, preserving A/B/X/CC and all other control34 shadow bits.
; Read the software shadow, never the mixed status/strobe hardware register.
BEEP_STOP PSHA
        TPA
        PSHA
        SEI
        CLR $18F5
        CLR $18F6
        LDAA $1801
        ANDA #$BF
        STAA $1801
        STAA $34
        PULA
        TAP
        PULA
        RTS
BEEP_END EQU *
