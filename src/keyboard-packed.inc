; Lossless shared 22-byte blocks, eight pointers per keyboard locale.
; Entry replaces KBDCHAR+4, after the existing special-key/graphics filter.
; KRAW=0..43, KLOCALE=0..9; $32 bit 7=Shift, KMODE nonzero=II.
; No extra RAM. Existing KBDRETURN restores the caller's saved X and B.
KPACK LDAA KLOCALE
        CMPA #10
        BCS KPVALID
        JMP KBDNONE
KPVALID LDAB KRAW
        CMPB #22
        BCS KPLOW
        SUBB #22
        PSHB
        ASLA
        ASLA
        ASLA
        INCA
        BRA KPMODE
KPLOW PSHB
        ASLA
        ASLA
        ASLA
KPMODE TST KMODE
        BEQ KPSHIFT
        ADDA #4
KPSHIFT LDAB $32
        BPL KPINDEX
        ADDA #2
KPINDEX TAB
        ASLB
        LDX #KPTABLE
        ABX
        LDX ,X
        PULB
        ABX
        LDAA ,X
        JMP KBDRETURN
KPACKEND EQU *
