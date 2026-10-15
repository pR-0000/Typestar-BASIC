; DW=left, DW+9=right. Only temporaries inside the existing decimal workspace.
LXAPPLY CMPA #4
        BCC LXEXT
        LDX #DW
        JSR $9C00
        STAA DERR
        RTS
LXEXT CMPA #16
        BCC LXCOMPARE
        PSHA
        LDAA DW+8
        PSHA
        JSR LXINT
        PSHB
        PSHA
        LDX #DW
        LDAB #9
LXCOPYRIGHT LDAA 9,X
        STAA ,X
        INX
        DECB
        BNE LXCOPYRIGHT
        JSR LXINT
        STD DOUT
        PULA
        PULB
        PULX ; X high=left sign/scale, low=operation.
        TST DERR
        BNE LXAPRETURN
        STX DCOPY
        PSHA
        LDAA DCOPY+1
        CMPA #4
        PULA
        BEQ LXMODULO
        PSHA
        LDAA DCOPY+1
        CMPA #5
        PULA
        BNE LXORVALUE
        ANDA DOUT
        ANDB DOUT+1
        BRA LXSIGNED
LXORVALUE ORAA DOUT
        ORAB DOUT+1
LXSIGNED TSTA
        BPL LXUNSIGNED
        STD DOUT
        LDD #0
        SUBD DOUT
        STD DOUT
        JSR RDVALUE
        LDAA #$80
        STAA DW+8
        RTS
LXUNSIGNED STD DOUT
        JMP RDVALUE
LXINT TST DERR
        BNE LXINTBAD
        JSR $A400
        BCC LXAPRETURN
        LDAA #4
        STAA DERR
LXINTBAD SEC
LXAPRETURN RTS
LXCOMPARE ANDA #7
        STAA CMASK
        LDX #DW
        LDAB #9
LXCMPMOVE LDAA ,X
        STAA CLHS-DW,X
        LDAA 9,X
        STAA ,X
        INX
        DECB
        BNE LXCMPMOVE
        JSR CCMPVALUE
        JMP LXFROMBOOL
; MOD: exact integers, sign of dividend, nonzero divisor. Repeated subtraction
; is bounded by 65535 iterations; no division rounding or intermediate overflow.
LXMODULO TST DCOPY
        BPL LXMODPOS
        STD DBOUND
        LDD #0
        SUBD DBOUND
LXMODPOS STD DBOUND
        TST DW+8
        BPL LXMODDIV
        LDD #0
        SUBD DOUT
        STD DOUT
LXMODDIV LDD DOUT
        BNE LXMODSTART
        LDAA #2
        STAA DERR
        RTS
LXMODSTART LDD DBOUND
LXMODLOOP SUBD DOUT
        BCC LXMODLOOP
        ADDD DOUT
        STD DOUT
        JSR RDVALUE
        LDAA DCOPY
        ANDA #$80
        STAA DW+8
        RTS
