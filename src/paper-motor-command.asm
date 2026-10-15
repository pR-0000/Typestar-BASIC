; Public fine motion in native units (two phase steps per unit).
; MOVE x,y absolute relative to ORIGIN; HEAD dx signed; FEED dy forward.
; ORIGIN declares current position zero, never seeks an endstop.
; Bounds: X=0..128, Y=0..448. Paper reverse deliberately rejected.
MCX EQU $1DB6
MCY EQU $1DB8
MCDISPATCH LDX #MCORIGINNAME
        JSR MATCH
        BCC MCORIGIN
        LDX #MCMOVENAME
        JSR MATCH
        BCC MCMOVE
        LDX #MCHEADNAME
        JSR MATCH
        BCC MCHEAD
        LDX #MCFEEDNAME
        JSR MATCH
        BCC MCFEED
        JMP SDDISPATCH
MCORIGINNAME FCC "ORIGIN"
        FCB 0
MCMOVENAME FCC "MOVE"
        FCB 0
MCHEADNAME FCC "HEAD"
        FCB 0
MCFEEDNAME FCC "FEED"
        FCB 0
MCORIGIN JSR EOS
        JSR MCFREE
        JMP PMORIGIN
MCMOVE JSR MCUNSIGNED
        STD MCX
        JSR SPACE
        CMPA #44
        BNE MCSYNTAX
        INX
        STX CUR
        JSR MCUNSIGNED
        STD MCY
        JSR EOS
        BRA MCRUN
MCHEAD JSR EXPR
        STD MCX
        TST DW+8
        BMI MCNEGATIVE
        SUBD #128
        BHI MCRANGE
        BRA MCHEADEND
MCNEGATIVE SUBD #$FF80
        BCS MCRANGE
MCHEADEND JSR EOS
        JSR MCREADY
        LDD MCX
        ADDD PMX
        STD MCX
        LDD PMY
        STD MCY
        BRA MCCALL
MCFEED JSR MCUNSIGNED
        SUBD #448
        BHI MCRANGE
        ADDD #448
        STD MCY
        JSR EOS
        JSR MCREADY
        LDD MCY
        ADDD PMY
        STD MCY
        LDD PMX
        STD MCX
        BRA MCCALL
MCUNSIGNED JSR EXPR
        TST DW+8
        BMI MCRANGE
        RTS
MCSYNTAX JMP SYNTAX
MCRANGE JMP RANGEERROR
MCRUN JSR MCREADY
MCCALL LDD MCX
        LDX MCY
        JSR PMMOVE
        BCS MCERROR
        RTS
MCREADY JSR MCFREE
        LDAA PMVALID
        CMPA #1
        BNE MCERROR
        RTS
; Movement cannot shift the reference of a drawing waiting in the heap.
; Even an empty deferred scene must be closed explicitly with INSTANT/CANCEL.
MCFREE TST SACTIVE
        BNE MCERROR
        LDAA GPRAN
        CMPA #2
        BEQ MCERROR
        JSR SCLIST
        BCC MCHASLIST
        CMPA #1
        BNE MCERROR
        RTS
MCHASLIST LDAA ,X
        CMPA #255
        BNE MCPENDING
        RTS
MCPENDING LDX #SDPENDING
        JMP ERROR
MCERROR LDX #MCMESSAGE
        JMP ERROR
MCMESSAGE FCC "?MOTOR"
        FCB 0
MCEND EQU *

; Boot always invalidates the physical origin, independently of retained RAM.
MOTORBOOT CLR PMVALID
        CLR GPRAN
        CLR SACTIVE
        RTS
; Existing raw printer calls stay at their ABI address. Heating invalidates
; manual coordinates: graphics presently place their own origin at the current
; sheet position. Re-declare ORIGIN before the next manual motion sequence.
MOTORPRINT CLR PMVALID
        LDX $4E
        CPX #$6EE9
        JMP GPPRINT+5
; Only the motor transaction uses PMVALID=2. Every error unwinds its own stack.
MOTORABORT LDAA PMVALID
        CMPA #2
        BEQ MOTORFAIL
        JMP RBERROUTE
MOTORFAIL JMP PMABORT
MOTOREND EQU *
