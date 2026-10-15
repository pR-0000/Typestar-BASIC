; CIRCLE cx,cy,radius,width,fill. Logical isotropic coordinates, like LINE.
; Whole disk must fit X=0..247,Y=0..255; radius>=1,width=1..16,fill=0/1.
; Store kind=2 and inclusive bounding box in the existing eight-byte record.
; Parse/validate everything before allocating or modifying a deferred scene.
CCDISPATCH LDX #CCNAME
        JSR MATCH
        BCC CCPARSE
        JMP MCDISPATCH
CCNAME FCC "CIRCLE"
        FCB 0
CCPARSE CLR PXINDEX
CCARG JSR EXPR
        TSTA
        BNE CCBAD
        TST DW+8
        BMI CCBAD
        PSHB
        LDX #PXSTATE
        LDAB PXINDEX
        ABX
        PULB
        STAB ,X
        INC PXINDEX
        LDAA PXINDEX
        CMPA #5
        BEQ CCCHECK
        JSR SPACE
        CMPA #44
        BNE CCSYNTAX
        INX
        STX CUR
        BRA CCARG
CCBAD JMP RANGEERROR
CCSYNTAX JMP SYNTAX
CCCHECK JSR EOS
        LDAA PXSTATE+2
        BEQ CCBAD
        LDAA PXSTATE+3
        BEQ CCBAD
        CMPA #16
        BHI CCBAD
        LDAA PXSTATE+4
        CMPA #1
        BHI CCBAD
        STAA SHRECORD+6
        LDAA PXSTATE+3
        STAA SHRECORD+5
        LDAA PXSTATE
        SUBA PXSTATE+2
        BCS CCBAD
        STAA SHRECORD+1
        LDAA PXSTATE
        ADDA PXSTATE+2
        BCS CCBAD
        CMPA #247
        BHI CCBAD
        STAA SHRECORD+3
        LDAA PXSTATE+1
        SUBA PXSTATE+2
        BCS CCBAD
        STAA SHRECORD+2
        LDAA PXSTATE+1
        ADDA PXSTATE+2
        BCS CCBAD
        STAA SHRECORD+4
        LDAA #2
        STAA SHRECORD
        CLR SHRECORD+7
        JMP SHLOOKUP

; Extend scene dispatch without relocating existing BOX/LINE code.
CCSELECT LDX PCPTR
        LDAA ,X
        CMPA #2
        BEQ CCCIRCLE
        JMP PCNEXT+3
; Only LINE extends beyond its endpoints. BOX and CIRCLE are bounded inside.
CCEXTENT CLRB
        LDAA ,X
        CMPA #1
        BNE CCEXTEND
        LDAB 5,X
        LSRB
CCEXTEND JMP SHX

; Tile-local integer disk/annulus rasterizer, no floating point or new RAM.
; Evaluate both logical rows per native dot and OR them via existing PLDOT.
; Squares are unsigned 16-bit; overflow of their sum is outside any disk.
; Stroke lies inward: outer radius r, inner radius max(r-width,0).
CCX EQU PLSTATE
CCY EQU PLSTATE+1
CCR EQU PLSTATE+2
CCOUTER EQU PLSTATE+3
CCINNER EQU PLSTATE+7
CCSOLID EQU PLSTATE+9
CCROW EQU PLSTATE+10
CCCOL EQU PLSTATE+11
CCDX2 EQU PLSTATE+12
CCCIRCLE LDAA 3,X
        SUBA 1,X
        LSRA
        STAA CCR
        ADDA 1,X
        STAA CCX
        LDAA 2,X
        ADDA CCR
        STAA CCY
        LDAA 6,X
        STAA CCSOLID
        LDAA CCR
        TAB
        MUL
        STD CCOUTER
        LDAA CCR
        SUBA 5,X
        BHI CCHOLLOW
        INC CCSOLID
        CLRA
CCHOLLOW TAB
        MUL
        STD CCINNER
        LDAA PCOX
        STAA PLOX
        LDAA PCOY
        STAA PLOY
        LDX #PLOUT
        LDAB #64
CCZERO CLR ,X
        INX
        DECB
        BNE CCZERO
        CLR CCCOL
CCNEXTX LDAA PCOX
        ADDA CCCOL
        STAA PLSX+1
        CLR PLSX
        SUBA CCX
        BCC CCABSX
        NEGA
CCABSX TAB
        MUL
        STD CCDX2
        CLR CCROW
CCNEXTY LDAA PCOY
        ASLA
        ADDA CCROW
        STAA PLSYDOT+1
        CLR PLSYDOT
        SUBA CCY
        BCC CCABSY
        NEGA
CCABSY TAB
        MUL
        ADDD CCDX2
        BCS CCSKIP
        SUBD CCOUTER
        BHI CCSKIP
        ADDD CCOUTER
        TST CCSOLID
        BNE CCDOT
        SUBD CCINNER
        BLS CCSKIP
CCDOT JSR PLDOT
CCSKIP INC CCROW
        LDAA CCROW
        CMPA #32
        BNE CCNEXTY
        INC CCCOL
        LDAA CCCOL
        CMPA #31
        BNE CCNEXTX
        CLC
        JMP PCMERGE
CCEND EQU *
