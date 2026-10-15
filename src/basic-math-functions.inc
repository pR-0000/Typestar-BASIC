; ABS/SGN share argument parsing. B selects ABS=0 or SGN=1.
; Preserve the outer unary sign and function kind across nested expressions.
MFUNC PSHB
        LDAA SIGN
        PSHA
        JSR SPACE
        CMPA #40
        BNE MFBAD
        INX
        STX CUR
        JSR EXPR
        STD TEMP
        JSR SPACE
        CMPA #41
        BNE MFBAD
        INX
        STX CUR
        PULA
        STAA SIGN
        PULB
        TSTB
        BEQ MFABS
        LDD TEMP
        BEQ MFDONE
        BMI MFNEG
        LDD #1
        BRA MFDONE
MFNEG LDD #$FFFF
        BRA MFDONE
MFABS LDD TEMP
        BPL MFDONE
        COMA
        COMB
        ADDD #1
        BPL MFDONE
        JMP RANGEERROR ; abs(-32768)=32768 cannot fit a signed 16-bit result.
MFDONE JMP ATOMSIGN
MFBAD JMP SYNTAX
