; Public fixed module entries. Linked against main BASIC symbols.
        JMP LCDDISPATCH
        JMP BINATOM
        JMP LOWINIT
        JMP LOWSTATUS
        JMP LOWCLEAR
        JMP SOFTAPPLY
        JMP SOFTTICK
        JMP SOFTMODECMD
        JMP IFCONDITION
        JMP GDISPATCH ; $481B
        JMP GFINISH ; $481E
        JMP GNEXTCHECK ; $4821
LOWSHADOW EQU $1B60
TRIBANK EQU $1B5A
LCDDISPATCH LDX #KTRI
        JSR MATCH
        BCS TRYLOW
        JMP LCDTRI
TRYLOW LDX #KLOW
        JSR MATCH
        BCS NOTLCD
        JMP LCDLINE
NOTLCD JMP SOUNDDISPATCH
KTRI FCC "LCDTRI"
        FCB 0
KLOW FCC "LCDLINE"
        FCB 0
; Initialize and clear the lower bank, then restore the I/II indicator.
; Both native glyphs and automatic CGRAM glyphs are tracked from now on.
LOWINIT CLRA
LOWINITLOOP LDAB #32
        JSR LOWSTATUS
        INCA
        CMPA #32
        BNE LOWINITLOOP
        JMP LCDMODE
        INCLUDE "src/lcd-status-module.inc"
; Eight automatic composite slots. Metadata is valid for slots assigned here;
; raw POKE/CGRAM definitions must not be mixed with this allocator.
TRICHARS EQU $1B44
TRIMASKS EQU $1B4C
TRICOL EQU $1B54
TRIMASK EQU $1B55
TRICHAR EQU $1B56
TRISLOT EQU $1B57
TRIFONT EQU $1B58
; LCDTRI column,mask: validate arguments before modifying the display.
LCDTRI CLR TRIBANK
        JSR TRIPARSE
        JMP TRIBODY
LCDLINE LDAA #1
        STAA TRIBANK
        JSR TRIPARSE
        LDAA #$FF
        STAA TRICHAR
        TST TRIMASK
        BNE LOWALLOC
        LDAB #32
        BRA LOWPLACE
LOWALLOC JSR TRIALLOC
        JSR TRISAVEADDR
        JSR TRIMETA
        LDAA TRIMASK
        JSR LCDDATA
        LDAB #7
LOWZERO CLRA
        JSR LCDDATA
        DECB
        BNE LOWZERO
        LDAA LCDSAVED
        JSR LCDCMD
        LDAB TRISLOT
LOWPLACE LDAA TRICOL
        JSR LOWSTATUS
        LDAA #1
        STAA OUTFLAG
        RTS
TRIPARSE JSR EXPR
        TSTA
        BEQ TRICHECKCOL
        JMP RANGEERROR
TRICHECKCOL TSTB
        BEQ TRIRANGE
        CMPB #32
        BHI TRIRANGE
        DECB
        PSHB
        JSR SPACE
        CMPA #44
        BEQ TRICOMMA
        JMP SYNTAX
TRICOMMA INX
        STX CUR
        JSR EXPR
        TSTA
        BNE TRIRANGE
        CMPB #31
        BHI TRIRANGE
        PSHB
        JSR EOS
        PULB
        STAB TRIMASK
        PULB
        STAB TRICOL
        RTS
TRIBODY LDX #LCDBUF
        ABX
        LDAA ,X
        CMPA #7
        BHI TRIASCII
        TAB
        LDX #TRICHARS
        ABX
        LDAA ,X
TRIASCII STAA TRICHAR
        TST TRIMASK
        BNE TRIFINDGLYPH
        JMP TRIRESTORE
TRIRANGE JMP RANGEERROR
TRINOCHAR LDX #TRICHARMSG
        JMP ERROR
; Full-height BASIC font; Canon accent bases have two leading blank rows.
TRIFINDGLYPH CMPA #32
        BEQ TRISPACE
        CMPA #65
        BCS TRINOCHAR
        CMPA #90
        BLS TRIUPPER
        CMPA #97
        BCS TRINOCHAR
        CMPA #122
        BHI TRINOCHAR
        SUBA #6
TRIUPPER SUBA #65
        TAB
        CLRA
        STD TRIFONT
        ASLD
        ASLD
        ASLD
        SUBD TRIFONT
        ADDD #TRILETTERS
        BRA TRIFONTSET
TRISPACE LDD #TRIBLANK
TRIFONTSET STD TRIFONT
        JSR TRIALLOC
        JMP TRIASSIGN
; Scan both banks before reusing CGRAM. Exclude only the target cell.
TRIALLOC CLR TRISLOT
TRISLOTLOOP LDX #LCDBUF
        CLRB
TRISCAN TST TRIBANK
        BNE TRISCANUP
        CMPB TRICOL
        BEQ TRISCANNEXT
TRISCANUP LDAA ,X
        CMPA TRISLOT
        BEQ TRIOCCUPIED
TRISCANNEXT INX
        INCB
        CMPB #32
        BNE TRISCAN
        LDX #LOWSHADOW
        CLRB
LOWSCAN TST TRIBANK
        BEQ LOWCHECK
        CMPB TRICOL
        BEQ LOWSCANNEXT
LOWCHECK LDAA ,X
        CMPA TRISLOT
        BEQ TRIOCCUPIED
LOWSCANNEXT INX
        INCB
        CMPB #32
        BNE LOWSCAN
        RTS
TRIOCCUPIED LDX #TRICHARS
        LDAB TRISLOT
        ABX
        LDAA ,X
        CMPA TRICHAR
        BNE TRINEXTSLOT
        LDAA 8,X
        CMPA TRIMASK
        BNE TRINEXTSLOT
        RTS
TRINEXTSLOT INC TRISLOT
        LDAA TRISLOT
        CMPA #7
        BNE TRISLOTLOOP
        LDX #TRIFULLMSG
        JMP ERROR
TRIASSIGN JSR TRISAVEADDR
        JSR TRIMETA
        BRA TRIWRITEFONT
TRISAVEADDR JSR LCDWAIT
        LDAA $38
        ANDA #$7F
        ORAA #$80
        STAA LCDSAVED
        RTS
TRIMETA LDX #TRICHARS
        LDAB TRISLOT
        ABX
        LDAA TRICHAR
        STAA ,X
        LDAA TRIMASK
        STAA 8,X
        LDAA TRISLOT
        ASLA
        ASLA
        ASLA
        ORAA #$40
        JMP LCDCMD
TRIWRITEFONT LDX TRIFONT
        LDAB #7
TRIROWS LDAA ,X
        JSR LCDDATA
        INX
        DECB
        BNE TRIROWS
        LDAA TRIMASK
        JSR LCDDATA
        LDAA TRISLOT
        BRA TRIPLACE
TRIRESTORE JSR LCDWAIT
        LDAA $38
        ANDA #$7F
        ORAA #$80
        STAA LCDSAVED
        LDAA TRICHAR
TRIPLACE LDAB TRICOL
        LDX #LCDBUF
        ABX
        STAA ,X
        CLR UIPENDING
        JSR LCDREDRAW
        LDAA LCDSAVED
        JSR LCDCMD
        LDAA #1
        STAA OUTFLAG
        RTS
TRIFULLMSG FCC "?LCD SLOTS"
        FCB 0
TRICHARMSG FCC "?LCD CHAR"
        FCB 0
; Binary literal for all expressions: 1..16 digits, no truncation.
; X points to %, SIGN belongs to ATOM and must be preserved.
BINATOM INX
        CLR DIGIT
        LDD #0
        STD VALUE
BINLOOP LDAA ,X
        CMPA #48
        BEQ BINBIT
        CMPA #49
        BNE BINDONE
BINBIT SUBA #48
        PSHA
        INC DIGIT
        LDAA DIGIT
        CMPA #16
        BLS BINSHIFT
        JMP RANGEERROR
BINSHIFT LDD VALUE
        ASLD
        STD VALUE
        PULA
        TAB
        CLRA
        ADDD VALUE
        STD VALUE
        INX
        BRA BINLOOP
BINDONE TST DIGIT
        BNE BINVALID
        JMP SYNTAX
BINVALID STX CUR
        LDD VALUE
        JMP ATOMSIGN

; CLS clears only lower cells owned by LCDLINE. Preserve ICON and I/II.
; No CGRAM rewrites: shared upper-bank glyphs remain valid.
LOWCLEAR CLRA
LOWCLEARLOOP PSHA
        TAB
        LDX #LOWSHADOW
        ABX
        LDAB ,X
        CMPB #7
        BHI LOWKEEP
        LDX #TRICHARS
        ABX
        LDAA ,X
        CMPA #$FF
        BNE LOWKEEP
        PULA
        LDAB #32
        JSR LOWSTATUS
        BRA LOWCLEARNEXT
LOWKEEP PULA
LOWCLEARNEXT INCA
        CMPA #32
        BNE LOWCLEARLOOP
        RTS
        INCLUDE "tmp/historical-lcd-font/lcd-font-5x7.inc" ; historical builds through .48 only

        INCLUDE "src/basic-sound.inc"

        INCLUDE "src/lcd-soft-cursor.inc"

        INCLUDE "src/basic-condition.inc"

        INCLUDE "src/basic-gosub.inc"
