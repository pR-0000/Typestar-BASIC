; Unsigned 16-bit %binary and &Hhex literals, converted exactly to Canon DW.
; Unary minus remains the decimal parser's responsibility (65535 is positive).
; Scratch reuses decimal literal/formatter temporaries, never native RAM.
        ORG $45D2 ; Retired integer FOR, after the unsigned line formatter.
RADIXSTART
RDLITERAL CMPA #37
        BEQ RDBINARY
        CMPA #38
        BNE RDFALLBACK
        JSR DADVANCE
        LDAA ,X
        ANDA #$DF
        CMPA #72
        BNE RDSYNTAX
        LDAA #4
        BRA RDPREFIX
RDBINARY LDAA #1
RDPREFIX STAA DDOT
        CLR DOUT
        CLR DOUT+1
        CLR DDIG
        JSR DADVANCE
RDREAD LDAA ,X
        CMPA #48
        BCS RDDONE
        CMPA #57
        BLS RDDECIMAL
        ANDA #$DF
        CMPA #65
        BCS RDDONE
        CMPA #70
        BHI RDDONE
        SUBA #7
RDDECIMAL SUBA #48
        STAA DCH
        LDAB DDOT
        CMPB #1
        BNE RDSHIFT
        CMPA #1
        BHI RDSYNTAX
RDSHIFT LSL DOUT+1
        ROL DOUT
        BCS RDOVERFLOW
        DECB
        BNE RDSHIFT
        LDAA DOUT+1
        ORAA DCH
        STAA DOUT+1
        INC DDIG
        JSR DADVANCE
        BRA RDREAD
RDFALLBACK JMP DNUMBER
RDSYNTAX LDAA #1
        BRA RDERROR
RDOVERFLOW LDAA #4
RDERROR STAA DERR
        RTS
RDDONE TST DDIG
        BEQ RDSYNTAX
RDVALUE LDX #DW
        LDAB #9
RDZERO CLR ,X
        INX
        DECB
        BNE RDZERO
; Sixteen double-and-add iterations produce unpacked base-10 digits.
; Carry is the incoming bit, then the carry from the less significant digit.
        LDAA #16
        STAA DDIG
RDBIT LSL DOUT+1
        ROL DOUT
        LDX #DW+7
        LDAB #8
RDDIGIT LDAA ,X
        ROLA
        CMPA #10
        BCS RDNOCARRY
        SUBA #10
        SEC
        BRA RDWRITE
RDNOCARRY CLC
RDWRITE STAA ,X
        DEX
        DECB
        BNE RDDIGIT
        DEC DDIG
        BNE RDBIT
        RTS
RADIXEND EQU *
