; RNEXT is a token-stream continuation: record header or byte after ':'.
; Existing two-byte GOSUB/FOR frames therefore resume within a line too.
; Cache the containing record for sequential execution; jumps may scan spans.
SCBASE EQU $1CD3
SCEND EQU $1CD5
SCPOS EQU $1CD7
SCSTART EQU $1CD9
SCQUOTE EQU $1CDB
        ORG $574C ; Retired LIST body; keep LISTWAIT at $57CC.
STSEGONE
SCEXP STX SCPOS
        LDX SCBASE
        BEQ SCRESET
        CPX SCPOS
        BHI SCRESET
        LDX SCPOS
        CPX SCEND
        BCS SCFOUND
        BEQ SCSEEK ; Next physical record: retain O(1) sequential traversal.
SCRESET LDX #PROGRAM
SCSEEK STX SCBASE
        CPX PEND
        BCC SCBAD
        LDAB ,X
        CMPB #4
        BCS SCBAD
        CMPB #66
        BHI SCBAD
        ABX
        CPX PEND
        BHI SCBAD
        STX SCEND
        CPX SCPOS
        BLS SCSEEK
SCFOUND LDX SCBASE
        LDD 1,X
        STD RLINE
        CPX SCPOS
        BNE SCBODY
        INX
        INX
        INX
        STX SCPOS
SCBODY LDX SCPOS
        STX SCSTART
        LDAA ,X
        CMPA #$82 ; Preserve the fast path for full REM statements.
        BNE SCNORMAL
        LDX SCEND
        STX RNEXT
        CLRB
        JMP SCDECODE
SCNORMAL
        CLR SCQUOTE
        CLRB
        JMP SCSCAN
SCBAD JMP PRAMERROR
SCDECODE LDX SCSTART
        JSR $A803
        BCS SCBAD
        LDX #$1C00
        STX CUR
        RTS
STSEGONEEND EQU *
        ORG $5840 ; Retired RUN; leave the GOTO entry at $5876 intact.
STSEGTWO
SCSCAN CPX SCEND
        BCC SCLAST
        LDAA ,X
        CMPA #34
        BNE SCNOTQUOTE
        COM SCQUOTE
SCNOTQUOTE TST SCQUOTE
        BNE SCCHAR
        CMPA #$82 ; REM consumes the remainder, including all colons.
        BEQ SCREM
        CMPA #58
        BEQ SCCOLON
SCCHAR INX
        INCB
        BRA SCSCAN
SCREM INX
        INCB
        CPX SCEND
        BCS SCREM
SCLAST STX RNEXT
        JMP SCDECODE
SCCOLON INX
        STX RNEXT
        JMP SCDECODE
STSEGTWOEND EQU *
