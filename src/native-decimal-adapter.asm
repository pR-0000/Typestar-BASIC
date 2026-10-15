; OFFLINE PROTOTYPE. Not linked into the released BASIC image.
; S-70 maskROM arithmetic adapter, IRQ masked during transaction.
; A=0 add, 1 subtract, 2 multiply, 3 divide.
; X -> 19-byte non-overlapping caller buffer: R0[9], rhs[9], status[1].
; On accepted call: R0 replaced by result, status=0 or 2 (native error).
; Return A=0/2, 3 insufficient stack, 4 invalid opcode. X preserved.
; Input digits MUST be 0..9, scale 0..7, flags only sign bit7/scale.
; All native scratch saved on stack then zeroed, restored even on error.
; Caller buffer must not overlap protected scratch or stack. Non-reentrant.
; 194 saved bytes; requires entry SP >= $1FE8, rejecting deeper nesting.
; No permanent RAM allocation; this strict stack limit is a prototype limit.
        OPT H01
        ORG $9C00
DECIMAL_CALL CMPA #3
        BLS DECIMAL_OPCODE_OK
        LDAA #4
        RTS
DECIMAL_OPCODE_OK PSHX
        TSX
        CPX #$1FE7
        BCC DECIMAL_STACK_OK
        PULX
        LDAA #3
        RTS
DECIMAL_STACK_OK PSHA
        TPA
        PSHA
        SEI
        LDX #$007C
        LDAB #34
SAVE0   LDAA ,X
        PSHA
        CLR ,X
        INX
        DECB
        BNE SAVE0
        LDX #$18E5
        LDAB #1
SAVE1   LDAA ,X
        PSHA
        CLR ,X
        INX
        DECB
        BNE SAVE1
        LDX #$1DCB
        LDAB #151
SAVE2   LDAA ,X
        PSHA
        CLR ,X
        INX
        DECB
        BNE SAVE2
        LDX #$1E82
        LDAB #2
SAVE3   LDAA ,X
        PSHA
        CLR ,X
        INX
        DECB
        BNE SAVE3
        LDX #$1E8A
        LDAB #3
SAVE4   LDAA ,X
        PSHA
        CLR ,X
        INX
        DECB
        BNE SAVE4
        LDX #$1E93
        LDAB #1
SAVE5   LDAA ,X
        PSHA
        CLR ,X
        INX
        DECB
        BNE SAVE5
        LDX #$1EE6
        LDAB #1
SAVE6   LDAA ,X
        PSHA
        CLR ,X
        INX
        DECB
        BNE SAVE6
; V1 complement carry also wraps to V1+FF=$1F06. Below guarded stack.
        LDAA $1F06
        PSHA
        CLR $1F06
; Saved frame above the 194 bytes: CCR, opcode, original X high/low.
        TSX
        LDX 196,X
        STX $1E82
        LDAB #9
        LDX #$1DCC
COPY_LEFT PSHX
        LDX $1E82
        LDAA ,X
        INX
        STX $1E82
        PULX
        STAA ,X
        INX
        DECB
        BNE COPY_LEFT
        TSX
        LDAA 195,X
        CMPA #2
        BCC RIGHT_R2
        LDX #$1DD5
        BRA COPY_RIGHT_START
RIGHT_R2 LDX #$1DDE
COPY_RIGHT_START LDAB #9
COPY_RIGHT PSHX
        LDX $1E82
        LDAA ,X
        INX
        STX $1E82
        PULX
        STAA ,X
        INX
        DECB
        BNE COPY_RIGHT
        TSX
        LDAA 195,X
        BEQ DO_ADD
        CMPA #1
        BEQ DO_SUB
        CMPA #2
        BEQ DO_MUL
        JSR $CDEA
        BRA MATH_DONE
DO_ADD  JSR $C824
        BRA MATH_DONE
DO_SUB  JSR $C896
        BRA MATH_DONE
DO_MUL  JSR $CC5A
MATH_DONE TSX
        LDX 196,X
        STX $1E82
        LDAB #9
        LDX #$1DCC
COPY_RESULT LDAA ,X
        PSHX
        LDX $1E82
        STAA ,X
        INX
        STX $1E82
        PULX
        INX
        DECB
        BNE COPY_RESULT
        TSX
        LDX 196,X
        LDAA $1DCB
        ANDA #2
        STAA 18,X
        PULA
        STAA $1F06
        LDX #$1EE6
        LDAB #1
RESTORE6 PULA
        STAA ,X
        DEX
        DECB
        BNE RESTORE6
        LDX #$1E93
        LDAB #1
RESTORE5 PULA
        STAA ,X
        DEX
        DECB
        BNE RESTORE5
        LDX #$1E8C
        LDAB #3
RESTORE4 PULA
        STAA ,X
        DEX
        DECB
        BNE RESTORE4
        LDX #$1E83
        LDAB #2
RESTORE3 PULA
        STAA ,X
        DEX
        DECB
        BNE RESTORE3
        LDX #$1E61
        LDAB #151
RESTORE2 PULA
        STAA ,X
        DEX
        DECB
        BNE RESTORE2
        LDX #$18E5
        LDAB #1
RESTORE1 PULA
        STAA ,X
        DEX
        DECB
        BNE RESTORE1
        LDX #$009D
        LDAB #34
RESTORE0 PULA
        STAA ,X
        DEX
        DECB
        BNE RESTORE0
        PULA
        TAP
        PULA               ; discard saved opcode
        PULX
        LDAA 18,X           ; status, CCR arithmetic flags are not preserved
        RTS
