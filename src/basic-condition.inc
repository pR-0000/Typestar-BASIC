; IF-only signed comparisons. Arithmetic retains its existing + / - rules.
; Return D=0/1 for a comparison, or the unchanged numeric condition.
; Left operand lives on the stack while the right expression uses globals.
; Mask bits: less=1, equal=2, greater=4. No permanent RAM is reserved.
IFCONDITION JSR EXPR
        PSHB
        PSHA
        JSR SPACE
        CMPA #61
        BEQ IFEQUAL
        CMPA #60
        BEQ IFLESS
        CMPA #62
        BEQ IFGREATER
        PULA
        PULB
        RTS
IFEQUAL LDAA #2
        BRA IFCONSUME
IFLESS INX
        LDAA ,X
        CMPA #61
        BEQ IFLESSEQUAL
        CMPA #62
        BEQ IFNOTEQUAL
        LDAA #1
        BRA IFRIGHT
IFLESSEQUAL LDAA #3
        BRA IFCONSUME
IFNOTEQUAL LDAA #5
        BRA IFCONSUME
IFGREATER INX
        LDAA ,X
        CMPA #61
        BEQ IFGREATEREQUAL
        LDAA #4
        BRA IFRIGHT
IFGREATEREQUAL LDAA #6
IFCONSUME INX
IFRIGHT STX CUR
        PSHA
        JSR EXPR
        STD TEMP
        PULA
        STAA OP
        PULA
        PULB
        SUBD TEMP
        BEQ IFISEQUAL
        BLT IFISLESS ; signed N xor V, including 32767 versus -32768
        LDAB #4
        BRA IFMASK
IFISEQUAL LDAB #2
        BRA IFMASK
IFISLESS LDAB #1
IFMASK ANDB OP
        BEQ IFFALSE
        LDAB #1
IFFALSE CLRA
        RTS
