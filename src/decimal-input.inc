; Offline decimal INPUT using the existing prompt and line editor.
; IVAR holds the legacy offset only until conversion to ASCII A..Z.
        ORG $A700
DECICOMMAND TST RUNNING
        BNE DECIPARSE
        JMP MODEERROR
DECIPARSE CLR ILEN
        JSR SPACE
        CMPA #34
        BNE DECIVARIABLE
        INX
        STX IPTR
DECISTRING LDAA ,X
        BEQ DECIBAD
        CMPA #34
        BEQ DECISTRINGEND
        INC ILEN
        LDAA ILEN
        CMPA #16
        BHI DECIRANGE
        INX
        BRA DECISTRING
DECISTRINGEND INX
        STX CUR
        JSR SPACE
        CMPA #59
        BNE DECIBAD
        INX
        STX CUR
DECIVARIABLE JSR VARADDR
        STAB IVAR
        JSR EOS ; Validate the whole statement before asking for a reply.
        LDAA #30
        SUBA ILEN
        STAA EDWIDTH
        JSR READINPUT
        LDX #BUF
        STX CUR
        JSR $A000 ; Decimal expression; CUR must follow the whole answer.
        STX CUR
        TSTA
        BNE DECINPUTFAIL
        JSR EOS
; EOS above validates before any allocation or write to the variable heap.
        LDAB IVAR
        LSRB
        ADDB #65
        STAB $1EC3 ; DLHS, protected from expression parser temporaries.
        LDX PEND
        INX
        STX $1EC0 ; DFLOOR = first free program byte.
        JSR $A00C
        TSTA
        BNE DECINPUTFAIL
        RTS
DECIBAD JMP SYNTAX
DECIRANGE JMP RANGEERROR
DECINPUTFAIL JMP $A518
