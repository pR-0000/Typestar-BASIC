; Recursive, right-associative ^. Also used inside unary +/- so -2^2=-4.
; Existing DATOM stack guard applies at every recursive operand.
XPATOM JSR DATOM
        TST DERR
        BNE XPRETURN
        JSR DSPACE
        CMPA #94
        BNE XPRETURN
        LDX #DW
        LDAB #9
XPPUSH LDAA ,X
        PSHA
        INX
        DECB
        BNE XPPUSH
        JSR DADVANCE
        JSR XPATOM
        LDX #XMEXPONENT
        JSR XMSAVE
        LDX #DW+8
        LDAB #9
XPPOP PULA
        STAA ,X
        DEX
        DECB
        BNE XPPOP
        TST DERR
        BNE XPRETURN
        JMP XMPOWER
XPRETURN RTS
; Integer exponents use squaring; positive bases also accept real exponents.
; No fractional power of a negative base. 0^0=1; 0^negative is an error.
XMPOWER STS XMSP
        LDX #XMARG
        JSR XMSAVE
        LDX #XMEXPONENT
        JSR XMLOAD
        JSR $A400
        BCS XPREAL
        STD XMN
        LDAA DW+8
        ANDA #$80
        STAA XMSIGN
        BEQ XPINTSTART
        LDD #0
        SUBD XMN
        STD XMN
XPINTSTART TST XMSIGN
        BEQ XPBASEOK
        LDX #TRONE
        JSR XMLOAD
        LDX #XMARG
        JSR XMDIV
        LDX #XMARG
        JSR XMSAVE
        CLR XMSIGN ; Invert first: 10^-8 must underflow, not overflow at 10^8.
XPBASEOK LDX #TRONE
        JSR XMLOAD
        LDX #XMSUM
        JSR XMSAVE
XPINTLOOP LDD XMN
        BEQ XPINTDONE
        LSR XMN
        ROR XMN+1
        BCC XPSQUARE
        LDX #XMSUM
        JSR XMLOAD
        LDX #XMARG
        JSR XMMUL
        LDX #XMSUM
        JSR XMSAVE
XPSQUARE LDD XMN
        BEQ XPINTDONE
        LDX #XMARG
        JSR XMLOAD
        LDX #XMARG
        JSR XMMUL
        LDX #XMARG
        JSR XMSAVE
        BRA XPINTLOOP
XPINTDONE LDX #XMSUM
        JSR XMLOAD
        JMP XMEINVERSE
XPREAL LDX #XMARG
        JSR XMLOAD
        JSR XMZERO
        BNE XPNONZERO
        TST XMEXPONENT+8
        BMI XPBADZERO
        RTS
XPBADZERO JMP XMRANGE
XPNONZERO
        JSR XMLOG
        LDX #XMEXPONENT
        JSR XMMUL
        JMP XMEXP
XMPOWEREND EQU *
