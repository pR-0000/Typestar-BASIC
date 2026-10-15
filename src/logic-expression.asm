; Precedence climbing. Each pending binary operation keeps its operands and
; minimum precedence on the CPU stack, so nested functions cannot overwrite it.
; OR=1 AND=2 NOT=3 comparisons=4 +=5 MOD=6 */=7; XPATOM owns ^.
LXENTRY LDAA #1
        JMP LXPARSE
LXPARSE PSHA
        JSR LXATOM
LXLOOP TST DERR
        BNE LXEND
        JSR LXOP
        CMPB #8
        BEQ LXEND
        PSHX
        TSX
        CMPA 2,X
        PULX
        BCS LXEND
        STX DPTR
        INCA
        PSHB
        PSHA
        LDX #DW
        LDAB #9
LXSAVE LDAA ,X
        PSHA
        INX
        DECB
        BNE LXSAVE
        TSX
        LDAA 9,X
        JSR LXPARSE
        LDX #DW
        LDAB #9
LXRIGHT LDAA ,X
        STAA 9,X
        INX
        DECB
        BNE LXRIGHT
        LDX #DW+8
        LDAB #9
LXLEFT PULA
        STAA ,X
        DEX
        DECB
        BNE LXLEFT
        PULA
        PULA
        TST DERR
        BNE LXEND
        JSR LXAPPLY
        BRA LXLOOP
LXEND INS
        RTS
LXATOM TSX
        CPX #$1F80
        BCC LXSAFE
        LDAA #3
        STAA DERR
        RTS
LXSAFE JSR DSPACE
        JSR LXOP
        CMPB #8
        BNE LXVALUE
        STX DPTR
        LDAA #3
        JSR LXPARSE
        JSR LXINT
        BCS LXRETURN
        COMA
        COMB
        JMP LXSIGNED
LXVALUE JSR STISSTR
        BCS LXSTRING
        JMP XPATOM
LXSTRING JSR STCMP
LXFROMBOOL TSTB
        BEQ LXBOOL
        LDD #$FFFF
LXBOOL JMP LXSIGNED
LXRETURN RTS
