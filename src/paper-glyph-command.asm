; GLYPH A(first),width,height[,zoom] : packed row words, width <=16.
; GLYPH A(row,0),width,height[,zoom] : pixel matrix, width equals stride <=31.
; Each argument and every cell is checked before any paper motion. Source
; remains in its array; a 64-byte staged bitmap separates evaluation/printing.
SGACTIVE EQU $196D
SGSRC EQU $1D80
SGENDPTR EQU $1D82
SGWIDTH EQU $1D84
SGHEIGHT EQU $1D85
SGZOOM EQU $1D86
SGRANK EQU $1D87
SGSTRIDE EQU $1D88
SGROWPTR EQU $1D8A
SGDEST EQU $1D8C
SGROW EQU $1D8E
SGCOL EQU $1D8F
SGMASK EQU $1D90
SGOUT EQU $1D91
SGBAND EQU $1D93
SGOUTWIDTH EQU $1D94
SGOUTHEIGHT EQU $1D95
SGPARSE JSR MCFREE
        LDX CUR
        STX DPTR
        CLR DERR
        JSR ARADDRESS
        TST DERR
        BEQ SGSOURCEOK
        JMP SGERROR
SGSOURCEOK STX SGSRC
        LDD DIMJOB+27
        STD SGENDPTR
        LDAA DIMJOB
        STAA SGRANK
        LDD DIMJOB+4
        STD SGSTRIDE
        LDD DIMJOB+10
        BNE SGBAD
        LDX DPTR
        STX CUR
        JSR SGCOMMA
        STAB SGWIDTH
        CMPB #31
        BHI SGBAD
        JSR SGCOMMA
        STAB SGHEIGHT
        CMPB #16
        BHI SGBAD
        LDAB #1
        STAB SGZOOM
        JSR SPACE
        CMPA #44
        BNE SGNOZOOM
        JSR SGCOMMA
        CMPB #2
        BHI SGBAD
        STAB SGZOOM
SGNOZOOM JSR EOS
        LDAA SGRANK
        CMPA #1
        BEQ SGWORDS
        CLRA
        LDAB SGWIDTH
        SUBD SGSTRIDE
        BNE SGBAD
        BRA SGSTAGING
SGWORDS LDAB SGWIDTH
        CMPB #16
        BHI SGBAD
SGSTAGING JMP SGSTAGE
SGBAD JMP RANGEERROR
SGERROR LDAA DERR
        JMP $A518
SGCOMMA JSR SPACE
        CMPA #44
        BEQ SGARG
        JMP SYNTAX
SGARG INX
        STX CUR
        JSR EXPR
        TSTA
        BNE SGBAD
        TST DW+8
        BMI SGBAD
        TSTB
        BEQ SGBAD
        RTS
SGCOMMANDEND EQU *
