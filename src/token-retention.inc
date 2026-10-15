; Token format structural validation + CRC-16/CCITT, AFTER native startup.
; Called through the existing RETCRC16 entry. Never trusts retained PEND.
; Return C=0, X=sentinel, D=CRC; C=1 malformed. No program RAM writes.
; Scratch excludes RETFLAG/RETFIRST/RETEXPECT and the CRC accumulator.
VREC EQU $1B80
VNEXT EQU $1B82
VLAST EQU $1B84
VLEN EQU $1B86
VCOUNT EQU $1B87
VCOPY EQU $1B88
        ORG STORELINE+3 ; Reuse the obsolete source-record writer, after its JMP.
        LDD #$FFFF
        STD DCHECK
        CLR VLAST
        CLR VLAST+1
        LDX #PROGRAM
VRECORD CPX #PROGRAMEND
        BHI VBAD
        LDAA ,X
        BNE VNOTEND
        JMP VEND
VNOTEND
        CMPA #4
        BCS VBAD
        CMPA #66
        BHI VBAD
        STX VREC
        TAB
        ABX
        CPX #PROGRAMEND
        BHI VBAD
        STX VNEXT
        LDX VREC
        LDD 1,X
        SUBD VLAST
        BLS VBAD ; Strictly increasing unsigned line numbers, excludes zero.
        LDD 1,X
        STD VLAST
        LDAB ,X
        SUBB #3
        STAB VLEN
        INX
        INX
        INX
        JSR $A803
        BCS VBAD
; Reject whitespace-only stored records (the editor represents these as delete).
        LDX #$1C00
VSPACE LDAA ,X
        BEQ VBAD
        CMPA #32
        BNE VNONEMPTY
        INX
        BRA VSPACE
VBAD SEC
        RTS
VNONEMPTY LDX #$1C00
        LDAB $1D49 ; Expanded source length from decoder.
        JSR $A806 ; In-place compression is safe: output never exceeds input.
        BCS VBAD
        LDAA $1D49
        CMPA VLEN
        BNE VBAD
; Re-encoding must reproduce every byte: rejects tokens inside quoted strings
; or REM tails, while permitting malformed BASIC to be edited after restart.
        LDX VREC
        LDAB #3
        ABX
        STX VCOPY
        LDX #$1C00
        LDAA VLEN
        STAA VCOUNT
VCOMPARE LDAA ,X
        PSHX
        LDX VCOPY
        CMPA ,X
        BNE VPOPBAD
        INX
        STX VCOPY
        PULX
        INX
        DEC VCOUNT
        BNE VCOMPARE
        LDX VREC
VCRC LDAA ,X
        JSR PC_BYTE ; Existing verified CRC byte routine; X preserved.
        INX
        CPX VNEXT
        BCS VCRC
        JMP VRECORD
VPOPBAD PULX
        SEC
        RTS
VEND JSR PC_BYTE ; Include the final zero-length sentinel in CRC.
        LDD DCHECK
        CLC
        RTS
