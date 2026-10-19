; RBJOB callback: stage exactly one band, including blank guard columns.
; A=band, B=tiles, X=destination. Zoom preserves all 32 columns of a 16x8
; sprite: native column 31 continues in a second contiguous tile, not cropped.
; PBMASKS is shared with the geometry renderer and can be relocated. The final
; incremental linker must rebind this operand to the current symbol map; .89
; repairs a stale $40F8 reference. Sparse pixel tests cover every table row.
SGRENDER STX SGOUT
        ASLA
        ASLA
        ASLA
        ASLA
        STAA SGBAND
        ASLB
        ASLB
        ASLB
        ASLB
        ASLB
        ASLB
SGRZERO CLR ,X
        INX
        DECB
        BNE SGRZERO
        CLR SGCOL
SGRCOLUMN CLR SGROW
SGRROW LDAA SGROW
        ADDA SGBAND
        CMPA SGOUTHEIGHT
        BHS SGRNEXTROW
        LDAB SGZOOM
        CMPB #2
        BNE SGRY
        LSRA
SGRY ASLA
        ASLA
        TAB
        LDX #GXPATTERN
        ABX
        LDAA SGCOL
        LDAB SGZOOM
        CMPB #2
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
        ANDB #7
        LDAA #$80
SGRSHIFT TSTB
        BEQ SGRTEST
        LSRA
        DECB
        BRA SGRSHIFT
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
        LDAA SGCOL
        CMPA #31
        BNE SGRADVANCE
        INX ; Skip the zero native guard word between tiles.
        INX
SGRADVANCE STX SGOUT
        CMPA SGOUTWIDTH
        BLO SGRCOLUMN
        CLC
        RTS
SGRENDEREND EQU *
