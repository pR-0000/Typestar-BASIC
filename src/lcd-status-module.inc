; Preserve A/B/X and actual DDRAM address while tracking lower-bank ownership.
; Called by ICON, LCDLINE and keyboard I/II. Raw POKE bypasses this shadow.
LOWSTATUS PSHA
        PSHB
        PSHX
        PSHA
        PSHX
        PSHB
        TAB
        LDX #LOWSHADOW
        ABX
        PULB
        STAB ,X
        PULX
        JSR LCDWAIT
        LDAA $38
        ANDA #$7F
        ORAA #$80
        STAA LCDSAVED
        PULA
        ORAA #$C0
        JSR LCDCMD
        TBA
        JSR LCDDATA
        LDAA LCDSAVED
        JSR LCDCMD
        PULX
        PULB
        PULA
        RTS
