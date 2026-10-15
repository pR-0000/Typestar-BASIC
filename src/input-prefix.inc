; EDSHOW prefix: ordinary > or INPUT's optional (max 16-byte) prompt + ?.
; Returns X at the first editable LCD cell, without touching BUF or CUR.
IPREFIX LDX #LCDBUF
        LDAA EDWIDTH
        CMPA #31
        BNE IPQUESTION
        LDAA #62
        STAA ,X
        INX
        RTS
IPQUESTION LDAB $1B42
        BEQ IPSUFFIX
        STX HDEST
        LDX $1B40
IPCOPY LDAA ,X
        INX
        PSHX
        LDX HDEST
        STAA ,X
        INX
        STX HDEST
        PULX
        DECB
        BNE IPCOPY
        LDX HDEST
IPSUFFIX LDAA #63
        STAA ,X
        INX
        LDAA #32
        STAA ,X
        INX
        RTS
