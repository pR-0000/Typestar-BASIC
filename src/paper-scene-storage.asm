; Offline scene list in the actual named-array arena. No public BASIC parser.
; Private name 0 is skipped by the existing A..Z array lookup. Its descriptor
; is a rank-1 byte array of 257 bytes: count + 32 fixed 8-byte shape records.
; Total allocation 266 bytes. BEGIN reuses the record; RUN/NEW/edit discard it
; with other volatile arrays. No persistent pointer survives a heap reset.
; SCJOB=32-byte allocator job, SCSTATE=2-byte source pointer, test placements.
; SCBEGIN: create/reuse and clear count. SCLIST: X->count, C clear if present.
; SCADD: X->eight validated-format bytes, validate/copy and publish count last.
; SCCLOSE: mark inactive (count=255), retain allocation for the next BEGIN.
; C set on failure. A=1 missing/closed/full/bad record, A=4 corrupt heap/header.
; X/A/B volatile. No arena write on rejection; temporary job may change.
SCSOURCE EQU SCSTATE
SCBEGIN JSR SCLIST
        BCC SCRESET
        CMPA #1
        BEQ SCALLOC
        SEC
        RTS
SCALLOC EQU *
        LDX #SCJOB
        LDD #$0101
        STD 0,X
        STD 2,X
        LDD #1
        STD 4,X
        ; ANRESERVE reuses the allocator but bypasses the public A..Z check.
        ; SCLIST has already searched for private name 0 and validated spans.
        JSR ANRESERVE
        BCS SCRETURN
        JSR SCLIST
        BCS SCRETURN
SCRESET CLR ,X
        CLC
SCRETURN RTS
SCLIST LDX #SCJOB
        CLR 29,X
        JSR ARRAY_NAMED_FIND
        BCS SCRETURN
        LDX SCJOB+25
        LDD 0,X
        SUBD #$0101
        BNE SCCORRUPT
        LDD 2,X
        SUBD #257
        BNE SCCORRUPT
        LDD 4,X
        SUBD #1
        BNE SCCORRUPT
        LDD 6,X
        SUBD #257
        BNE SCCORRUPT
        LDAB #8
        ABX
        CLC
        RTS
SCCORRUPT LDAA #4
        SEC
        RTS
SCBAD LDAA #1
        SEC
        RTS
SCADD STX SCSOURCE
        LDAA 0,X
        CMPA #1
        BHI SCBAD
        LDAA 1,X
        CMPA #247
        BHI SCBAD
        LDAA 3,X
        CMPA #247
        BHI SCBAD
        LDAA 5,X
        BEQ SCBAD
        CMPA #16
        BHI SCBAD
        TST 7,X
        BNE SCBAD
        TST 0,X
        BNE SCLINECHECK
        LDAA 1,X
        CMPA 3,X
        BHI SCBAD
        LDAA 2,X
        CMPA 4,X
        BHI SCBAD
        LDAA 6,X
        CMPA #1
        BHI SCBAD
        BRA SCFIND
SCLINECHECK TST 6,X
        BNE SCBAD
SCFIND JSR SCLIST
        BCS SCRETURN
        LDAB ,X
        CMPB #32
        BCC SCBAD
        ; Preserve count pointer until all eight bytes have been written.
        PSHX
        ASLB
        ASLB
        ASLB
        INX
        ABX
        STX SCJOB+30
        LDX SCSOURCE
        LDAB #8
SCCOPY LDAA ,X
        PSHX
        LDX SCJOB+30
        STAA ,X
        INX
        STX SCJOB+30
        PULX
        INX
        DECB
        BNE SCCOPY
        PULX
        INC ,X
        CLC
        RTS
SCCLOSE JSR SCLIST
        BCS SCCLOSERET
        LDAA #255
        STAA ,X
        CLC
SCCLOSERET RTS
SCEND EQU *
