; Eight software call frames: caller line + FOR depth at entry.
; Shares LIST scratch while RUN; no CPU-stack frames survive a statement.
GCOUNT EQU $197F
GFRAMES EQU $1B30
KGOSUB FCC "GOSUB"
        FCB 0
KRETURN FCC "RETURN"
        FCB 0
GDISPATCH LDX #KGOSUB
        JSR MATCH
        BCS GTRYRETURN
        JMP GCALL
GTRYRETURN LDX #KRETURN
        JSR MATCH
        BCC GRETURN
        JMP $4412
GRUNONLY TST RUNNING
        BNE GRUNOK
        JMP MODEERROR
GRUNOK RTS
GCALL JSR GRUNONLY
        JSR EXPR
        STD VALUE
        JSR EOS
        LDD VALUE
        JSR CHECKLINE
        LDAA GCOUNT
        CMPA #8
        BCS GPUSH
        LDX #GDEPTHMSG
        JMP ERROR
GPUSH ASLA
        TAB
        LDX #GFRAMES
        ABX
        LDAA LINE
        STAA ,X
        LDAA $1974
        STAA 1,X
        INC GCOUNT
        LDAB VALUE+1
        JMP GOTOINRUN ; Validates target exists, then RUN advances to it.
GRETURN JSR GRUNONLY
        JSR EOS
        LDAB GCOUNT
        BEQ GPAIRERROR
        DECB
        ASLB
        LDX #GFRAMES
        ABX
        LDAA $1974
        CMPA 1,X
        BNE GLOOPERROR ; Require locally opened loops to finish before RETURN.
        LDAA ,X
        STAA LINE ; RUN resumes at the next existing line after the call.
        DEC GCOUNT
        RTS
GFINISH TST GCOUNT
        BNE GPAIRERROR
        TST $1974
        BNE GLOOPERROR
        RTS
; NEXT may not consume a loop belonging to the caller. Preserve the depth
; in A for the original NEXT frame-index calculation on return.
GNEXTCHECK LDAB GCOUNT
        BEQ GNEXTOK
        DECB
        ASLB
        LDX #GFRAMES
        ABX
        LDAA $1974
        CMPA 1,X
        BLS GLOOPERROR
GNEXTOK LDAA $1974
        RTS
GPAIRERROR LDX #GPAIRMSG
        JMP ERROR
GLOOPERROR LDX #GLOOPMSG
        JMP ERROR
GDEPTHMSG FCC "?GOSUB DEPTH"
        FCB 13,10,0
GPAIRMSG FCC "?GOSUB/RETURN"
        FCB 13,10,0
GLOOPMSG FCC "?FOR/NEXT"
        FCB 13,10,0
