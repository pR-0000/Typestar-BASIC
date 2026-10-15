; Experimental named arrays above the tokenized program; scalars grow down.
; Linked only in the CPU integration bench, NOT in the flashable firmware.
; Requires ARRAY_CREATE / ARRAY_ELEMENT and PEND, DHEAP, DFLOOR equates.
; X -> 32-byte job: original allocator job[29], ASCII name at29, scan word30.
; Named record: name + original 8-byte descriptor + payload (9-byte overhead).
; Caller resets DFLOOR=PEND+1 with the volatile scalar heap on RUN/NEW/edit.
; X preserved, A/B/flags volatile. No program byte or scalar is moved.
;
; FIND: C=0, job25 -> eight-byte descriptor (after name).
;       C=1, A=1 not found, A=4 inconsistent record span.
ARRAY_NAMED_FIND LDD PEND
        ADDD #1
        STD 30,X
ANSCAN LDD 30,X
        SUBD DFLOOR
        BEQ ANMISS
        BCC ANCORRUPT
        LDD 30,X
        ADDD #9
        BCS ANCORRUPT
        SUBD DFLOOR
        BHI ANCORRUPT
        PSHX
        LDX 30,X
        LDD 7,X ; Payload length: header must already fit before reading it.
        PULX
        ADDD #9
        BCS ANCORRUPT
        ADDD 30,X
        BCS ANCORRUPT
        STD 27,X
        SUBD DFLOOR
        BHI ANCORRUPT
        PSHX
        LDX 30,X
        LDAA ,X
        PULX
        CMPA 29,X
        BEQ ANFOUND
        LDD 27,X
        STD 30,X
        BRA ANSCAN
ANFOUND LDD 30,X
        ADDD #1
        STD 25,X
        CLRA
        CLC
        RTS
ANMISS LDAA #1
        SEC
        RTS
ANCORRUPT LDAA #4
        SEC
        RTS
;
; DIM job lengths (not BASIC inclusive bounds), element size currently5.
; C=0 publishes DFLOOR and descriptor only after successful initialization.
; C=1: A=1 invalid shape/full, 2 duplicate, 3 invalid name, 4 bad heap.
; Failed allocations leave arena and DFLOOR/DHEAP unchanged.
ARRAY_NAMED_CREATE
        LDAA 29,X
        CMPA #65
        BCS ANBADNAME
        CMPA #90
        BHI ANBADNAME
        JSR ARRAY_NAMED_FIND
        BCC ANDUPLICATE
        CMPA #1
        BEQ ANRESERVE
        SEC
        RTS
ANRESERVE
        LDD DFLOOR
        ADDD #1 ; Reserve name; original allocator writes descriptor/payload.
        BCS ANFULL
        STD 21,X
        LDD DHEAP
        STD 23,X
        JSR ARRAY_CREATE
        BCS ANFULL
        LDD 25,X
        SUBD #1
        STD 30,X
        LDAA 29,X
        PSHX
        LDX 30,X
        STAA ,X
        PULX
        LDD 21,X
        STD DFLOOR
        CLRA
        CLC
ANRETURN RTS
ANFULL LDAA #1
        SEC
        RTS
ANDUPLICATE LDAA #2
        SEC
        RTS
ANBADNAME LDAA #3
        SEC
        RTS
ARRAY_NAMED_END EQU *
