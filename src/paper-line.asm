; Offline HD6301 segment rasterizer. Not linked into the released firmware.
; PLSTATE (40 bytes) and PLOUT (64 bytes) are supplied by the test linker.
; Input: four byte coordinates x1,y1,x2,y2, width 1..16, native tile ox,oy.
; Coordinates use the validated logical units: native Y=floor(logical Y/2).
; Output: 31 columns x16 rows, Canon bit order, two zero guard bytes.
; Bounds: X<=247,Y<=255, tile ox<=247,oy<=127. Invalid input leaves output
; untouched and returns carry. Otherwise output is replaced, carry clear.
; Endpoints are canonicalized (X, then Y) for direction-independent ties.
; Stroke is a square brush centred on each Bresenham point. Even widths
; have the extra column/row towards positive coordinates. Clipped at page edge.
; No motors, heap, serial or firmware scratch touched. X/A/B clobbered.
PLX1 EQU PLSTATE
PLY1 EQU PLSTATE+1
PLX2 EQU PLSTATE+2
PLY2 EQU PLSTATE+3
PLWIDTH EQU PLSTATE+4
PLOX EQU PLSTATE+5
PLOY EQU PLSTATE+6
PLX EQU PLSTATE+7
PLY EQU PLSTATE+9
PLDX EQU PLSTATE+11
PLDY EQU PLSTATE+13
PLSY EQU PLSTATE+15
PLERR EQU PLSTATE+17
PLE2 EQU PLSTATE+19
PLLOW EQU PLSTATE+21
PLSX EQU PLSTATE+23
PLSX0 EQU PLSTATE+25
PLSYDOT EQU PLSTATE+27
PLNX EQU PLSTATE+29
PLNY EQU PLSTATE+30
PLCOLUMN EQU PLSTATE+31
PLROW EQU PLSTATE+32
PLMASK EQU PLSTATE+33
PLTARGET EQU PLSTATE+35
PLENDX EQU PLSTATE+37
PLENDY EQU PLSTATE+38
PLLINE LDAA PLX1
        CMPA #247
        BHI PLBAD
        LDAA PLX2
        CMPA #247
        BHI PLBAD
        LDAA PLOX
        CMPA #247
        BHI PLBAD
        LDAA PLOY
        CMPA #127
        BHI PLBAD
        LDAA PLWIDTH
        BEQ PLBAD
        CMPA #16
        BHI PLBAD
        BRA PLVALID
PLBAD SEC
        RTS
PLVALID LDX #PLOUT
        LDAB #64
PLZERO CLR ,X
        INX
        DECB
        BNE PLZERO
        ; Lower stroke offset = floor((width-1)/2).
        CLRA
        LDAB PLWIDTH
        DECB
        LSRB
        STD PLLOW
        LDAA PLX1
        CMPA PLX2
        BHI PLSWAP
        BLO PLFORWARD
        LDAA PLY1
        CMPA PLY2
        BHI PLSWAP
PLFORWARD CLRA
        LDAB PLX1
        STD PLX
        LDAB PLY1
        STD PLY
        LDAA PLX2
        STAA PLENDX
        LDAA PLY2
        STAA PLENDY
        BRA PLINIT
PLSWAP CLRA
        LDAB PLX2
        STD PLX
        LDAB PLY2
        STD PLY
        LDAA PLX1
        STAA PLENDX
        LDAA PLY1
        STAA PLENDY
PLINIT CLRA
        LDAB PLENDX
        SUBD PLX
        STD PLDX
        LDD #1
        STD PLSY
        CLRA
        LDAB PLENDY
        SUBD PLY
        BPL PLDYOK
        COMA
        COMB
        ADDD #1
        LDX #$FFFF
        STX PLSY
PLDYOK STD PLDY
        LDD PLDX
        SUBD PLDY
        STD PLERR
PLPOINT JSR PLSTAMP
        LDAB PLX+1
        CMPB PLENDX
        BNE PLSTEP
        LDAB PLY+1
        CMPB PLENDY
        BNE PLSTEP
        CLC
        RTS
PLSTEP LDD PLERR
        ASLB
        ROLA
        STD PLE2
        ; e2 >= -dy, signed. Magnitudes never exceed 510.
        ADDD PLDY
        BMI PLNOX
        LDD PLERR
        SUBD PLDY
        STD PLERR
        LDX PLX
        INX
        STX PLX
PLNOX LDD PLE2
        SUBD PLDX
        BGT PLPOINT
        LDD PLERR
        ADDD PLDX
        STD PLERR
        LDD PLY
        ADDD PLSY
        STD PLY
        BRA PLPOINT
; Stamp in logical units, then fold pairs of Y rows onto native dots.
; Duplicate writes are ORs. This avoids gaps along steep diagonals.
PLSTAMP LDD PLX
        SUBD PLLOW
        STD PLSX0
        LDD PLY
        SUBD PLLOW
        STD PLSYDOT
        LDAA PLWIDTH
        STAA PLNY
PLSTAMPY LDD PLSX0
        STD PLSX
        LDAA PLWIDTH
        STAA PLNX
PLSTAMPX JSR PLDOT
        LDX PLSX
        INX
        STX PLSX
        DEC PLNX
        BNE PLSTAMPX
        LDX PLSYDOT
        INX
        STX PLSYDOT
        DEC PLNY
        BNE PLSTAMPY
        RTS
; Clip before subtracting tile origin: negative/wrapped stroke coordinates
; and coordinates beyond the public page limit must never reach the buffer.
PLDOT LDD PLSX
        TSTA
        BNE PLDOTEND
        CMPB #247
        BHI PLDOTEND
        SUBB PLOX
        BCS PLDOTEND
        CMPB #31
        BHS PLDOTEND
        STAB PLCOLUMN
        LDD PLSYDOT
        TSTA
        BNE PLDOTEND
        LSRB
        SUBB PLOY
        BCS PLDOTEND
        CMPB #16
        BHS PLDOTEND
        ASLB
        LDX #PLMASKS
        ABX
        LDD ,X
        STD PLMASK
        LDAB PLCOLUMN
        ASLB
        LDX #PLOUT
        ABX
        LDAA ,X
        ORAA PLMASK
        STAA ,X
        LDAA 1,X
        ORAA PLMASK+1
        STAA 1,X
PLDOTEND RTS
PLMASKS FDB $1000,$2000,$4000,$8000,$0001,$0002,$0004,$0008
        FDB $0010,$0020,$0040,$0080,$0100,$0200,$0400,$0800
PLCODEEND EQU *
