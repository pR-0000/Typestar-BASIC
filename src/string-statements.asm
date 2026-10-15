; A006 retains the numeric/array assignment gateway when LHS has no '$'.
STLET STX DPTR
        CLR DERR
        JSR DSPACE
        LDAB 1,X
        CMPB #36
        BEQ STASSIGN
        JMP STOLDLET
STASSIGN JSR STNAME
        JSR DSPACE
        CMPA #61
        BNE STSYNTAX
        JSR DADVANCE
        CLR STMODE
        JSR STEXPR
        JSR DSPACE
        TSTA
        BNE STSYNTAX
        JMP STSTORE
STNAME CMPA #65
        BLO STSYNTAX
        CMPA #90
        BHI STSYNTAX
        ORAA #$80
        STAA STLHS
        INX
        INX
        STX DPTR
        RTS
STSYNTAX JMP SYNTAX
; Called for all PRINT items. Numeric path remains the existing bridge.
STPRINT LDX CUR
        STX DPTR
        CLR DERR
        JSR STISSTR
        BCS STPRINTSTR
        JMP PRINTNUM
STPRINTSTR LDAA #1
        STAA STMODE
        JSR STEXPR
        LDX DPTR
        STX CUR
        JMP PRINTSEP
; LPRINT strings append to the current staged output, with no temporary
; writes into BUF. The existing 72-column preflight still precedes heating.
STLPRINT LDX CUR
        STX DPTR
        CLR DERR
        JSR STISSTR
        BCS STLPRINTSTR
        JMP LVNUMBER
STLPRINTSTR LDAA #2
        STAA STMODE
        JSR STEXPR
        LDX DPTR
        STX CUR
        JMP LVSEPARATOR
STSTATEMENTSEND EQU *
