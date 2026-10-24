; Guard columns follow physical buffer offsets, also for wide modes 2/3.
SGRCOLUMN CLR SGROW
SGRROW LDAA SGROW
        ADDA SGBAND
        CMPA SGOUTHEIGHT
        BHS SGRNEXTROW
        LDAB SGZOOM
        BITB #1
        BNE SGRY
        LSRA
SGRY ASLA
        ASLA
        TAB
        LDX #GXPATTERN
        ABX
        LDAA SGCOL
        LDAB SGZOOM
        CMPB #1
        BEQ SGRX
        LSRA
        CMPB #4
        BNE SGRX
        LSRA
SGRX TAB
        LSRA
        LSRA
        LSRA
        PSHB
        TAB
        ABX
        PULB
        LDAA #$80
        ANDB #7
        BEQ SGRTEST
SGRSHIFT LSRA
        DECB
        BNE SGRSHIFT
SGRTEST BITA ,X
        BEQ SGRNEXTROW
        LDAB SGROW
        ASLB
        LDX #PBMASKS
        ABX
        LDD ,X
        LDX SGOUT
        ORAA ,X
        ORAB 1,X
        STD ,X
SGRNEXTROW INC SGROW
        LDAA SGROW
        CMPA #16
        BLO SGRROW
        LDX SGOUT
        INX
        INX
        INC SGCOL
        PSHX
        XGDX
        SUBD DFLOOR
        ANDB #63
        PULX
        CMPB #62
        BNE SGRADVANCE
        INX ; Skip each zero native guard word.
        INX
        LDAB SGZOOM
        CMPB #4
        BNE SGRADVANCE
        INC SGCOL ; Large square mode uses physical, rather than useful columns.
SGRADVANCE STX SGOUT
        LDAA SGCOL
        CMPA SGOUTWIDTH
        BHS SGRDONE
        JMP SGRCOLUMN
SGRDONE EQU *
        RTS ; CMPA above already cleared carry (column >= width).
SGRENDEREND EQU *
