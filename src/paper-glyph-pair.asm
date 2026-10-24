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
        TST SGRANK
        BNE SGMATRIX
        JSR SGREAD
        LDX #16
        XGDX
        SUBB SGWIDTH
        STAB SGCOL
        XGDX
SGSHIFT TST SGCOL
        BMI SGPAIR
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
; Width 32 consumes two consecutive 16-bit words for each source row.
SGPAIR LDX SGROWPTR
        STD ,X
        PSHX
        JSR SGREAD
        PULX
        STD 2,X
        BRA SGROWREADY
; Return an unsigned integer cell. Five-byte decimal payload, no heap write.
SGREAD LDD SGSRC
        ADDD #5
        SUBD SGENDPTR
        BHI SGRANGE
        LDX SGSRC
        JSR DFUNPACK
        LDD DFSRC
        STD SGSRC
        JSR $A400
        BCS SGRANGE
        TST DW+8
        BMI SGRANGE
        RTS
SGSTAGEEND EQU *
