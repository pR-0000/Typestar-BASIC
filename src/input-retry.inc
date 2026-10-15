; .86: replace exactly $A74E..$A75F, leaving parser and store entry intact.
; Invalid numeric replies retry the editor without committing the variable.
; READINPUT clears its buffer, the decimal parser clears DERR each attempt.
; SPACE examines the whole reply: only NUL may terminate it (not ':'/ELSE).
; Program-syntax and variable-allocation errors retain their existing paths.
        ORG $A74E
INPUTREPLY LDX #BUF
        JSR $A000
        STX CUR
        TSTA
        BNE $A74B
        JSR SPACE
        TSTA
        BNE $A74B
INPUTREPLYEND EQU *
