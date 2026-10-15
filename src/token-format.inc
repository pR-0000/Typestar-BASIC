        ORG FORCOMMAND+3 ; Reuse disabled legacy integer FOR body.
; Unsigned 16-bit formatting into LBUFFER. Do not call signed OUTNUM, which
; would render 32768..65535 as negatives. Return X at the first free byte.
RFORMAT STD RFMT
        LDX #LBUFFER
        STX RFPTR
        CLR RFSTART
        LDX #DIVISORS
RFLOOP LDAA #48
        STAA RFDIG
RFSUB LDD RFMT
        SUBD ,X
        BCS RFEMIT
        STD RFMT
        INC RFDIG
        BRA RFSUB
RFEMIT LDAA RFDIG
        CMPA #48
        BNE RFWRITE
        TST RFSTART
        BNE RFWRITE
        CPX #DIVISORS+8
        BNE RFSKIP
RFWRITE PSHX
        LDX RFPTR
        STAA ,X
        INX
        STX RFPTR
        PULX
        INC RFSTART
RFSKIP INX
        INX
        CPX #DIVISORS+10
        BNE RFLOOP
        LDX RFPTR
        RTS
