; CPU prototype only: origin and RAM bindings supplied by the test linker.
; No LCD, serial, heap, motors or native ROM calls.
; PBSTATE: left/right/top/bottom (four unsigned inclusive 16-bit coords),
; tile X/Y origin (words), thickness 1..16, fill 0/1. Remaining bytes scratch.
; PBOUT: exactly 64 bytes, 31 columns x16 dots plus two zero guard bytes.
; C=1 invalid arguments, output untouched. C=0 output replaced completely.
; Tile origin <=65505/65520 prevents coordinate wrap. X/A/B clobbered.
PBLEFT EQU PBSTATE
PBRIGHT EQU PBSTATE+2
PBTOP EQU PBSTATE+4
PBBOTTOM EQU PBSTATE+6
PBTX EQU PBSTATE+8
PBTY EQU PBSTATE+10
PBWIDTH EQU PBSTATE+12
PBFILL EQU PBSTATE+13
PBPX EQU PBSTATE+14
PBPY EQU PBSTATE+16
PBCOL EQU PBSTATE+18
PBROW EQU PBSTATE+19
PBWORD EQU PBSTATE+20
PBPTR EQU PBSTATE+22
PBRECT LDD PBRIGHT
        SUBD PBLEFT
        BCS PBINVALID
        LDD PBBOTTOM
        SUBD PBTOP
        BCS PBINVALID
        LDD #65505
        SUBD PBTX
        BCS PBINVALID
        LDD #65520
        SUBD PBTY
        BCS PBINVALID
        LDAA PBWIDTH
        BEQ PBINVALID
        CMPA #16
        BHI PBINVALID
        LDAA PBFILL
        CMPA #1
        BHI PBINVALID
        BRA PBVALID
PBINVALID SEC
        RTS
PBVALID LDX #PBOUT
        STX PBPTR
        LDD PBTX
        STD PBPX
        CLR PBCOL
PBCOLUMN LDD #0
        STD PBWORD
        LDD PBTY
        STD PBPY
        CLR PBROW
PBPIXEL JSR PBHIT
        BCC PBWHITE
        LDAB PBROW
        ASLB
        LDX #PBMASKS
        ABX
        LDAA ,X
        ORAA PBWORD
        STAA PBWORD
        LDAA 1,X
        ORAA PBWORD+1
        STAA PBWORD+1
PBWHITE LDD PBPY
        ADDD #1
        STD PBPY
        INC PBROW
        LDAA PBROW
        CMPA #16
        BNE PBPIXEL
        LDD PBWORD
        LDX PBPTR
        STD ,X
        INX
        INX
        STX PBPTR
        LDD PBPX
        ADDD #1
        STD PBPX
        INC PBCOL
        LDAA PBCOL
        CMPA #31
        BNE PBCOLUMN
        CLR ,X
        CLR 1,X
        CLC
        RTS
; Closed rectangle. Border thickness is measured inward, in raster pixels.
PBHIT LDD PBPX
        SUBD PBLEFT
        BCS PBOFF
        LDD PBRIGHT
        SUBD PBPX
        BCS PBOFF
        LDD PBPY
        SUBD PBTOP
        BCS PBOFF
        LDD PBBOTTOM
        SUBD PBPY
        BCS PBOFF
        TST PBFILL
        BNE PBON
        ; D still holds bottom distance; high byte nonzero means >=256.
        BSR PBNEAR
        BCS PBON
        LDD PBPY
        SUBD PBTOP
        BSR PBNEAR
        BCS PBON
        LDD PBPX
        SUBD PBLEFT
        BSR PBNEAR
        BCS PBON
        LDD PBRIGHT
        SUBD PBPX
        BRA PBNEAR
PBON SEC
        RTS
PBOFF CLC
        RTS
PBNEAR TSTA
        BNE PBOFF
        CMPB PBWIDTH
        RTS
; Canon's experimentally validated row permutation (not linear row order).
PBMASKS FDB $1000,$2000,$4000,$8000,$0001,$0002,$0004,$0008
        FDB $0010,$0020,$0040,$0080,$0100,$0200,$0400,$0800
PBEND EQU *
