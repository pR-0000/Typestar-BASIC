; Explicit reproducible seed; no timer dependency or implicit user input.
; Validate the entire statement before modifying the existing RND state.
        ORG $8F13
RZDISPATCH LDX #RZNAME
        JSR MATCH
        BCC RZCOMMAND
        JMP LCDNEW
RZCOMMAND JSR EXPR
        TST DW+8
        BMI RZBAD
        SUBD #0
        BEQ RZBAD
        PSHB
        PSHA
        JSR EOS
        PULA
        PULB
        STD $1EC6
        RTS
RZBAD JMP RANGEERROR
RZNAME FCC "RANDOMIZE"
        FCB 0
RZEND EQU *
