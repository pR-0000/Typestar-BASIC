; BASIC composition front end. Test linker supplies placements and hooks.
; DRAW INSTANT / DEFERRED / PRINT / CANCEL. BOX/LINE append while open, otherwise
; submit a one-record job. All numeric arguments pass existing parsers first.
; Never cache a heap pointer across BASIC statements (RUN/NEW/edit reset it).
; SHRECORD aliases PLSTATE, used only after EXPR/EOS; rendering starts later.
SHRECORD EQU PLSTATE
SHAUTO EQU $1D7F
SHMAXX EQU $1D77
SHMAXY EQU $1D78
SHLEFT EQU $1D79
SDDISPATCH LDX #SDNAME
        JSR MATCH
        BCC SDSUBCOMMAND
        JMP LNDISPATCH
SDNAME FCC "DRAW"
        FCB 0
SDSUBCOMMAND JSR SPACE
        LDX #SDDEFERNAME
        JSR MATCH
        BCC SDDEFERRED
        LDX #SDINSTANTNAME
        JSR MATCH
        BCC SDINSTANT
        LDX #SDPRINTNAME
        JSR MATCH
        BCS SDTRYCANCEL
        JMP SDPRINT
SDTRYCANCEL LDX #SDCANCELNAME
        JSR MATCH
        BCC SDCANCEL
        JMP SYNTAX
SDDEFERNAME FCC "DEFERRED"
        FCB 0
SDINSTANTNAME FCC "INSTANT"
        FCB 0
SDPRINTNAME FCC "PRINT"
        FCB 0
SDCANCELNAME FCC "CANCEL"
        FCB 0
; The list's existing count doubles as the mode: 0..32 deferred, absent or
; 255 instant. No permanent mode byte; heap resets naturally select INSTANT.
; Repeating DEFERRED keeps a pending drawing. INSTANT never discards one.
SDDEFERRED LDAB #1
        BRA SDMODE
SDINSTANT CLRB
SDMODE PSHB
        JSR EOS
        JSR SCLIST
        PULB
        BCC SDEXISTS
        CMPA #1
        BNE SDERROR
        BRA SDAPPLY
SDEXISTS LDAA ,X
        CMPA #255
        BEQ SDAPPLY
        CMPA #32
        BHI SDERROR
        TSTB
        BNE SDRETURN
        TSTA
        BEQ SDCANCEL
        LDX #SDPENDING
        JMP ERROR
SDAPPLY TSTB
        BEQ SDRETURN
        JSR SCBEGIN
        BCS SDERROR
        RTS
SDCANCEL JSR EOS
        JSR SCCLOSE
        BCC SDRETURN
        CMPA #1
        BNE SDERROR
SDRETURN RTS
SDERROR LDX #SDMESSAGE
        JMP ERROR
SDMESSAGE FCC "?DRAW"
        FCB 0
SDPENDING FCC "?DRAW PENDING"
        FCB 0
SDPRINT JSR EOS
        JMP SDSUBMIT

; Hooks replace the parameter-commit tail, AFTER original range checks.
SHBOX CLRA
        BRA SHCOPY
SHLINE LDAA #1
SHCOPY STAA SHRECORD
        LDD PXSTATE
        STD SHRECORD+1
        LDD PXSTATE+2
        STD SHRECORD+3
        LDD PXSTATE+4
        STD SHRECORD+5
        CLR SHRECORD+7
        TST SHRECORD
        BEQ SHLOOKUP
        CLR SHRECORD+6
SHLOOKUP CLR SHAUTO
        JSR SCLIST
        BCC SHFOUND
        CMPA #1
        BNE SDERROR
        BRA SHAUTOBEGIN
SHFOUND LDAA ,X
        CMPA #32
        BLS SHADD
        CMPA #255
        BNE SDERROR
SHAUTOBEGIN JSR SCBEGIN
        BCS SDERROR
        INC SHAUTO
SHADD LDX #SHRECORD
        JSR SCAPPEND
        BCS SDERROR
        TST SHAUTO
        BNE SDSUBMIT
        RTS

; Compute common extents before calling any native motor routine. Stored
; records came from the validated BOX/LINE parsers; POKE must not corrupt them.
; Half the LINE brush extends beyond the endpoints, clipped to page limits.
SDSUBMIT JSR SCLIST
        BCS SHERROR
        STX SBLIST
        LDAA ,X
        BEQ SHEMPTY
        CMPA #32
        BHI SHERROR
        STAA SHLEFT
        CLR SHMAXX
        CLR SHMAXY
        INX
SHEXTENT CLRB
        TST ,X
        BEQ SHX
        LDAB 5,X
        LSRB
SHX LDAA 1,X
        CMPA 3,X
        BCC SHXMAX
        LDAA 3,X
SHXMAX ABA
        CMPA #247
        BLS SHXCLIP
        LDAA #247
SHXCLIP CMPA SHMAXX
        BLS SHY
        STAA SHMAXX
SHY LDAA 2,X
        CMPA 4,X
        BCC SHYMAX
        LDAA 4,X
SHYMAX ABA
        BCC SHYCLIP
        LDAA #255
SHYCLIP CMPA SHMAXY
        BLS SHADVANCE
        STAA SHMAXY
SHADVANCE LDAB #8
        ABX
        DEC SHLEFT
        BNE SHEXTENT
        LDAA SHMAXX
        CLRB
SHDIV INCB
        SUBA #31
        BCC SHDIV
        LDAA SHMAXY
        LSRA
        LSRA
        LSRA
        LSRA
        LSRA
        INCA
        JSR RBJOB
        ; Error 6 is a preflight refusal (busy/serial/RAM), before any motion.
        ; Keep the scene open so the user can correct the cause and retry.
        CMPA #6
        BNE SHCLOSE
        JMP RBPAPERERROR
        ; Closing happens AFTER the callback finished reading the count.
        ; Preserve the driver's result while allocator scratch is reused.
SHCLOSE PSHA
        JSR SCCLOSE
        PULA
        TSTA
        BEQ SHRETURN
        JMP RBPAPERERROR
SHEMPTY JMP SCCLOSE
SHERROR JMP SDERROR
SHRETURN RTS
SDEND EQU *
