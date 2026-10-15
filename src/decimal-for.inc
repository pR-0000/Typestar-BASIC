; Eight decimal FOR frames: id, limit BCD[5], step BCD[5], successor[2].
; Dedicated RAM survives decimal adapter calls; variables remain in the heap.
DFRAMES EQU $1C40
DFSTART EQU $1CB0
DFLIMIT EQU $1CB9
DFSTEP EQU $1CC2
DFTEXT EQU $1CCB
DFSRC EQU $1CCD
DFDST EQU $1CCF
DFDEPTH EQU $1CD1
GCDEPTH EQU $1BB0
        ORG $9D00
        JMP DFOR
DFOR JSR FORRUNONLY
        JSR VARADDR
        LSRB
        ADDB #65
        STAB FVAR
        JSR SPACE
        CMPA #61
        BEQ DFEQUAL
        JMP SYNTAX
DFEQUAL INX
        STX CUR
        JSR CEVAL
        LDX #DFSTART
        JSR DFSTASH
        LDX #KTO
        JSR MATCH
        BCC DFLIMITOK
        JMP SYNTAX
DFLIMITOK JSR CEVAL
        LDX #DFLIMIT
        JSR DFSTASH
        LDX #DFSTEP
        LDAB #9
DFDEFAULT CLR ,X
        INX
        DECB
        BNE DFDEFAULT
        INC DFSTEP+7
        LDX #KSTEP
        JSR MATCH
        BCS DFPARSED
        JSR CEVAL
        LDX #DFSTEP
        JSR DFSTASH
DFPARSED JSR EOS
        LDX #DFSTEP
        JSR CANY
        BNE DFNONZERO
        JMP RANGEERROR
DFNONZERO LDAB FCOUNT
        CMPB #8
        BCS DFCAPACITY
        JMP FORDEPTHERROR
DFCAPACITY LDX #DFRAMES
        TSTB
        BEQ DFASSIGN
DFCHECK LDAA ,X
        CMPA FVAR
        BNE DFCHECKNEXT
        JMP FORVARERROR
DFCHECKNEXT PSHB
        LDAB #13
        ABX
        PULB
        DECB
        BNE DFCHECK
DFASSIGN STX FPTR
        LDX #DFSTART
        JSR DFLOAD
        JSR DFSTOREVAR
        JSR DFCOMPARE
        TSTB
        BNE DFPUSH
        JMP DFSKIP
DFPUSH LDX FPTR
        LDAA FVAR
        STAA ,X
        LDD RNEXT
        STD 11,X
        LDX #DFLIMIT
        JSR DFLOAD
        LDX FPTR
        INX
        JSR DFPACK
        LDX #DFSTEP
        JSR DFLOAD
        LDX FPTR
        LDAB #6
        ABX
        JSR DFPACK
        INC FCOUNT
        RTS
