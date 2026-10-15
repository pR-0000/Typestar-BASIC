; A private flag selects the GLYPH callback; all native format-0 hooks stay intact.
SGSUBMIT LDAA SGWIDTH
        LDAB SGZOOM
        MUL
        STAB SGOUTWIDTH
        PSHB
        LDAA SGHEIGHT
        LDAB SGZOOM
        MUL
        STAB SGOUTHEIGHT
        DECB
        LSRB
        LSRB
        LSRB
        LSRB
        INCB
        TBA ; Number of vertical bands, 1..2.
        PULB
        CMPB #32
        LDAB #1
        BCS SGTILES
        INCB
SGTILES PSHA
        PSHB
        LDAA #1
        STAA SGACTIVE
        PULB
        PULA
        JSR RBJOB
        CLR SGACTIVE
        CLR GPRAN ; RBJOB has stopped the engine on both success and failure.
        TSTA
        BEQ SGDONE
        JMP RBPAPERERROR
SGDONE RTS
SGSELECT TST SGACTIVE
        BNE SGSELECTRAW
        JMP SBBAND
SGSELECTRAW JMP SGRENDER
; Reset once per statement, including the next command after errors/BREAK.
SGRESET CLR STDEPTH
        CLR SGACTIVE
        RTS
SGSUBMITEND EQU *
