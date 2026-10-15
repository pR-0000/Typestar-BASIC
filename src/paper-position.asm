; Offline synchronous positioning prototype. NOT linked into a release.
; D=absolute head target, X=absolute paper target, in native motor units.
; Bounds for this test: head 0..128, paper 0..448, no reverse paper.
; No millimetre or graphical-dot equivalence is claimed by this low-level ABI.
; PMORIGIN is a software declaration only; caller must establish the physical
; origin. PMMOVE must run with IRQ masked and exclusive foreground ownership.
; PMSTATE: 17 bytes, assigned only by the test linker for now.
PMVALID EQU PMSTATE
PMX EQU PMSTATE+1
PMY EQU PMSTATE+3
PMTX EQU PMSTATE+5
PMTY EQU PMSTATE+7
PMSP EQU PMSTATE+9
PMBACKUP EQU PMSTATE+11
PMPTR EQU PMSTATE+13
PMRESULT EQU PMSTATE+15
PMSAVED08 EQU PMSTATE+16
PMORIGIN CLR PMX
        CLR PMX+1
        CLR PMY
        CLR PMY+1
        LDAA #1
        STAA PMVALID
        RTS
PMMOVE STD PMTX
        STX PMTY
        SUBD #128
        BHI PMREJECT
        CPX #448
        BHI PMREJECT
        CPX PMY
        BCS PMREJECT
        LDAA PMVALID
        CMPA #1
        BNE PMREJECT
        TST SACTIVE
        BNE PMREJECT
        TST GPRAN
        BNE PMREJECT
        ; Same native phase-ring preconditions as the released raw printer.
        LDX $4E
        CPX #$6EE9
        BCS PMREJECT
        CPX #$6EF1
        BCC PMREJECT
        LDX $50
        CPX #$6EF1
        BCS PMREJECT
        CPX #$6EF9
        BCC PMREJECT
        LDX PEND
        INX
        CPX DFLOOR
        BHI PMREJECT
        LDD DFLOOR
        SUBD #$20C1
        BCS PMREJECT
        LDX DHEAP
        CPX #$3800
        BHI PMREJECT
        LDD DFLOOR
        ADDD #220
        BCS PMREJECT
        SUBD DHEAP
        BHI PMREJECT
        BRA PMSTART
PMREJECT LDAA #6
        SEC
        RTS
PMSTART STS PMSP
        LDX DFLOOR
        STX PMBACKUP
        STX PMPTR
        LDX #$1DCB
        LDAB #220
PMSAVE LDAA ,X
        PSHX
        LDX PMPTR
        STAA ,X
        INX
        STX PMPTR
        PULX
        INX
        DECB
        BNE PMSAVE
        CLR PMRESULT
        LDAA $08
        ANDA #$1F
        STAA PMSAVED08
        STAA GPSAVED08
        ; Pending state must never be treated as a known coordinate.
        LDAA #2
        STAA PMVALID
        LDD PMTX
        SUBD PMX
        BEQ PMFEED
        STD $BA
        JSR GPENABLE
        LDX #$716F
        JSR GPCALL
PMFEED LDD PMTY
        SUBD PMY
        BEQ PMCOMMIT
        STD $B8
        JSR GPENABLE
        CLRA
        CLRB
        STD $AB
        STAA $013E
        LDX #$7154
        JSR GPCALL
PMCOMMIT LDD PMTX
        STD PMX
        LDD PMTY
        STD PMY
        LDAA #1
        STAA PMVALID
        BRA PMCLEAN
; Test linker directs GPABORT's terminal JMP here. Unwind native RTI frames.
PMABORT LDAA GPERROR
        STAA PMRESULT
        CLR PMVALID
        LDS PMSP
PMCLEAN LDAA PMSAVED08
        STAA GPSAVED08
        JSR GPOFF
        LDX PMBACKUP
        STX PMPTR
        LDX #$1DCB
        LDAB #220
PMRESTORE PSHX
        LDX PMPTR
        LDAA ,X
        INX
        STX PMPTR
        PULX
        STAA ,X
        INX
        DECB
        BNE PMRESTORE
        LDAA PMRESULT
        BNE PMFAIL
        CLC
        RTS
PMFAIL SEC
        RTS
PMEND EQU *
