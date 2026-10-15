; LPRINT literal with automatic wrapping at the validated eight-tile width.
; Validate the complete statement before heating, then stream groups of eight.
; Source lives in the BASIC input/expanded-line buffer, outside native scratch.
; No full-string copy or permanent heap reservation is needed.
; No expression evaluation or heap mutation during decode/physical printing.
; Temporary LIST/SAVE/motor scratch is exclusive while a command is running.
LPTEXT EQU $1DA5
LPREAD EQU $1DAD
LPREMAIN EQU $1DAF
LPMODE EQU $1DBA
LPPTR EQU $1DBB
LPDEST EQU $1DBD
LPLEFT EQU $1DBF
LPCOUNT EQU $1DC0
LPINDEX EQU $1DC1
LPDISPATCH CLR LPMODE
        LDX #LPNAME
        JSR MATCH
        BCC LPPARSE
        JMP PTDISPATCH
LPNAME FCC "LPRINT"
        FCB 0
LPPARSE JSR SPACE
        CMPA #34
        BNE LPSYNTAX
        INX
        STX LPREAD
        CLR LPREMAIN
LPSCAN LDAA ,X
        CMPA #34
        BEQ LPQUOTED
        CMPA #32
        BLO LPSYNTAX
        CMPA #126
        BHI LPBAD
        LDAB LPREMAIN
        CMPB #63
        BCC LPBAD
        INC LPREMAIN
        INX
        BRA LPSCAN
LPQUOTED INX
        STX CUR
        JSR EOS
        ; Reject an open drawing, serial session or engaged printer first.
        JSR MCFREE
LPNEXTLINE TST LPREMAIN
        BEQ LPRETURN
        CLR LPCOUNT
        LDX LPREAD
LPCOPY LDAA ,X
        INX
        STX LPREAD
        LDX #LPTEXT
        LDAB LPCOUNT
        ABX
        STAA ,X
        INC LPCOUNT
        DEC LPREMAIN
        BEQ LPCOPIED
        LDX LPREAD
        LDAA LPCOUNT
        CMPA #8
        BNE LPCOPY
LPCOPIED EQU *
        LDAB LPCOUNT
        LDAA #1
        STAA LPMODE
        JSR RBJOB
        CLR LPMODE
        TSTA
        BNE LPERROR
        CLR GPRAN
        BRA LPNEXTLINE
LPRETURN RTS
LPERROR JMP RBPAPERERROR
LPBAD JMP RANGEERROR
LPSYNTAX JMP SYNTAX

; Preserve the old 64-byte graphics path when not rendering text.
LPSIZE LDAA #64
        TST LPMODE
        BEQ LPMUL
        LDAA #96
LPMUL MUL
        RTS
LPNEXT TST LPMODE
        BEQ LPADD64
        ADDD #96
        RTS
LPADD64 ADDD #64
        RTS
LPFORMAT LDAA LPMODE
        STAA GPDESC+1
        RTS

LPSELECT TST LPMODE
        BNE LPRENDER
        JMP LNSELECT
LPRENDER STX LPDEST
        STAB LPLEFT
        LDX #LPTEXT
        STX LPPTR
LPNEXTCHAR LDX LPPTR
        LDAA ,X
        INX
        STX LPPTR
        LDX LPDEST
        JSR HFDECODE
        BCS LPFAIL
        ; Native format 1 expects C,B,A, whereas extraction stores A,B,C.
        ; Keep all channels, including those absent from format-0 graphics.
        LDX LPDEST
        LDAB #31
LPSWAP LDAA ,X
        PSHA
        LDAA 2,X
        STAA ,X
        PULA
        STAA 2,X
        INX
        INX
        INX
        DECB
        BNE LPSWAP
        CLR ,X
        CLR 1,X
        CLR 2,X
        INX
        INX
        INX
        STX LPDEST
        DEC LPLEFT
        BNE LPNEXTCHAR
        CLC
        RTS
LPFAIL SEC
        RTS
LPEND EQU *
