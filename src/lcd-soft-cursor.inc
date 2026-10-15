; Software cursor, only during live input. No CGRAM allocation or hardware
; blink bit: alternate the text code with a space. At blank input positions,
; show reserved CGRAM slot 7: seven full rows and a zero triangle row.
; CURSOR 0 is software; 1..3 hardware; 4 is disabled.
BLCOUNT EQU $19F8
BLPHASE EQU $19FA
BLACTIVE EQU $19FB
SOFTMODECMD JSR EXPR
        TSTA
        BNE SOFTBAD
        CMPB #4
        BHI SOFTBAD
        PSHB
        JSR EOS
        PULB
        TSTB
        BNE SOFTNATIVE
        LDAB #16
        BRA SOFTSTORE
SOFTNATIVE CMPB #4
        BNE SOFTHARDWARE
        CLRB
SOFTHARDWARE ORAB #$0C
SOFTSTORE STAB CURSORMODE
        BRA SOFTAPPLY
SOFTBAD JMP RANGEERROR
SOFTAPPLY CLR BLPHASE
        ; Show an edit marker on the first poll, then alternate every 32 scans.
        LDX #1
        STX BLCOUNT
        LDAA CURSORMODE
        CMPA #16
        BNE SOFTCONTROL
        JSR SOFTBLOCK
        LDAA #$0C
SOFTCONTROL JMP LCDCMD
SOFTTICK TST BLACTIVE
        BEQ SOFTRET
        TST HVIEW
        BNE SOFTRET
        LDAA CURSORMODE
        CMPA #16
        BNE SOFTRET
        PSHX
        LDX BLCOUNT
        DEX
        STX BLCOUNT
        BNE SOFTEND
        LDX #32
        STX BLCOUNT
        PSHB
        JSR LCDWAIT
        LDAA $38
        ANDA #$7F
        ORAA #$80
        PSHA
        LDAA EDPOS
        SUBA EDWIN
        ADDA #32
        SUBA EDWIDTH
        TAB
        ORAA #$80
        JSR LCDCMD
        LDX #LCDBUF
        ABX
        LDAA ,X
        TST BLPHASE
        BNE SOFTVISIBLE
        INC BLPHASE
        LDAA #7
        BRA SOFTWRITE
SOFTVISIBLE CLR BLPHASE
SOFTWRITE JSR LCDDATA
        PULA
        JSR LCDCMD
        PULB
SOFTEND PULX
SOFTRET RTS

; Define a known 5x7 block instead of guessing the Canon CGROM code for |.
; Slot 7 is excluded from the automatic LCDTRI/LCDLINE allocator.
SOFTBLOCK JSR LCDWAIT
        LDAA $38
        ANDA #$7F
        ORAA #$80
        PSHA
        LDAA #$78
        JSR LCDCMD
        LDAB #7
        LDAA #31
SOFTBLOCKROW JSR LCDDATA
        DECB
        BNE SOFTBLOCKROW
        CLRA
        JSR LCDDATA
        PULA
        JMP LCDCMD
