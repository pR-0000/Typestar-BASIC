; ORIGIN [x[,y]], same checked interface as the original split implementation.
; Coordinates are only committed after both operands and ownership validate.
OCENTRY CLRA
        CLRB
        STD MCX
        STD MCY
        JSR SPACE
        TSTA
        BEQ OCVALIDATE
        CMPA #58
        BEQ OCVALIDATE
        JSR MCUNSIGNED
        SUBD #128
        BHI OCBAD
        ADDD #128
        STD MCX
        JSR SPACE
        CMPA #44
        BNE OCVALIDATE
        INX
        STX CUR
        JSR MCUNSIGNED
        SUBD #448
        BHI OCBAD
        ADDD #448
        STD MCY
OCVALIDATE JSR EOS
        JSR MCFREE
        JSR PMORIGIN
        LDD MCX
        STD PMX
        LDD MCY
        STD PMY
        RTS
OCBAD JMP RANGEERROR
OCEND EQU *
