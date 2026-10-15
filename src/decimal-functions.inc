; Decimal ABS/SGN/INT: pure digit operations, no native peripheral calls.
; Function selection is stacked across recursive argument evaluation.
        ORG $43A2 ; Retired integer MFUNC; preserve INPUT prefix below it.
FNAPPLYSTART
FNAPPLY CMPB #3
        BNE FNLOCAL
        JMP FNPEEK
FNLOCAL TSTB
        BEQ FNABS
        CMPB #2
        BNE FNSIGN
        JMP FNINT
FNABS LDAA DW+8
        ANDA #$7F
        STAA DW+8
        RTS
FNSIGN LDAA DW+8
        ANDA #$80
        STAA DDOT
        LDX #DW
        LDAB #8
        CLRA
FNZERO ORAA ,X
        CLR ,X
        INX
        DECB
        BNE FNZERO
        CLR DW+8
        TSTA
        BEQ FNRETURN
        INC DW+7
        LDAA DDOT
        STAA DW+8
FNRETURN RTS
FNAPPLYEND EQU *
        ORG $4756 ; Retired INPUT implementation and legacy RUNFIND.
FNPARSESTART
FNENTRY LDX #FNAMES
        STX DOUT
        CLRB
FNTRY LDX DOUT
        PSHB
        LDAB ,X
        INX
        STX DOUT
        LDX DPTR
FNCHAR LDAA ,X
        ANDA #$DF
        PSHX
        LDX DOUT
        CMPA ,X
        BNE FNMISS
        INX
        STX DOUT
        PULX
        INX
        DECB
        BNE FNCHAR
        PULB
        STX DPTR
        PSHB
        JSR DSPACE
        CMPA #40
        BNE FNBADARG
        JSR DADVANCE
        JSR DEXPR
        TST DERR
        BNE FNARGERROR
        JSR DSPACE
        CMPA #41
        BNE FNBADARG
        JSR DADVANCE
        PULB
        JMP FNAPPLY
FNBADARG LDAA #1
        STAA DERR
FNARGERROR PULB
        RTS
FNMISS PULX
        PULB
        INCB
        CMPB #4
        BEQ FNFALLBACK
        PSHB
        LDAA #5
        MUL
        ADDD #FNAMES
        XGDX
        STX DOUT
        PULB
        BRA FNTRY
FNFALLBACK JSR DSPACE
        JMP DVARIABLE
; Fixed five-byte slots: length + name, padding ignored by comparison.
FNAMES FCB 3
        FCC "ABS "
        FCB 3
        FCC "SGN "
        FCB 3
        FCC "INT "
        FCB 4
        FCC "PEEK"
FNPARSEEND EQU *
        ORG $4E4F ; Retired signed-integer IF comparator; keep KGOSUB intact.
FNINTSTART
FNINT LDAA DW+8
        ANDA #7
        STAA DDIG
        BEQ FNINTRETURN
        CLR DDOT ; OR of discarded fractional digits.
FNSHIFT LDAA DW+7
        ORAA DDOT
        STAA DDOT
        LDX #DW+6
        LDAB #7
FNSHIFTDIG LDAA ,X
        STAA 1,X
        DEX
        DECB
        BNE FNSHIFTDIG
        CLR DW
        DEC DDIG
        BNE FNSHIFT
        LDAA DW+8
        ANDA #$80
        STAA DW+8
        BEQ FNINTRETURN
        TST DDOT
        BEQ FNINTRETURN
; Microsoft-style INT is floor: INT(-1.2)=-2, not truncation toward zero.
        LDX #DW+7
        LDAB #8
FNROUND INC ,X
        LDAA ,X
        CMPA #10
        BCS FNINTRETURN
        CLR ,X
        DEX
        DECB
        BNE FNROUND
        LDAA #4
        STAA DERR
FNINTRETURN RTS
FNINTEND EQU *
        ORG $ABD4 ; Immediately after the token dictionary; before native AC00.
FNPEEKSTART
FNPEEK JSR $A400 ; Exact integral address; same signed aliases as POKE.
        BCS FNPEEKBAD
        XGDX
        LDAB ,X
        CLRA
        STD DOUT
        JMP RDVALUE ; Reuse unsigned word -> decimal digits, no string buffer.
FNPEEKBAD LDAA #4
        STAA DERR
        RTS
FNPEEKEND EQU *
