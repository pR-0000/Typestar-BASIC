; Substrings use one reusable 65-byte payload (74-byte object) per active level.
; Object names $80..$87 differ from A$..Z$ ($C1..$DA) and the drawing list (0).
; Existing arrays/scalars never move. A returned view is consumed immediately,
; before the same level's scratch object can be reused by the following atom.
STSUB STX DPTR
        PSHB
        JSR DSPACE
        CMPA #40
        BEQ STSUBOPEN
        JMP SYNTAX
STSUBOPEN JSR DADVANCE
        PULB
        LDAA STMODE
        PSHA
        LDAA STLEN
        PSHA
        LDAA STFIRST
        PSHA
        LDX STDEST
        PSHX
        PSHB
        JSR STSCRATCH
        INX
        STX STDEST
        LDAA #4
        STAA STMODE
        JSR STEXPR
        LDAA STLEN
        PSHA
        LDX STDEST
        PSHX
        JSR DSPACE
        CMPA #44
        BEQ STSUBINDEX
        JMP SYNTAX
STSUBINDEX
        JSR DADVANCE
        JSR STINTARG
        PSHB
        PSHA
        JSR DSPACE
        CMPA #44
        BNE STSUBDEFAULT
        TSX
        LDAA 5,X ; kind above index, source pointer and source length
        CMPA #5
        BEQ STSUBEXPLICIT
        JMP SYNTAX
STSUBEXPLICIT
        JSR DADVANCE
        JSR STINTARG
        BRA STSUBCOUNT
STSUBDEFAULT LDD #63
STSUBCOUNT STD STCOUNT
        JSR DSPACE
        CMPA #41
        BNE STSUBBAD
        JSR DADVANCE
        PULA
        PULB
        STD STARG
        PULX
        STX STDEST
        PULA
        STAA STLEN
        PULB
        CMPB #5
        BEQ STMID
        PSHB
        LDD STARG
        JSR STCLAMP
        PULA
        CMPA #3
        BEQ STSUBRETURN
        STAB STRESULTLEN
        LDAA STLEN
        SBA
        TAB
        ABX
        LDAB STRESULTLEN
        BRA STSUBRETURN
STMID LDD STARG
        BEQ STSUBRANGE
        SUBD #1
        TSTA
        BNE STEMPTYVIEW
        CMPB STLEN
        BHS STEMPTYVIEW
        ABX
        LDAA STLEN
        SBA
        STAA STLEN
        LDD STCOUNT
        JSR STCLAMP
        BRA STSUBRETURN
STEMPTYVIEW CLRB
STSUBRETURN STX STRESULTPTR
        STAB STRESULTLEN
        PULX
        STX STDEST
        PULA
        STAA STFIRST
        PULA
        STAA STLEN
        PULA
        STAA STMODE
        DEC STDEPTH
        LDX STRESULTPTR
        LDAB STRESULTLEN
        RTS
STCLAMP TSTA
        BNE STCLAMPALL
        CMPB STLEN
        BLS STCLAMPRET
STCLAMPALL LDAB STLEN
STCLAMPRET RTS
STSUBBAD JMP SYNTAX
STSUBRANGE JMP RANGEERROR
STSUBEND EQU *
