; Private scratch uses the existing bounded named-object heap. A slot is
; allocated once per maximum active nesting depth, then reused, never appended
; per call. The 65-byte payload has room for the length, 63 bytes and VAL's NUL.
; Return X -> payload. Caller increments X before setting STDEST and balances
; STDEPTH on success; STCOMMAND resets depth after an error unwinds the stack.
STSCRATCH LDAA STDEPTH
        CMPA #8
        BHS STSCRATCHDEPTH
        INC STDEPTH
        ADDA #$80
        JSR STFIND
        BCC STSCRATCHRET
        CMPA #1
        BNE STSCRATCHBAD
        LDX #DIMJOB
        LDD #$0101
        STD ,X
        LDD #65 ; 63 bytes plus length and a spare terminator for VAL.
        STD 2,X
        LDD #1
        STD 4,X
        JSR ANRESERVE
        BCS STSCRATCHFULL
        LDAA STDEPTH
        DECA
        ADDA #$80
        JSR STFIND
        BCS STSCRATCHBAD
STSCRATCHRET RTS
STSCRATCHDEPTH LDAA #3
        JMP $A518
STSCRATCHBAD JMP PRAMERROR
STSCRATCHFULL JMP PMEMERROR
STINTARG JSR DEXPR
        LDAA DERR
        BNE STINTFAIL
        JSR $A400
        BCS STINTRANGE
        TST DW+8
        BMI STINTRANGE
        RTS
STINTRANGE JMP RANGEERROR
STINTFAIL JMP $A518
; Reset temporary nesting at every statement, including after an error or
; BREAK. Keep the original dispatcher's LPRINT reset and entry semantics.
STCOMMAND CLR STDEPTH
        CLR LPMODE
        JMP CMDENTRY+3
STSCRATCHEND EQU *
