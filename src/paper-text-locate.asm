; Text-grid positioning, separate from manual motor coordinates.
; PMVALID=3 owns LPCOLUMN and LLROW; other operations invalidate the grid.
; First text operation declares the current physical point as row 1/column 1.
; Rows 1..64, columns 1..72. Native pitch: 16 head / 56 paper units.
; The normal PMMOVE 128/448 limits remain unchanged for manual commands.
LLROW EQU $1972
LLTARGETROW EQU $1973
LLTARGETCOL EQU MCX
LLENTRY JSR LLARG
        CMPB #63
        BHI LLBAD
        STAB LLTARGETROW
        JSR SPACE
        CMPA #44
        BNE LLSYNTAX
        INX
        STX CUR
        JSR LLARG
        STAB LLTARGETCOL
        JSR EOS
        JSR MCFREE
        JSR LLINIT
        LDAA LLROW
        CMPA #63
        BHI LLBAD
        ; Capture the column before PMX reuses its storage as a word.
        LDAB LPCOLUMN
        LDAA #16
        MUL
        STD PMX
        LDAB LLROW
        LDAA #56
        MUL
        STD PMY
        LDAA #1
        STAA PMVALID
        JMP LLMOVE
LLBAD JMP RANGEERROR
LLSYNTAX JMP SYNTAX
; @island move
LLMOVE LDAB LLTARGETROW
        LDAA #56
        MUL
        STD PMTY
        LDAB LLTARGETCOL
        LDAA #16
        MUL
        STD PMTX
        ; Targets have already been validated in text-grid units. Enter the
        ; common validator AFTER only the manual-coordinate range checks.
        ; RAM reservation, serial exclusion, phase checks and cleanup remain.
        JSR LLPMCHECK
        BCS LLFAIL
        LDAA LLTARGETROW
        STAA LLROW
        LDAA LLTARGETCOL
        STAA LPCOLUMN
        LDAA #3
        STAA PMVALID
        RTS
LLFAIL CLR PMVALID
        JMP MCERROR
; @island argument
LLARG JSR MCUNSIGNED
        TSTA
        BNE LLARGBAD
        TSTB
        BEQ LLARGBAD
        DECB
        CMPB #71
        BHI LLARGBAD
        RTS
LLARGBAD JMP RANGEERROR
; @island init
LLINIT LDAA PMVALID
        CMPA #3
        BEQ LLINITRET
        CLR LLROW
        CLR LPCOLUMN
LLINITRET RTS
; @island newline
; Saturate rather than wrap after 256 printed lines. LLOCATE refuses an
; out-of-grid current row; ORIGIN explicitly starts a new reference then.
LLNEWLINE INC LLROW
        BNE LLROWEND
        DEC LLROW
LLROWEND CLR LPCOLUMN
        RTS
