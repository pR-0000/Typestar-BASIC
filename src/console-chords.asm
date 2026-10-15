; CODE chords are editor-only; physical Shift/Caps never select deletion.
CXSCAN JSR KBDSCAN
        CMPA #$3B
        BNE CXRET
        TST RUNNING
        BNE CXRET
        TST BOOTFLAG
        BNE CXRET
        TST SACTIVE
        BNE CXRET
        TST $19FB
        BEQ CXRET
        LDX #CXTABLE
CXLOOP LDAA ,X
        STAA $31
        LDAA $30
        ORAA $30
        ANDA 1,X
        BEQ CXFOUND
        INX
        INX
        INX
        CPX #CXTABLEEND
        BNE CXLOOP
        LDAA #$3B
        BRA CXRELEASE
CXFOUND LDAA 2,X
CXRELEASE PSHA
        LDAA #$FF
        STAA $31
        PULA
CXRET RTS
; @island table
; row, active-low bit, synthetic debounced key. CODE+P keeps its old ID.
CXTABLE FCB $FD,$80,$80,$DF,$80,$91,$BF,$02,$BC,$BF,$04,$BE
CXTABLEEND EQU *
; @island translate
CXCHAR CMPA #$80
        BNE CXOTHER
        LDAA #$96
CXOTHER CMPA #$FF
        BEQ CXNONE
        TSTA
        BPL CXNORMAL
        ANDA #$7F
        JMP KBDRETURN
CXNORMAL CMPA #44
        BCC CXNONE
        JMP KBDCHAR+4
CXNONE JMP KBDNONE
; @island delete
CXDELETE CMPA #$11
        BNE CXBACKSPACE
        LDAA EDLEN
        SUBA EDPOS
        STAA EDLEN
        LDAB EDPOS
        CLR EDPOS
        LDX #BUF
CXCOPY PSHX
        ABX
        LDAA ,X
        PULX
        STAA ,X
        INX
        TSTA
        BNE CXCOPY
        JMP EDRESTORE
CXBACKSPACE CMPA #8
        BNE CXPRINT
        JMP EDNOTRIGHT+4
CXPRINT JMP EDPRINTABLE
