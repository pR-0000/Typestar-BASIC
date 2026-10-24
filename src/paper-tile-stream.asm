; Streaming row of 8x8 tiles, GLYPH A(first),columns,8,5.
; A(first..first+63): sixteen tiles, four big-endian row pairs per tile.
; A(first+64..): column tile IDs (0..15). Preflight before motor ownership.
; Native LPRINT cache/queued continuation prints the whole row, including blanks.
TMBASE EQU SGSTRIDE
TMPTR EQU SGROWPTR
TMCOUNT EQU SGMASK
; @island route
TMROUTE LDAB SGZOOM
        CMPB #5
        BNE TMOLD
        JMP TMINIT
TMOLD
        LDAB SGWIDTH
        CMPB #32
        BHI TMBAD
        JMP SGLAYOUT
; @island init
TMINIT TST SGREPEAT
        BNE TMBAD
        LDAA SGHEIGHT
        SUBA #8
        BNE TMBAD
        LDX SGSRC
        STX TMBASE
        LDAB #64
        STAB TMCOUNT
TMCHECK JSR SGREAD
        DEC TMCOUNT
        BNE TMCHECK
        LDX #LVBUFFER
        STX TMPTR
        STX LPREAD
        LDAB SGWIDTH
        STAB TMCOUNT
        STAB LPREMAIN
TMROW JSR SGREAD
        TSTA
        BNE TMBAD
        CMPB #15
        BHI TMBAD
        LDX TMPTR
        STAB ,X
        INX
        STX TMPTR
        DEC TMCOUNT
        BNE TMROW
        CLR LPCOLUMN
        CLR LPSUPPRESS
        ; Eight source rows occupy the unused upper half of GXPATTERN.
        ; Keys occupy at most its first sixteen bytes. Render band 1 of a
        ; virtual 32-row sprite to address rows 8..15 without a new callback.
        LDD #$2020
        STD SGOUTWIDTH
        DEC SGZOOM
        LDAA #2
        STAA SGACTIVE
        JSR LPBUILD
        CLR SGACTIVE
        CLR PMVALID
        RTS
TMBAD JMP RANGEERROR
; @island decode
TMDECODE STX LPDEST
        TST SGACTIVE
        BNE TMTILE
        ; ASCII was validated by LPRINT/LLIST before the cache is built.
        JSR HFDECODE
        LDX LPDEST
        LDAB #93
        ABX
        CLR ,X
        CLR 1,X
        CLR 2,X
        INX
        INX
        INX
        RTS
TMTILE LDAB #20
        MUL
        ADDD TMBASE
        STD SGSRC
        LDX #GXPATTERN+32
        LDAB #4
        STAB TMCOUNT
TMREAD PSHX
        JSR SGREAD
        PULX
        STAA ,X
        STAB 4,X
        LDAB #8
        ABX
        DEC TMCOUNT
        BNE TMREAD
        LDX LPDEST
        LDAB #1
        TBA
        JSR SGRENDER
        LDAB #32
        ABX
        RTS
; @island select
TMSELECT PSHA
        LDAA SGACTIVE
        BEQ TMSELECTSCENE
        DECA
        PULA ; Preserve the requested band and the DECA condition flags.
        BNE TMSELECTRAW
        JMP SGRENDER
TMSELECTSCENE PULA
        JMP SBBAND
TMSELECTRAW JMP LPSELECT
; @island format
TMFORMAT LDAB SGACTIVE
        CMPB #2
        BNE TMFONTFORMAT
        CLR GPDESC+1
        RTS
TMFONTFORMAT JMP PETAIL
