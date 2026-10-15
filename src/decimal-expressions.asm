; Decimal expression module, offline integration candidate, HD6301.
; Entry A000: X->expression, returns A=status, X->first unconsumed char.
; Result in DW[0..8] (Canon format); errors: 1 syntax, 2 arithmetic,
; 3 depth, 4 literal range. Caller decides which delimiters are permitted.
; Entry A003 formats DW to NUL-terminated DTEXT, X->DTEXT, A=0.
; Supports decimal literals, unary +/- and + - * / with parentheses.
; Dedicated native scratch REQUIRED; never use with current program arena.
; A006: assignment X->A=expression; A009: initialize heap, X->program end.
; A..Z variables allocated on assignment as id+5 BCD bytes; undefined=0.
; No functions yet. No external I/O or UI calls.
        OPT H01
DW      EQU $1E94
DPTR    EQU $1EA7
DERR    EQU $1EA9
DDOT    EQU $1EAA
DDIG    EQU $1EAB
DCH     EQU $1EAC
DOUT    EQU $1EAD
DBOUND  EQU $1EAF
DSTART  EQU $1EB0
DTEXT   EQU $1EB1
DHEAP   EQU $1EBE
DFLOOR  EQU $1EC0
DVAR    EQU $1EC2
DLHS    EQU $1EC3
DCOPY   EQU $1EC4
        ORG $A000
        JMP DECIMAL_EXPR
        JMP DECIMAL_TEXT
        JMP DECIMAL_LET
        JMP DECIMAL_INIT
DECIMAL_EXPR STX DPTR
        CLR DERR
        JSR DEXPR
        LDX DPTR
        LDAA DERR
        RTS
; Skip ASCII spaces without consuming expression punctuation.
DSPACE  LDX DPTR
DSPACE_LOOP LDAA ,X
        CMPA #32
        BNE DSPACE_DONE
        INX
        BRA DSPACE_LOOP
DSPACE_DONE STX DPTR
; Keep input text intact, but accept lowercase variable names like the BASIC.
        CMPA #97
        BCS DSPACE_RETURN
        CMPA #122
        BHI DSPACE_RETURN
        ANDA #$DF
DSPACE_RETURN RTS
DADVANCE LDX DPTR
        INX
        STX DPTR
        RTS
DEXPR   JSR DTERM
DE_LOOP TST DERR
        BNE DE_RETURN
        JSR DSPACE
        CMPA #43
        BEQ DE_PLUS
        CMPA #45
        BNE DE_RETURN
        LDAA #1
        BRA DE_BINARY
DE_PLUS CLRA
DE_BINARY
        PSHA
        LDX #DW
        LDAB #9
DE_SAVE LDAA ,X
        PSHA
        INX
        DECB
        BNE DE_SAVE
        JSR DADVANCE
        JSR DTERM
; Right result goes to second native operand before left is popped.
        LDX #DW
        LDAB #9
DE_RIGHT LDAA ,X
        STAA 9,X
        INX
        DECB
        BNE DE_RIGHT
        LDX #DW+8
        LDAB #9
DE_LEFT PULA
        STAA ,X
        DEX
        DECB
        BNE DE_LEFT
        PULA
        TST DERR
        BNE DE_RETURN
        LDX #DW
        JSR $9C00
        STAA DERR
        JMP DE_LOOP
DE_RETURN RTS
DTERM   JSR DATOM
DT_LOOP TST DERR
        BNE DT_RETURN
        JSR DSPACE
        CMPA #42
        BEQ DT_MULT
        CMPA #47
        BNE DT_RETURN
        LDAA #3
        BRA DT_BINARY
DT_MULT LDAA #2
DT_BINARY
        PSHA
        LDX #DW
        LDAB #9
DT_SAVE LDAA ,X
        PSHA
        INX
        DECB
        BNE DT_SAVE
        JSR DADVANCE
        JSR DATOM
; Right result goes to second native operand before left is popped.
        LDX #DW
        LDAB #9
DT_RIGHT LDAA ,X
        STAA 9,X
        INX
        DECB
        BNE DT_RIGHT
        LDX #DW+8
        LDAB #9
DT_LEFT PULA
        STAA ,X
        DEX
        DECB
        BNE DT_LEFT
        PULA
        TST DERR
        BNE DT_RETURN
        LDX #DW
        JSR $9C00
        STAA DERR
        JMP DT_LOOP
DT_RETURN RTS
; Conservative guard leaves room for the reserved adapter's own guard.
DATOM   TSX
        CPX #$1F80
        BCC DA_SAFE
        LDAA #3
        STAA DERR
        RTS
DA_SAFE JSR DSPACE
        CMPA #43
        BEQ DA_PLUS
        CMPA #45
        BEQ DA_MINUS
        CMPA #40
        BEQ DA_GROUP
        CMPA #65
        BCS DA_NUMBER
        CMPA #90
        BHI DA_NUMBER
        JMP DVARIABLE
DA_NUMBER JMP DNUMBER
DA_PLUS JSR DADVANCE
        JSR DATOM
        RTS
DA_MINUS JSR DADVANCE
        JSR DATOM
        LDAA DW+8
        EORA #$80
        STAA DW+8
        RTS
DA_GROUP JSR DADVANCE
        JSR DEXPR
        TST DERR
        BNE DA_RETURN
        JSR DSPACE
        CMPA #41
        BNE DSYNTAX
        JMP DADVANCE
DA_RETURN RTS
DSYNTAX LDAA #1
        STAA DERR
        RTS
DRANGE  LDAA #4
        STAA DERR
        RTS
DNUMBER LDX #DW
        LDAB #9
DN_CLEAR CLR ,X
        INX
        DECB
        BNE DN_CLEAR
        CLR DDOT
        CLR DDIG
DN_NEXT LDX DPTR
        LDAA ,X
        CMPA #46
        BNE DN_DIGIT
        TST DDOT
        BNE DN_DONE
        INC DDOT
        JSR DADVANCE
        BRA DN_NEXT
DN_DIGIT CMPA #48
        BCS DN_DONE
        CMPA #57
        BHI DN_DONE
        SUBA #48
        STAA DCH
        TST DW
        BNE DRANGE
        TST DDOT
        BEQ DN_SHIFT
        LDAA DW+8
        CMPA #7
        BCC DRANGE
        INC DW+8
DN_SHIFT LDX #DW
        LDAB #7
DN_SHIFT_LOOP LDAA 1,X
        STAA ,X
        INX
        DECB
        BNE DN_SHIFT_LOOP
        LDAA DCH
        STAA DW+7
        INC DDIG
        JSR DADVANCE
        BRA DN_NEXT
DN_DONE TST DDIG
        BEQ DSYNTAX
        RTS
; Formatter preserves DW; only its text scratch is modified. No Canon UI call.
DECIMAL_TEXT LDX #DTEXT
        STX DOUT
        CLR DSTART
        LDAA DW+8
        ANDA #15
        LDAB #8
        SBA
        NEGA
        STAA DBOUND
; Emit minus only for nonzero coefficient (avoid negative zero).
        LDX #DW
        LDAB #8
        CLRA
DF_ZERO ORAA ,X
        INX
        DECB
        BNE DF_ZERO
        TSTA
        BEQ DF_BEGIN
        LDAA DW+8
        BPL DF_BEGIN
        LDAA #45
        JSR DEMIT
DF_BEGIN CLRB
DF_LOOP CMPB DBOUND
        BNE DF_DIGIT
        LDAA #46
        JSR DEMIT
DF_DIGIT LDX #DW
        ABX
        LDAA ,X
        BNE DF_EMIT
        TST DSTART
        BNE DF_EMIT
        PSHA
        LDAA DBOUND
        DECA
        STAA DCH
        PULA
        CMPB DCH
        BCS DF_NEXT
DF_EMIT INC DSTART
        ADDA #48
        JSR DEMIT
DF_NEXT INCB
        CMPB #8
        BNE DF_LOOP
        CLRA
        JSR DEMIT
        LDX #DTEXT
        CLRA
        RTS
DEMIT PSHX
        LDX DOUT
        STAA ,X
        INX
        STX DOUT
        PULX
        RTS

; Volatile variable heap grows downward from 1DCB, never across DFLOOR.
; DFLOOR must track the actual end of the program including its sentinel.
; The BASIC integration must reset/reconcile this heap on program edits.
DECIMAL_INIT CPX #$1B80
        BCS DI_BAD
        CPX #$1DCB
        BHI DI_BAD
        STX DFLOOR
        LDX #$1DCB
        STX DHEAP
        CLR DERR
        CLRA
        RTS
DI_BAD  LDAA #5
        STAA DERR
        RTS
DFIND   LDX DHEAP
        LDAA DVAR
DFIND_LOOP CPX #$1DCB
        BEQ DFIND_DONE
        CMPA ,X
        BEQ DFIND_DONE
        LDAB #6
        ABX
        BRA DFIND_LOOP
DFIND_DONE RTS
DVARIABLE STAA DVAR
        JSR DADVANCE
        JSR DFIND
        CPX #$1DCB
        BEQ DV_ZERO
        INX
        STX DCOPY
        LDX #DW
        LDAB #5
DV_COPY PSHX
        LDX DCOPY
        LDAA ,X
        INX
        STX DCOPY
        PULX
        STAA ,X
        INX
        DECB
        BNE DV_COPY
        LDX #DW
        JSR $9E03
        RTS
DV_ZERO LDX #DW
        LDAB #9
DV_CLEAR CLR ,X
        INX
        DECB
        BNE DV_CLEAR
        RTS
DECIMAL_LET STX DPTR
        CLR DERR
        JSR DSPACE
        CMPA #65
        BCS DL_SYNTAX
        CMPA #90
        BHI DL_SYNTAX
        STAA DLHS
        JSR DADVANCE
        JSR DSPACE
        CMPA #61
        BNE DL_SYNTAX
        JSR DADVANCE
        JSR DEXPR
        TST DERR
        BNE DL_RETURN
        JSR DSPACE
        TSTA
        BNE DL_SYNTAX
; Commit only after expression and end-of-statement both validated.
        LDAA DLHS
        STAA DVAR
        JSR DFIND
        CPX #$1DCB
        BNE DL_HAVE_SLOT
        LDD DHEAP
        SUBD #6
        XGDX
        CPX DFLOOR
        BCS DL_NO_ROOM
        STX DHEAP
        LDAA DLHS
        STAA ,X
DL_HAVE_SLOT INX
        STX DCOPY
        LDX #DW
        JSR $9E00
        LDX #DW
        LDAB #5
DL_COPY LDAA ,X
        PSHX
        LDX DCOPY
        STAA ,X
        INX
        STX DCOPY
        PULX
        INX
        DECB
        BNE DL_COPY
        LDX #DW
        JSR $9E03
DL_RETURN LDAA DERR
        LDX DPTR
        RTS
DL_SYNTAX JSR DSYNTAX
        BRA DL_RETURN
DL_NO_ROOM LDAA #5
        STAA DERR
        BRA DL_RETURN
