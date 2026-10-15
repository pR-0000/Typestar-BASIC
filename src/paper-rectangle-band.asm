; Offline RBRENDER adapter. Caller supplies rectangle in PBSTATE.
; A=band index, B=tile count, X=destination. 3 scratch bytes at PRSTATE.
; Generate each 31x16 tile and copy its 64 bytes into the borrowed band.
PRDEST EQU PRSTATE
PRLEFT EQU PRSTATE+2
PRBAND STX PRDEST
        STAB PRLEFT
        LDAB #16
        MUL
        STD PBTY
        CLRA
        CLRB
        STD PBTX
PRNEXT JSR PBRECT
        BCS PRERROR
        LDX #PBOUT
        LDAB #64
PRCOPY LDAA ,X
        PSHX
        LDX PRDEST
        STAA ,X
        INX
        STX PRDEST
        PULX
        INX
        DECB
        BNE PRCOPY
        LDD PBTX
        ADDD #31
        STD PBTX
        DEC PRLEFT
        BNE PRNEXT
        CLC
        RTS
PRERROR SEC
        RTS
PREND EQU *
