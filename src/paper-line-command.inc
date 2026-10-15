; PLINE x1,y1,x2,y2,width. Evaluate all five expressions before touching
; shared LIST scratch or native printer state. Same logical units as PBOX.
LNDISPATCH LDX #LNNAME
        JSR MATCH
        BCC LNPARSE
        JMP PXDISPATCH
LNNAME FCC "PLINE"
        FCB 0
LNPARSE CLR PXINDEX
LNARG JSR EXPR
        TSTA
        BNE LNRANGE
        TST DW+8
        BMI LNRANGE
        PSHB
        LDX #PXSTATE
        LDAB PXINDEX
        ABX
        PULB
        STAB ,X
        INC PXINDEX
        LDAA PXINDEX
        CMPA #5
        BEQ LNCHECK
        JSR SPACE
        CMPA #44
        BNE LNSYNTAX
        INX
        STX CUR
        BRA LNARG
LNRANGE JMP RANGEERROR
LNSYNTAX JMP SYNTAX
LNCHECK JSR EOS
        LDAA PXSTATE
        CMPA #247
        BHI LNRANGE
        LDAA PXSTATE+2
        CMPA #247
        BHI LNRANGE
        LDAA PXSTATE+4
        BEQ LNRANGE
        CMPA #16
        BHI LNRANGE
        ; Five bytes are committed only after expression evaluation ends.
        LDD PXSTATE
        STD PLSTATE
        LDD PXSTATE+2
        STD PLSTATE+2
        LDAA PXSTATE+4
        STAA PLWIDTH
        LDAA #1
        STAA LNMODE
        ; Extents include the positive half of the square brush. Clamp to
        ; the public page limits before deriving the native tile counts.
        LDAA PLWIDTH
        LSRA
        STAA LNEXTRA
        LDAA PLX1
        CMPA PLX2
        BCC LNMAXX
        LDAA PLX2
LNMAXX ADDA LNEXTRA
        CMPA #247
        BLS LNXOK
        LDAA #247
LNXOK CLRB
LNXDIV INCB
        SUBA #31
        BCC LNXDIV
        PSHB
        LDAA PLY1
        CMPA PLY2
        BCC LNMAXY
        LDAA PLY2
LNMAXY ADDA LNEXTRA
        BCC LNYOK
        LDAA #255
LNYOK LSRA
        LSRA
        LSRA
        LSRA
        LSRA
        INCA
        PULB
        JSR RBJOB
        BCC LNOK
        JMP RBPAPERERROR
LNOK RTS
; Existing rectangle callback is preserved. PBOX clears LNMODE at PGSTART.
LNSELECT TST LNMODE
        BNE LNBAND
        JMP PRBAND
LNBAND STX PRDEST
        STAB PRLEFT
        LDAB #16
        MUL
        STAB PLOY
        CLR PLOX
LNNEXT JSR PLLINE
        BCS LNFAIL
        LDX #PLOUT
        LDAB #64
LNTILECOPY LDAA ,X
        PSHX
        LDX PRDEST
        STAA ,X
        INX
        STX PRDEST
        PULX
        INX
        DECB
        BNE LNTILECOPY
        LDAA PLOX
        ADDA #31
        STAA PLOX
        DEC PRLEFT
        BNE LNNEXT
        CLC
        RTS
LNFAIL SEC
        RTS
LNEND EQU *
