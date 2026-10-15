; ELSE lives in the unchanged token stream as ASCII. Split at its boundary,
; just as at ':', so GOSUB/FOR continuations keep their ordinary addresses.
; A reached ELSE skips the rest of the physical line. False IF searches the
; matching ELSE, counting nested IFs and ignoring strings and REM tails.
LECOUNT EQU $196E
LESEEK EQU $196F
LENEST EQU $1970
LEQUOTE EQU $1971
LESTART STX SCPOS
        CLR LECOUNT
        RTS
LECOND INC LECOUNT
        JMP DCONDITION
LEEND LDX LERECORDEND
        STX RNEXT
        RTS
LEFALSE LDAA LECOUNT
        STAA LESEEK
        CLR LENEST
        CLR LEQUOTE
        LDX SCSTART
LEFLOOP CPX LERECORDEND
        BCC LEEND
        LDAA ,X
        CMPA #34
        BNE LEFQUOTE
        COM LEQUOTE
LEFQUOTE TST LEQUOTE
        BNE LEFNEXT
        CMPA #$82
        BEQ LEEND
        CMPA #$87
        BNE LEFELSE
        TST LESEEK
        BEQ LEFNEST
        DEC LESEEK
        BRA LEFNEXT
LEFNEST INC LENEST
        BRA LEFNEXT
LEFELSE TST LESEEK
        BNE LEFNEXT
        JSR LECHECK
        BNE LEFNEXT
        TST LENEST
        BEQ LEFOUND
        DEC LENEST
LEFNEXT INX
        BRA LEFLOOP
LEFOUND INX
        INX
        INX
        INX
        CPX LERECORDEND
        BCS LEEXEC
        JMP SYNTAX
LEEXEC JSR SCEXP
        JMP THENBODY
