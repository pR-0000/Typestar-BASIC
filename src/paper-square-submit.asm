; Mode 1 raw, 2 doubles both axes, 3 doubles X only (square pixels).
; Fits original SGSUBMIT slot by replacing multiplications and stack saves.
SGSUBMIT LDAA SGWIDTH
        LDAB SGZOOM
        DECB
        BEQ SQWIDTH
        ASLA
SQWIDTH STAA SGOUTWIDTH
        PSHA
        LDAA SGHEIGHT
        LDAB SGZOOM
        CMPB #2
        BNE SQHEIGHT
        ASLA
SQHEIGHT STAA SGOUTHEIGHT
        DECA
        LSRA
        LSRA
        LSRA
        LSRA
        INCA
        PULB
        LSRB
        LSRB
        LSRB
        LSRB
        LSRB
        INCB
        ; SGRESET clears SGACTIVE before every BASIC statement.
SGTILES INC SGACTIVE
        JSR RBJOB
        CLR SGACTIVE
        CLR GPRAN
        TSTA
        BEQ SGDONE
        JMP RBPAPERERROR
SGDONE RTS
SQEND EQU *
