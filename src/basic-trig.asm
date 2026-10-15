; SIN/COS after the shared recursive argument parser (ids 10/11).
; The selector stays stacked in that parser until its argument is complete.
; SQR scratch can therefore be shared even in SIN(SQR(COS(...)+1)).
; No allocation, motor or peripheral calls. Canon decimal math via SQMATH.
TRSIGN EQU SQCOUNT
TRPTR EQU $1B2C ; Temporary coefficient pointer, below GFRAMES at $1B30.
TRQUAD EQU $1B2E
TRDISPATCH CMPB #10
        BHS TRSTART
        JMP FXDISPATCH
TRSTART SUBB #10
        STAB TRQUAD ; SIN starts quadrant 0, COS starts quadrant 1.
        LDAA DW+8
        ANDA #$80
        TSTB
        BEQ TRKEEPSIGN
        CLRA ; cos(-x)=cos(x).
TRKEEPSIGN STAA TRSIGN
        LDAA DW+8
        ANDA #7
        STAA DW+8
        LDD #SQN
        STD DOUT
        LDX #DW
        JSR SQCOPY
        ; Reject |x| > 1000 before reduction. 1000.0001 is the next
        ; representable number; subtraction must be strictly negative.
        LDX #TRBOUND
        JSR TRSECOND
        LDAA #1
        JSR SQMATH
        TST DERR
        BNE TRRETURN
        TST DW+8
        BMI TRINRANGE
        LDAA #4
        STAA DERR
TRRETURN RTS
TRINRANGE LDD #DW
        STD DOUT
        LDX #SQN
        JSR SQCOPY
        LDX #TRHALFPI
        JSR TRSECOND
        LDAA #3
        JSR SQMATH
        BNE TRRETURN
        ; q=abs(x)/(pi/2). Consume integer digits, accumulating q mod 4,
        ; while clearing them to leave fractional f in DW. No word overflow.
        LDAA DW+8
        ANDA #7
        LDAB #8
        SBA
        NEGA
        TAB ; B=8-scale integer positions, always at least one.
        LDX #DW
        CLRA
TRINTEGER PSHB
        LDAB #10
        MUL
        ADDB ,X
        ANDB #3
        TBA
        PULB
        CLR ,X
        INX
        DECB
        BNE TRINTEGER
        ADDA TRQUAD
        STAA TRQUAD
        BITA #2
        BEQ TRPOSITIVE
        LDAA TRSIGN
        EORA #$80
        STAA TRSIGN
TRPOSITIVE LDX #DW
        LDAB #8
        CLRA
TRCHECKZERO ORAA ,X
        INX
        DECB
        BNE TRCHECKZERO
        TSTA
        BNE TRNOTZERO
        ; Exact reduced quadrants, especially COS(0)=1, must not lose a
        ; unit when passed to INT/FIX for pixel coordinates or loop bounds.
        CLR DW+8
        LDAA TRQUAD
        BITA #1
        BEQ TRZEROEND
        LDD #DW
        STD DOUT
        LDX #TRONE
        JSR SQCOPY
TRZEROEND JMP TRSIGNED
TRNOTZERO LDAA TRQUAD
        BITA #1
        BEQ TRFRACTION
        ; Odd quadrant: sin(pi/2*(1-f)); subtract then take absolute.
        LDX #TRONE
        JSR TRSECOND
        LDAA #1
        JSR SQMATH
        BNE TRDONE
        LDAA DW+8
        ANDA #7
        STAA DW+8
TRFRACTION LDD #SQN
        STD DOUT
        LDX #DW
        JSR SQCOPY ; SQN=f, SQG=f*f.
        LDX #SQN
        JSR TRSECOND
        LDAA #2
        JSR SQMATH
        BNE TRDONE
        LDD #SQG
        STD DOUT
        LDX #DW
        JSR SQCOPY
        LDD #DW
        STD DOUT
        LDX #TRCOEFF
        JSR SQCOPY
        STX TRPTR
TRHORNER LDX #SQG
        JSR TRSECOND
        LDAA #2
        JSR SQMATH
        BNE TRDONE
        LDX TRPTR
        JSR TRSECOND
        STX TRPTR
        CLRA
        JSR SQMATH
        BNE TRDONE
        LDX TRPTR
        CPX #TRCOEFFEND
        BNE TRHORNER
        LDX #SQN
        JSR TRSECOND
        LDAA #2
        JSR SQMATH
        BNE TRDONE
TRSIGNED LDAA DW+8
        ORAA TRSIGN
        STAA DW+8
TRDONE RTS
; Copy nine digits from X into Canon's right operand; X ends after source.
TRSECOND LDD #DW+9
        STD DOUT
        JMP SQCOPY
TREND EQU *
