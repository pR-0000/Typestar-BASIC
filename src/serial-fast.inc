; Five hardware Timer2 rates; reuse the old parser footprint for a table
; and a bounded BREAK-only matrix poll. No IRQ or additional RAM.
        ORG $8FF2
RPARSE JSR EXPR
        PSHB
        PSHA
        JSR EOS
        PULA
        PULB
        JMP RLOOKUP
RPEND EQU *
        ORG $9044
; Divider zero is valid (31250), not an uninitialized/default sentinel.
; Accept hardware constants 0..3 or 12; other values fall back to 1200.
RAPPLY LDAA BAUDCONST
        CMPA #3
        BLS SBAPPLYOK
        CMPA #12
        BEQ SBAPPLYOK
        LDAA #25
RAEND EQU *
        ORG $90B1
RPPATCH JMP RPARSE
; Return Z=1 for BREAK, Z=0 otherwise. Unlike KBDSCAN this preserves X.
; B is scratch, as in KBDSCAN. Two samples match the existing electrical
; settling convention. Always deselect the row before returning.
RFASTBREAK LDAB #$BF ; raw $36 = row 6, column 6
        STAB $31
        LDAA $30
        ORAA $30
        LDAB #$FF
        STAB $31
        BITA #$40
        RTS
RATETABLE FDB 1200
        FCB 25
        FDB 2400
        FCB 12
        FDB 7812
        FCB 3
        FDB 15625
        FCB 1
        FDB 31250
        FCB 0
RTEND EQU *
        ORG $925E
RLOOKUP LDX #RATETABLE
RTRY SUBD ,X
        BEQ RFOUND
        ADDD ,X
        INX
        INX
        INX
        CPX #RTEND
        BNE RTRY
        JMP RANGEERROR
RFOUND LDAA 2,X
        RTS
RFLOOKEND EQU *
