; Numeric INPUT uses the ordinary line editor with a persistent prefix.
; Prompt text stays in program RAM; only its address/length and destination
; variable offset occupy the four spare bytes following the GOSUB frames.
IPTR EQU $1B40
ILEN EQU $1B42
IVAR EQU $1B43
KINPUT FCC "INPUT"
        FCB 0
IDISPATCH LDX #KINPUT
        JSR MATCH
        BCC ICOMMAND
        JMP TRYCURSOR
ICOMMAND TST RUNNING
        BNE IPARSE
        JMP MODEERROR
IPARSE CLR ILEN
        JSR SPACE
        CMPA #34
        BNE IVARIABLE
        INX
        STX IPTR
ISTRING LDAA ,X
        BEQ IBAD
        CMPA #34
        BEQ ISTRINGEND
        INC ILEN
        LDAA ILEN
        CMPA #16
        BHI IRANGE
        INX
        BRA ISTRING
ISTRINGEND INX
        STX CUR
        JSR SPACE
        CMPA #59
        BNE IBAD
        INX
        STX CUR
IVARIABLE JSR VARADDR
        STAB IVAR
        JSR EOS ; Validate the whole statement before asking for a reply.
        LDAA #30
        SUBA ILEN
        STAA EDWIDTH
        JSR READINPUT
        LDX #BUF
        STX CUR
        JSR EXPR ; Same integer expressions as LET, including binary literals.
        STD VALUE
        JSR EOS
        LDX #VARS
        LDAB IVAR
        ABX
        LDD VALUE
        STD ,X ; Do not change the variable on a malformed answer.
        RTS
IBAD JMP SYNTAX
IRANGE JMP RANGEERROR
