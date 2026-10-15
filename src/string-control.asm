; THEN A$=... is an inline assignment, like THEN A=... . Keep the existing
; keyword/numeric-target classifier for all other cases.
STTHEN CMPA #36
        BEQ STTHENASSIGN
        CMPA #40
        BEQ STTHENFUNCTION
        JMP THENNOTFUNC
STTHENFUNCTION JMP THENEQUAL+4
STTHENASSIGN JMP THENEXEC
; READ dispatch is re-entered after every comma, allowing mixed destinations.
STREAD LDX CUR
        STX DPTR
        JSR DSPACE
        CLR STDATA
        LDAB 1,X
        CMPB #36
        BEQ STREADSTR
        JSR SPACE
        JMP DAREAD+3
STREADSTR INC STDATA
        JSR STNAME
        LDX DPTR
        STX CUR
        JSR SPACE
        TSTA
        BEQ STREADFETCH
        CMPA #44
        BEQ STREADFETCH
        JMP SYNTAX
STREADFETCH STX DASAVE
        JSR DAGET
        JSR STSTORE
        JMP DACOMMITTED
STCONTROLEND EQU *
