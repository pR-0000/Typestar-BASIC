; .49 replaces the non-native composition font with explicit user pixels.
; No CGROM or CGRAM read needed. Custom slots are owned by one text cell.
; Raw POKE of CGRAM/LCDBUF remains outside allocator guarantees.
LCPX EQU $1B10             ; eight staged rows; changed display only after EOS
LCINDEX EQU $1B18
        ORG $4ABC
LCDNEW LDX #LCKEY
        JSR MATCH
        BCC LCPARSE
        LDX #KTRI
        JMP LCDDISPATCH+3
LCKEY FCC "LCDCHAR"
        FCB 0
; LCDCHAR position,row1,row2,row3,row4,row5,row6,row7,triangle
LCPARSE JSR EXPR
        TSTA
        BNE LCRANGE
        TSTB
        BEQ LCRANGE
        CMPB #32
        BHI LCRANGE
        DECB
        STAB TRICOL
        CLR LCINDEX
LCNEXT JSR SPACE
        CMPA #44
        BNE LCSYNTAX
        INX
        STX CUR
        JSR EXPR
        TSTA
        BNE LCRANGE
        CMPB #31
        BHI LCRANGE
        PSHB
        LDX #LCPX
        LDAB LCINDEX
        ABX
        PULB
        STAB ,X
        INC LCINDEX
        LDX CUR
        LDAA LCINDEX
        CMPA #8
        BNE LCNEXT
        JSR EOS
        CLR TRIBANK
        LDAA #$FE
        STAA TRICHAR
        LDAA LCPX+7
        STAA TRIMASK
        LDD #LCPX
        STD TRIFONT
        JSR TRIALLOC
        JMP TRIASSIGN
LCRANGE JMP RANGEERROR
LCSYNTAX JMP SYNTAX
; Slot reuse by metadata is only valid for blank triangles/lower lines.
; $FE is a user bitmap, whose rows need not match another $FE slot.
LCOCCUPIED LDAA TRICHAR
        CMPA #$FE
        BEQ LCSKIP
        LDX #TRICHARS
        JMP TRIOCCUPIED+3
LCSKIP JMP TRINEXTSLOT
; Inspect the displayed slot before resolving the old native-code metadata.
LCTRI LDX #LCDBUF
        ABX
        LDAA ,X
        CMPA #6
        BHI LCNATIVE
        STAA TRISLOT
        TAB
        LDX #TRICHARS
        ABX
        LDAA ,X
        CMPA #$FE
        BEQ LCEDIT
LCNATIVE LDX #LCDBUF
        LDAB TRICOL
        JMP TRIBODY+3
; Keep all seven user-defined rows and change only row eight, even mask=0.
LCEDIT JSR TRISAVEADDR
        LDX #TRIMASKS
        LDAB TRISLOT
        ABX
        LDAA TRIMASK
        STAA ,X
        LDAA TRISLOT
        ASLA
        ASLA
        ASLA
        ORAA #$47
        JSR LCDCMD
        LDAA TRIMASK
        JSR LCDDATA
        LDAA LCDSAVED
        JSR LCDCMD
        LDAA #1
        STAA OUTFLAG
        RTS
LCEND EQU *
        ORG $9120
; Native glyphs cannot be overlaid without a copy of their CGROM pixels.
LCNATIVEFONT CMPA #32
        BEQ LCSPACE
        JMP TRINOCHAR
LCSPACE JMP TRISPACE
LCFONTEND EQU *
