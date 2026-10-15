; OFFLINE ABI PROTOTYPE, not part of any flashable release.
; B=1..8 tiles already rendered at DFLOOR, each 64 bytes with zero guards.
; The caller may borrow free heap only while BASIC execution is suspended.
; Preserve $1DCB..$1EA6 (220 bytes) after the band, without changing heap bounds.
; No NEW, UART, LCD or editor return. A=0/C=0 success, A=error/C=1 failure.
; One transaction per boot, 1..16 bands, shared GPRAN policy with CODE+P.
; RBAND prints one pre-rendered band. RBJOB: A=band count, B=tile count.
; RBRENDER callback: A=zero-based band, B=tiles, X=DFLOOR. C=1 aborts.
; Callback may fill only the band buffer, not backup or persistent BASIC data.
; Preconditions: global IRQ masked, foreground BASIC evaluation suspended.
; RBSTATE (10 bytes) is test-only scratch outside native printer workspace.
RBSP EQU RBSTATE
RBBACKUP EQU RBSTATE+2
RBSOURCE EQU RBSTATE+4
RBRESULT EQU RBSTATE+6
RBTILES EQU RBSTATE+7
RBBANDS EQU RBSTATE+8
RBBANDINDEX EQU RBSTATE+9
RBAND LDAA #1
RBJOB TSTA
        BEQ RBREJECT
        CMPA #16
        BHI RBREJECT
        STAA RBBANDS
        TSTB
        BEQ RBREJECT
        CMPB #8
        BHI RBREJECT
        TST SACTIVE
        BNE RBREJECT
        TST GPRAN
        BNE RBREJECT
        STAB RBTILES
        LDX PEND
        INX
        CPX DFLOOR
        BHI RBREJECT
        LDX DFLOOR
        CPX #$20C1
        BCS RBREJECT
        LDX DHEAP
        CPX #$3800
        BHI RBREJECT
        LDAA #64
        MUL
        ADDD DFLOOR
        BCS RBREJECT
        STD RBBACKUP
        ADDD #220
        BCS RBREJECT
        SUBD DHEAP
        BHI RBREJECT
        BRA RBSAVE
RBREJECT LDAA #6
        SEC
        RTS
RBSAVE STS RBSP
        LDX RBBACKUP
        STX RBSOURCE
        LDX #$1DCB
        LDAB #220
RBSAVELOOP LDAA ,X
        PSHX
        LDX RBSOURCE
        STAA ,X
        INX
        STX RBSOURCE
        PULX
        INX
        DECB
        BNE RBSAVELOOP
        INC GPRAN
        CLR RBBANDINDEX
        CLR RBRESULT
        CLR GPERROR
        CLR PRINT_GLYPH_BUSY
        LDAA $08
        ANDA #$1F
        STAA GPSAVED08
        LDAA RBTILES
        STAA GXNX
RBNEXT LDAA RBBANDINDEX
        LDAB RBTILES
        LDX DFLOOR
        JSR RBRENDER
        BCC RBRENDERED
        LDAA #7
        STAA RBRESULT
        JMP RBCLEAN
RBRENDERED CLR GXPRINTCOL
        LDAA #$20
        STAA GPDESC
        CLR GPDESC+1
        LDX DFLOOR
        STX GXPATPTR
RBPRINT JSR GPPRINT
        INC GXPRINTCOL
        LDAA GXPRINTCOL
        CMPA GXNX
        BEQ RBROW
        LDD GXPATPTR
        ADDD #64
        STD GXPATPTR
        BRA RBPRINT
RBROW JSR GPROW
        INC RBBANDINDEX
        LDAA RBBANDINDEX
        CMPA RBBANDS
        BNE RBNEXT
        BRA RBCLEAN
; Test linker redirects GPABORT's terminal JMP here. Unwind RTI/helper frames.
RBABORT LDAA GPERROR
        STAA RBRESULT
        LDS RBSP
RBCLEAN JSR GPOFF
        LDX RBBACKUP
        STX RBSOURCE
        LDX #$1DCB
        LDAB #220
RBRESTORE PSHX
        LDX RBSOURCE
        LDAA ,X
        INX
        STX RBSOURCE
        PULX
        STAA ,X
        INX
        DECB
        BNE RBRESTORE
        LDAA RBRESULT
        BEQ RBOK
        SEC
        RTS
RBOK CLC
        RTS
RBEND EQU *
