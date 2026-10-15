; Text-only paper pitch; graphics and raw FEED units remain unchanged.
; Persistent byte between serial framing ($1B8B) and INKEY ($1B90).
LSPITCH EQU $1B8C
SPENTRY JSR MCFREE
        JSR SPACE
        INX
        LDAB #112
        CMPA #'2'
        BEQ SPEND
        CMPA #'1'
        BNE SPBAD
        LDAB #56
        LDAA ,X
        CMPA #'.'
        BNE SPEND
        INX
        LDAA ,X
        INX
        CMPA #'5'
        BNE SPBAD
        LDAB #84
SPEND STX CUR
        JSR EOS
        ; A changed pitch starts a fresh text/graphics origin at this position.
        STAB LSPITCH
        JMP PMORIGIN
SPBAD JMP RANGEERROR
; @island boot
SPBOOT LDAA #84
        STAA LSPITCH
        JMP MOTORBOOT
; @island multiply
SPMUL LDAA LSPITCH
        MUL
        RTS
; @island feed
; GPROW has already cleared A; preserve it and choose only the B magnitude.
SPFEED LDAB #56
        TST LPMODE
        BEQ SPFEEDRET
        LDAB LSPITCH
SPFEEDRET RTS
