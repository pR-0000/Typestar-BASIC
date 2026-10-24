; Inline ASCII keyword, tagged handler. Its high byte ends the keyword.
; Handler = $8000 | (CPU address-$4000); zero links to the next fragment.
; MATCH carry survives the LDAA/INX scan to the keyword's tagged end marker.
CMDENTRY JMP STCOMMAND
        JSR SPACE
        TSTA
        BEQ CMDRETURN
        LDX #CMDTABLE
CMDNEXT LDAA ,X
        BEQ CMDLINK
        PSHX
        JSR MATCH
        PULX
CMDSCAN LDAA ,X
        BMI CMDSCANNED
        INX
        BRA CMDSCAN
CMDSCANNED BCS CMDSKIP
        LDD ,X
        ANDA #$7F
        ADDD #$4000
        XGDX
        JMP ,X
CMDSKIP LDAB #2
        ABX
        BRA CMDNEXT
CMDLINK LDX 1,X
        BNE CMDNEXT
        JMP LET
CMDRETURN RTS
CMDEND EQU *
