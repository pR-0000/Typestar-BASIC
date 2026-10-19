; Continuous repeated glyphs. Public syntax:
; GLYPH A(first),width,height[,mode[,repeat]]; repeat 1..16.
; Mode 4: large square pixels (X4/Y2), physical guard columns included in pitch.
; Repeats reuse one rendered glyph per band; no allocation proportional to count.
; SGREPEAT=$1D9A is exclusive LIST/SAVE/printer scratch, not persistent RAM.
; @island command
SGPARSE JSR MCFREE
        LDX CUR
        STX DPTR
        CLR DERR
        JSR ARADDRESS
        TST DERR
        BNE SGERROR
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
        CMPB #4
        BHI SGBAD
        STAB SGZOOM
SGNOZOOM CLR SGREPEAT
        JSR SPACE
        CMPA #44
        BNE SGARGSEND
        JSR SGCOMMA
        CMPB #16
        BHI SGBAD
        STAB SGREPEAT
SGARGSEND JSR EOS
        JMP SGLAYOUT
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
; @island layout
SGLAYOUT LDAA SGRANK
        CMPA #1
        BEQ SGWORDS
        CLRA
        LDAB SGWIDTH
        SUBD SGSTRIDE
        BNE SGLBAD
        BRA SGSTAGING
SGWORDS LDAB SGWIDTH
        CMPB #16
        BHI SGLBAD
SGSTAGING JMP SGSTAGE
SGLBAD JMP RANGEERROR


; @island submit
; Mode 1 raw, 2 doubles both axes, 3 doubles X only (square pixels).
; Fits original SGSUBMIT slot by replacing multiplications and stack saves.
SGSUBMIT LDAA SGWIDTH
        LDAB SGZOOM
        DECB
        BEQ SQWIDTH
        ASLA
        CMPB #3
        BNE SQWIDTH
        ASLA
        STAA SGOUTWIDTH
        DECA ; Round the physical frame up, without adding an empty tile.
        BRA SQFRAME
SQWIDTH STAA SGOUTWIDTH
SQFRAME PSHA
        LDAA SGHEIGHT
        LDAB SGZOOM
        BITB #1
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

; @island render
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
        JMP SGRCOLUMN
; @island pixels
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
        TAB
        ANDB #31
        CMPB #31
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
        CLC
        RTS
SGRENDEREND EQU *

; @island tail
; Called instead of LPFORMAT, before the first glyph of each BASIC band.
; Text uses 96-byte cached glyphs: leave its count and path unchanged.
; Graphics tiles are 64 bytes including guard column. Trim only whole tiles.
; Keep RBTILES/RBBACKUP intact for rendering and workspace restoration.
PETAIL STAA GPDESC+1
        BNE PEDONE
        LDAA RBTILES
        STAA GXNX
        LDX RBBACKUP
PENEXT CLRA
        LDAB #64
PEBYTE DEX
        ORAA ,X
        DECB
        BNE PEBYTE
        TSTA
        BNE PEDONE
        DEC GXNX
        BNE PENEXT
        ; All blank: discard LPFORMAT return, feed without zero-distance
        ; carriage move, then continue RBROW after its LPROW call.
        PULX
        JSR GPROW+24
        JMP RBROW+3
PEDONE TST SGACTIVE
        BEQ SGTAILRETURN
        TST SGREPEAT
        BEQ SGTAILRETURN
        LDAA RBTILES
        LDAB SGREPEAT
        MUL
        STAB GXNX
SGTAILRETURN RTS
PEEND EQU *

; @island wrap
; Raw graphics: loop over one immutable cached glyph for repeat commands.
; X is scratch at this hook; XGDX preserves the comparison carry.
SGWRAP ADDD #64
        XGDX
        CPX RBBACKUP
        XGDX
        BCS SGWRAPRETURN
        LDD DFLOOR
SGWRAPRETURN RTS
SGWRAPEND EQU *

; @island print
; Keep BREAK responsive between cached blocks, as for continuous LPRINT.
SGPRINT JSR RFASTBREAK
        BNE SGPRINTNEXT
        LDAA #8
        STAA GPERROR
        JMP RBABORT
SGPRINTNEXT JMP GPPRINT
SGPRINTEND EQU *
