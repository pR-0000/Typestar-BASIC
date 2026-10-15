; Compact standard notation, e.g. SERCFG 7E1. Seven data bits unchanged.
; Framing bits from Canon B906 table: PEN=bit2, ODD=bit1, STOP2=bit0.
FRAMECFG EQU $1B8B
        ORG $8FA5
CFDISPATCH LDX #CFKEY
        JSR MATCH
        BCC CFPARSE
        JMP SBDISPATCH
CFPARSE JSR SBINACTIVE
        JSR SPACE
        CMPA #55
        BNE CFSYNTAX
        INX
        LDAA ,X
        JSR UPPER
        CLRB
        CMPA #78
        BEQ CFSTOP
        LDAB #4
        CMPA #69
        BEQ CFSTOP
        LDAB #6
        CMPA #79
        BNE CFSYNTAX
CFSTOP INX
        LDAA ,X
        SUBA #49
        CMPA #1
        BHI CFSYNTAX
        ABA
        PSHA
        INX
        STX CUR
        JSR EOS
        PULA
        STAA FRAMECFG
        RTS
CFSYNTAX JMP SYNTAX
CFKEY FCC "SERCFG"
        FCB 0
CFEND EQU *
        ORG $924D
CFBOOT JSR SBBOOT
        LDAA #4
        STAA FRAMECFG
        RTS
; Called while SCI is disabled. Preserve the proven parity and port order.
CFAPPLY LDAA FRAMECFG
        ANDA #7
        STAA $1E
        RTS
CFTAILEND EQU *
