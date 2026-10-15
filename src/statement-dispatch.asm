; Shared statement lookup. Four-byte entries: keyword pointer, handler.
; Zero keyword links to the next fragment (or zero for implicit LET).
; MATCH preserves CUR on failure. Keep the table iterator on the CPU stack,
; outside parser/native scratch; PULX preserves MATCH's carry result.
CMDENTRY CLR LPMODE
        JSR SPACE
        TSTA
        BEQ CMDRETURN
        LDX #CMDTABLE
CMDNEXT LDD ,X
        BEQ CMDLINK
        PSHX
        XGDX
        JSR MATCH
        PULX
        BCC CMDFOUND
        LDAB #4
        ABX
        BRA CMDNEXT
CMDFOUND LDX 2,X
        JMP ,X
CMDLINK LDX 2,X
        CPX #0
        BNE CMDNEXT
        JMP LET
CMDRETURN RTS
CMDEND EQU *
