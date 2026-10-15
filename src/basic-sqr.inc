; Newton sqrt using native decimal division/addition.
SQN EQU $1B19
SQG EQU $1B22
SQCOUNT EQU $1B2B
        ORG $4B93
SQENTRY LDX DPTR
        LDAB #3
        PSHX
        LDX #SQINNAME
        STX DOUT
        PULX
SQCHAR LDAA ,X
        ANDA #$DF
        PSHX
        LDX DOUT
        CMPA ,X
        BNE SQMISS
        INX
        STX DOUT
        PULX
        INX
        DECB
        BNE SQCHAR
        STX DPTR
        JSR DSPACE
        CMPA #40
        BNE SQSYNTAX
        JSR DADVANCE
        JSR DEXPR
        TST DERR
        BNE SQRETURN2
        JSR DSPACE
        CMPA #41
        BNE SQSYNTAX
        JSR DADVANCE
        JMP SQROOT
SQSYNTAX LDAA #1
        STAA DERR
SQRETURN2 RTS
SQMISS PULX
        JMP FRENTRY
SQINNAME FCC "SQR"
; X source, DOUT destination, nine bytes. No persistent pointer state.
SQCOPY LDAB #9
SQCP LDAA ,X
        PSHX
        LDX DOUT
        STAA ,X
        INX
        STX DOUT
        PULX
        INX
        DECB
        BNE SQCP
        RTS
SQZERO LDAB #9
SQZ CLR ,X
        INX
        DECB
        BNE SQZ
        RTS
SQMATH LDX #DW
        JSR $9C00
        STAA DERR
        RTS
SQROOT LDX #DW
        LDAB #8
        CLRA
SQISZERO ORAA ,X
        INX
        DECB
        BNE SQISZERO
        TSTA
        BEQ SQZERORESULT
        JMP SQNONZERO
SQZERORESULT
        CLR DW+8
        RTS
SQPARSEEND EQU *
        ORG $9192
SQNONZERO LDAA DW+8
        BPL SQPOS
        LDAA #4
        STAA DERR
        RTS
SQPOS LDX #DW
        LDAB #8
SQLEAD TST ,X
        BNE SQDIGITS
        INX
        DECB
        BRA SQLEAD
SQDIGITS LDAA DW+8
        ANDA #7
        STAA SQCOUNT
        TBA
        SUBA SQCOUNT
        INCA
        ASRA
        STAA SQCOUNT
        LDD #SQN
        STD DOUT
        LDX #DW
        JSR SQCOPY
        LDX #DW
        JSR SQZERO
        LDAA SQCOUNT
        BMI SQSMALL
        LDAB #7
        SBA
        NEGA
        TAB
        LDX #DW
        ABX
        INC ,X
        BRA SQGUESS
SQSMALL NEGA
        STAA DW+8
        INC DW+7
SQGUESS
        LDD #SQG
        STD DOUT
        LDX #DW
        JSR SQCOPY
        LDAA #10
        STAA SQCOUNT
SQLOOP LDD #DW
        STD DOUT
        LDX #SQN
        JSR SQCOPY
        LDD #DW+9
        STD DOUT
        LDX #SQG
        JSR SQCOPY
        LDAA #3
        JSR SQMATH
        BNE SQDONE
        LDD #DW+9
        STD DOUT
        LDX #SQG
        JSR SQCOPY
        CLRA
        JSR SQMATH
        BNE SQDONE
        LDX #DW+9
        JSR SQZERO
        LDAA #2
        STAA DW+16
        LDAA #3
        JSR SQMATH
        BNE SQDONE
        LDD #SQG
        STD DOUT
        LDX #DW
        JSR SQSAFE
        DEC SQCOUNT
        BNE SQLOOP
SQDONE RTS
SQEND EQU *

; Retired native-font dispatcher: cap long divisor coefficients to six
; significant positions to avoid the Canon divide boundary at 9999999x.
; DW retains the full final estimate; only the next divisor is shortened.
        ORG $9003
SQSAFE JSR SQCOPY
        LDAA SQG
        ORAA SQG+1
        BEQ SQSAFERET
        CLR SQG+6
        CLR SQG+7
SQSAFERET RTS
SQSAFEEND EQU *
