; Native decimal extensions. Arguments are completely evaluated before entry.
; Scratch borrows the inactive graphics/LPRINT key buffer; never used during
; printing or serial graphics reception. SQN/SQG remain owned by SIN/COS/SQR.
XMARG EQU GXPATTERN
XMTERM EQU GXPATTERN+9
XMSUM EQU GXPATTERN+18
XMSQUARE EQU GXPATTERN+27
XMEXPONENT EQU GXPATTERN+36
XMSP EQU GXPATTERN+45
XMSIGN EQU GXPATTERN+47
XMCOUNT EQU GXPATTERN+48
XMN EQU GXPATTERN+49
XMFLAGS EQU GXPATTERN+51
XMDISPATCH CMPB #12
        BHS XMSTART
        JMP TRDISPATCH
XMSTART STS XMSP
        CMPB #12
        BEQ XMTANJ
        CMPB #13
        BEQ XMATNJ
        CMPB #14
        BEQ XMLOGJ
        JMP XMEXP
XMTANJ JMP XMTAN
XMATNJ JMP XMATN
XMLOGJ JMP XMLOG
; X source/destination, nine unpacked Canon decimal bytes.
XMLOAD LDD #DW
        STD DOUT
        JMP SQCOPY
XMSAVE STX DOUT
        LDX #DW
        JMP SQCOPY
XMADD CLRA
        BRA XMOP
XMSUB LDAA #1
        BRA XMOP
XMMUL LDAA #2
        BRA XMOP
XMDIV LDAA #3
XMOP PSHA
        JSR TRSECOND
        PULA
        JSR SQMATH
        BEQ XMRET
XMFAIL LDS XMSP
XMRET RTS
XMRANGE LDAA #4
        STAA DERR
        BRA XMFAIL
; Test zero coefficient without modifying DW or its sign/scale.
XMZERO LDX #DW
        LDAB #8
        CLRA
XMZLOOP ORAA ,X
        INX
        DECB
        BNE XMZLOOP
        TSTA
        RTS
XMABS LDAA DW+8
        ANDA #7
        STAA DW+8
        RTS
; Divide DW by the small positive integer XMCOUNT (1..99).
XMDIVCOUNT LDX #DW+9
        JSR SQZERO
        CLRB
        LDAA XMCOUNT
XMDTENS CMPA #10
        BLO XMDDIGITS
        SUBA #10
        INCB
        BRA XMDTENS
XMDDIGITS STAB DW+15
        STAA DW+16
        LDAA #3
        JSR SQMATH
        BNE XMFAIL
        RTS
XMCOREEND EQU *
