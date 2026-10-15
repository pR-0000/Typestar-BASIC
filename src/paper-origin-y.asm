; ORIGIN [x[,y]]: declare current coordinates; never move or seek a sensor.
; X keeps 0..128, Y is 0..448. Preserve state until all validation succeeds.
OYENTRY CLRA
        CLRB
        STD MCY
        JSR SPACE
        CMPA #44
        BNE OYEOS
        INX
        STX CUR
        JSR MCUNSIGNED
        SUBD #448
        BLS OYOK
        JMP RANGEERROR
OYOK ADDD #448
        STD MCY
OYEOS JSR EOS
        JMP OCCHECK
OYSTORE STD PMX
        LDD MCY
        STD PMY
        RTS
OYEND EQU *
