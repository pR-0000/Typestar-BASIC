; CODE shares its row with the margin keys: the matrix's lowest pressed
; bit wins, so a margin key can hide CODE. Verify CODE explicitly, and retain
; the unmodified raw key whenever the chord is inactive or unavailable.
CXSCAN JSR KBDSCAN
        PSHA
        LDAA #$7F
        STAA $31
        LDAA $30
        ORAA $30
        BITA #8
        BNE CXORIGINAL
        ; The console owns width 31; INPUT owns 14..30. Startup, transfer,
        ; execution and result waits have no active editor ($19FB=0).
        LDAB EDWIDTH
        CMPB #31
        BNE CXORIGINAL
        TST $19FB
        BEQ CXORIGINAL
        LDX #CXTABLE
CXLOOP LDAA ,X
        STAA $31
        LDAA $30
        ORAA $30
        ANDA 1,X
        BEQ CXFOUND
        INX
        INX
        INX
        CPX #CXTABLEEND
        BNE CXLOOP
        LDAA #$3B
        BRA CXSELECTED
CXFOUND LDAA 2,X
CXSELECTED PULB
        BRA CXRELEASE
CXORIGINAL PULA
CXRELEASE LDAB #$FF
        STAB $31
CXRET RTS
; @island table
CXTABLE FCB $FD,$80,$80,$DF,$80,$91,$BF,$02,$BC,$BF,$04,$BE
        FCB $7F,1,$81,$7F,2,$82
CXTABLEEND EQU *
