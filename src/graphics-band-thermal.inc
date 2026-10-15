; Raw thermal/motor calls shared by the serial graphics session. The .40
; First glyph prepares once, middle glyphs use native continuation bit40.7;
; only the last glyph runs the deceleration/output shutdown tail. No UART or
; bulk copy in the timed chain: descriptors point directly into the band.
; No assumed ready latches and no native editor/dispatcher continuations.
GPINIT CLR GPRAN
        CLR SACTIVE
        RTS
GPPRINT LDX $4E
        CPX #$6EE9
        BCS GPBADSTATE
        CPX #$6EF1
        BCC GPBADSTATE
        LDX $50
        CPX #$6EF1
        BCS GPBADSTATE
        CPX #$6EF9
        BCC GPBADSTATE
        JSR GPENABLE
        LDAA GXPRINTCOL
        INCA
        CMPA GXNX
        BEQ GPLAST
        LDAA #$80 ; Native queued-glyph continuation (73D7 -> 73E9).
        STAA $40
GPLAST EQU *
        CLR $B7
        LDAA #$42
        STAA $BC
        CLR $BD
        CLRA
        CLRB
        STD $C0
        STD $71
        STD $B8
        STD $BA
        STD $BE
        LDD #64
        STD $6F
        LDX #GPDESC
        STX $5E
        LDX #$728B
        BRA GPCALL
GPBADSTATE LDAA #4
        JMP GPABORT

; A normal width-$20 glyph advances the native carriage by 16 units.
; One full row is followed by the opposite signed move, then PAPER_FEED=56.
; AB=0 forces a complete paper stop rather than Canon's queued continuation.
; Positive 56 avoids the native small-distance (<9) acceleration underflow.
GPROW JSR GPENABLE
        LDAB GXNX
        CLRA
        ASLD
        ASLD
        ASLD
        ASLD
        COMA
        COMB
        ADDD #1
        STD $BA
        LDX #$716F
        JSR GPCALL
        JSR GPENABLE
        CLRA
        CLRB
        STD $AB
        STAA $013E
        LDD #56
        STD $B8
        LDX #$7154
        BRA GPCALL
GPENABLE LDAA #$0C
        STAA $35
        LDAA #4
        STAA $32
        CLR $40
        CLR $43
        RTS
GPCALL PSHX
        LDX #PRINT_GLYPH_COMPLETE
        STX $45
        LDAA #1
        STAA PRINT_GLYPH_BUSY
        LDD #4096
        STD GPTICKS
        PULX
        JSR PRINT_CALL_STAGE
GPLOOP JSR PRINT_REPAIR_PAPER_CONTINUATION
        TST PRINT_GLYPH_BUSY
        BEQ GPDONE
        LDX GPTICKS
        DEX
        STX GPTICKS
        BEQ GPTOOMANY
        LDX #$FFFF
GPWAIT LDAA $08
        BITA #$40
        BNE GPTICK
        DEX
        BNE GPWAIT
        LDAA #2
        BRA GPABORT
GPTICK LDX #$77EF
        JSR PRINT_CALL_STAGE
        BRA GPLOOP
GPTOOMANY LDAA #3
        BRA GPABORT
GPDONE TST $40 ; Native fast completion preserves bit7, final tail clears it.
        BMI GPKEEP
        JMP GPOFF
GPKEEP RTS
GPABORT STAA GPERROR
        JMP GXFAIL ; Session unwinds to GPSP and closes SCI/motors.
; GPDESC is in session RAM; its pointer advances through the buffered band.
