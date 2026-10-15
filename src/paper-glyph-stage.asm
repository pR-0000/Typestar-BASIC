; Stage rows as four bytes, MSB at left. The UART graphics buffer is inactive.
SGSTAGE LDX #GXPATTERN
        LDAB #64
SGCLEAR CLR ,X
        INX
        DECB
        BNE SGCLEAR
        LDX #GXPATTERN
        STX SGROWPTR
        CLR SGROW
SGNEXTROW STX SGDEST
        LDAA SGRANK
        CMPA #1
        BNE SGMATRIX
        JSR SGREAD
        LDX #16
        XGDX
        SUBB SGWIDTH
        STAB SGCOL
        XGDX
SGSHIFT TST SGCOL
        BEQ SGWORDREADY
        ASLD
        BCS SGRANGE
        DEC SGCOL
        BRA SGSHIFT
SGWORDREADY LDX SGROWPTR
        STD ,X
        BRA SGROWREADY
SGMATRIX CLR SGCOL
        LDAA #$80
        STAA SGMASK
SGPIXEL JSR SGREAD
        TSTA
        BNE SGRANGE
        CMPB #1
        BHI SGRANGE
        TSTB
        BEQ SGPIXELNEXT
        LDX SGDEST
        LDAA ,X
        ORAA SGMASK
        STAA ,X
SGPIXELNEXT LSR SGMASK
        BNE SGMASKREADY
        LDAA #$80
        STAA SGMASK
        LDX SGDEST
        INX
        STX SGDEST
SGMASKREADY INC SGCOL
        LDAA SGCOL
        CMPA SGWIDTH
        BLO SGPIXEL
SGROWREADY LDX SGROWPTR
        LDAB #4
        ABX
        STX SGROWPTR
        INC SGROW
        LDAA SGROW
        CMPA SGHEIGHT
        BLO SGNEXTROW
        JMP SGSUBMIT
SGRANGE JMP RANGEERROR
; Return an unsigned integer cell. Five-byte decimal payload, no heap write.
SGREAD LDD SGSRC
        ADDD #5
        SUBD SGENDPTR
        BHI SGRANGE
        LDX #DW
        LDAB #5
SGCOPY PSHX
        LDX SGSRC
        LDAA ,X
        INX
        STX SGSRC
        PULX
        STAA ,X
        INX
        DECB
        BNE SGCOPY
        LDX #DW
        JSR $9E03
        JSR $A400
        BCS SGRANGE
        TST DW+8
        BMI SGRANGE
        RTS
SGSTAGEEND EQU *
