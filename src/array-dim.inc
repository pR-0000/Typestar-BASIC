; DIM A(upper0[,upper1]) for the named decimal array heap.
; CPU integration prototype: placement is supplied by the offline linker.
; One declaration per statement; ':' permits several declarations per line.
; Bounds are inclusive and evaluated by the actual decimal expression engine.
; JOB must be disjoint from expression/native workspaces, stack and arena.
; No arena mutation before BOTH bounds, ')' and EOS have been validated.
DIMJOB EQU $1CDE
DIMDISPATCH JSR SPACE
        LDX #DIMKEY
        JSR MATCH
        BCC DIMCOMMAND
        JSR SPACE ; Replay the displaced EXECUTE entry with the original CUR.
        JMP EXECUTE+3
DIMCOMMAND JSR SPACE
        JSR UPPER
        CMPA #65
        BCS DIMSYN
        CMPA #90
        BHI DIMSYN
        PSHA ; Name must survive array expressions used as bounds.
        INX
        STX CUR
        JSR SPACE
        CMPA #40
        BNE DIMSYN
        INX
        STX CUR
        JSR DIMBOUND
        PSHB
        PSHA ; First bound survives evaluation of the second bound.
        JSR SPACE
        CMPA #44
        BNE DIMONE
        INX
        STX CUR
        JSR DIMBOUND
        PSHB
        PSHA
        LDAA #2
        BRA DIMRANK
DIMONE LDD #1
        PSHB
        PSHA
        LDAA #1
DIMRANK STAA DIMJOB
        JSR SPACE
DIMCLOSE CMPA #41
        BNE DIMSYN
        INX
        STX CUR
        JSR EOS
        PULA
        PULB
        STD DIMJOB+4
        PULA
        PULB
        STD DIMJOB+2
        PULA
        STAA DIMJOB+29
        LDAA #5
        STAA DIMJOB+1
        LDX #DIMJOB
        JSR ARRAY_NAMED_CREATE
        BCC DIMRETURN
        CMPA #1
        BEQ DIMFULL
        CMPA #2
        BEQ DIMDUP
        LDX #DIMRAMMSG
        JMP ERROR
DIMDUP LDX #DIMDUPMSG
        JMP ERROR
DIMFULL JMP PMEMERROR
DIMSYN JMP SYNTAX
DIMRETURN RTS
DIMBOUND LDX CUR
        JSR $A000
        STX CUR
        TSTA
        BEQ DIMCONVERT
        JMP $A518
DIMCONVERT JSR $A400
        BCS DIMRANGE
        STD DIMJOB+14
        BEQ DIMZERO ; -0 is a valid zero bound too.
        TST $1E9C
        BMI DIMRANGE
DIMZERO ADDD #1 ; Inclusive BASIC upper bound -> positive length.
        BCS DIMRANGE ; 65535+1 cannot be represented by the allocator.
        RTS
DIMRANGE JMP RANGEERROR
DIMKEY FCC "DIM"
        FCB 0
DIMDUPMSG FCC "?REDIM"
        FCB 0
DIMRAMMSG FCC "?ARRAY RAM"
        FCB 0
DIMEND EQU *
