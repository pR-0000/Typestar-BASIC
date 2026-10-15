; Hook after the existing optional INPUT prompt. Numeric INPUT is preserved.
STINPUT LDX CUR
        STX DPTR
        JSR DSPACE
        LDAB 1,X
        CMPB #36
        BEQ STINPUTSTR
        JSR VARADDR
        JMP STOLDINPUT+3
STINPUTSTR JSR STNAME
        LDX DPTR
        STX CUR
        JSR EOS
        LDAA #30
        SUBA ILEN
        STAA EDWIDTH
        JSR READINPUT
        ; Treat a reply as text, preserving spaces and quotes verbatim.
        LDX #BUF
        CLR STLEN
STINPUTLEN TST ,X
        BEQ STINPUTDONE
        INC STLEN
        INX
        BRA STINPUTLEN
STINPUTDONE JMP STSTORE
STINPUTEND EQU *
