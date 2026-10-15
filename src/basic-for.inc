; Eight nested FOR frames share LIST's buffer (LIST is direct-mode only).
; Frame: variable byte offset, signed limit word, signed step word, FOR line.
FCOUNT EQU $1974
FPTR EQU $1975
FSTART EQU $1977
FLIMIT EQU $1979
FSTEP EQU $197B
FVAR EQU $197D
FSKIP EQU $197E
FFRAMES EQU $1B00
KFOR FCC "FOR"
        FCB 0
KNEXT FCC "NEXT"
        FCB 0
KTO FCC "TO"
        FCB 0
KSTEP FCC "STEP"
        FCB 0
FORDISPATCH LDX #KFOR
        JSR MATCH
        BCS FORTRYNEXT
        JMP FORCOMMAND
FORTRYNEXT LDX #KNEXT
        JSR MATCH
        BCS FORFALLBACK
        JMP NEXTCOMMAND
FORFALLBACK JMP $481B
FORRUNONLY TST RUNNING
        BNE FORRUNOK
        JMP MODEERROR
FORRUNOK RTS
FORCOMMAND JSR FORRUNONLY
        JSR VARADDR
        STAB FVAR
        JSR SPACE
        CMPA #61
        BEQ FOREQUAL
        JMP SYNTAX
FOREQUAL INX
        STX CUR
        JSR EXPR
        STD FSTART
        LDX #KTO
        JSR MATCH
        BCC FORLIMIT
        JMP SYNTAX
FORLIMIT JSR EXPR
        STD FLIMIT
        LDD #1
        STD FSTEP
        LDX #KSTEP
        JSR MATCH
        BCS FORPARSED
        JSR EXPR
        STD FSTEP
FORPARSED JSR EOS
        LDD FSTEP
        BNE FORNONZERO
        JMP RANGEERROR
FORNONZERO LDAA FCOUNT
        CMPA #8
        BCS FORCAPACITY
        JMP FORDEPTHERROR
; Reject nesting the same variable: it would alter the enclosing counter.
FORCAPACITY LDX #FFRAMES
        LDAB FCOUNT
        BEQ FORASSIGN
FORCHECKVAR LDAA ,X
        CMPA FVAR
        BNE FORCHECKNEXT
        JMP FORVARERROR
FORCHECKNEXT PSHB
        LDAB #6
        ABX
        PULB
        DECB
        BNE FORCHECKVAR
FORASSIGN STX FPTR
        LDX #VARS
        LDAB FVAR
        ABX
        LDD FSTART
        STD ,X
        TST FSTEP
        BMI FORDESCENDING
        ; TST changes N/Z/V: repeat the signed comparison after testing step.
        LDD FSTART
        SUBD FLIMIT
        BGT FORSKIP
        BRA FORPUSH
FORDESCENDING LDD FSTART
        SUBD FLIMIT
        BLT FORSKIP
FORPUSH LDX FPTR
        LDAA FVAR
        STAA ,X
        LDD FLIMIT
        STD 1,X
        LDD FSTEP
        STD 3,X
        LDAA LINE
        STAA 5,X
        INC FCOUNT
        RTS
; Zero-trip loops skip complete nested FOR/NEXT blocks, one statement/line.
; REM and quoted PRINT text cannot be mistaken for structural keywords.
FORSKIP CLR FSKIP
FORSCAN INC LINE
        LDAA LINE
        BNE FORSCANLINE
        JMP FORPAIRERROR
; Skip absent numbers without keyboard debounce; still poll before examining
; each real statement while matching a zero-trip FOR/NEXT pair.
FORSCANLINE JSR SLOT
        LDAA ,X
        BEQ FORSCAN
        JSR POLLIN
        CMPA #3
        BNE FORSCANREAD
        JMP BREAK
FORSCANREAD JSR SLOT
        STX CUR
        JSR SPACE
        LDX #KFOR
        JSR MATCH
        BCS FORSCANNEXT
        INC FSKIP
        BRA FORSCAN
FORSCANNEXT LDX #KNEXT
        JSR MATCH
        BCS FORSCAN
        TST FSKIP
        BEQ FORSCANEND
        DEC FSKIP
        BRA FORSCAN
FORSCANEND JSR SPACE
        TSTA
        BEQ FORSCANRET
        JSR VARADDR
        CMPB FVAR
        BEQ FORSCANVALID
        JMP FORPAIRERROR
FORSCANVALID JSR EOS
FORSCANRET RTS
NEXTCOMMAND JSR FORRUNONLY
        LDAA FCOUNT
        BNE NEXTHASFRAME
        JMP FORPAIRERROR
NEXTHASFRAME JSR $4821
        DECA
        TAB
        ASLA
        STAA TEMP
        ASLA
        ADDA TEMP
        TAB
        LDX #FFRAMES
        ABX
        STX FPTR
        JSR SPACE
        TSTA
        BEQ NEXTVALIDATE
        JSR VARADDR
        LDX FPTR
        CMPB ,X
        BEQ NEXTVALIDATE
        JMP FORPAIRERROR
NEXTVALIDATE JSR EOS
        LDX FPTR
        LDD 1,X
        STD FLIMIT
        LDD 3,X
        STD FSTEP
        LDAB ,X
        LDX #VARS
        ABX
        LDD ,X
        ADDD FSTEP
        BVS NEXTPOP ; Overflow terminates without wrapping into another loop.
        STD ,X
        TST FSTEP
        BMI NEXTDOWN
        LDD ,X
        SUBD FLIMIT
        BLE NEXTREPEAT
        BRA NEXTPOP
NEXTDOWN LDD ,X
        SUBD FLIMIT
        BGE NEXTREPEAT
NEXTPOP DEC FCOUNT
        RTS
NEXTREPEAT LDX FPTR
        LDAA 5,X
        STAA LINE ; RUN increments to the line following FOR, even if sparse.
        RTS
FORFINISH JMP $481E
FORPAIRERROR LDX #FORPAIRMSG
        JMP ERROR
FORDEPTHERROR LDX #FORDEPTHMSG
        JMP ERROR
FORVARERROR LDX #FORVARMSG
        JMP ERROR
FORPAIRMSG FCC "?FOR/NEXT"
        FCB 13,10,0
FORDEPTHMSG FCC "?FOR DEPTH"
        FCB 13,10,0
FORVARMSG FCC "?FOR VARIABLE"
        FCB 13,10,0
