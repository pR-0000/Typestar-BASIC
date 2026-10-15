; Typestar BASIC: checked row-major array address calculation, HD6301.
; Standalone module, NOT integrated in the current BASIC firmware.
; X points to a caller-owned 21-byte job, disjoint from CPU stack and data:
; +0 rank (1 or 2), +1 element size (1,2,4,5 bytes)
; Five bytes store the current BASIC packed decimal coefficient/sign/scale.
; +2 count0 word, +4 count1 word (must be 1 for rank1)
; +6 data address word, +8 index0 word, +10 index1 word (0 for rank1)
; +12 result address word; unchanged on any error
; +14 accumulator word, +16 multiplier word, +18 span word, +20 bit counter
; Counts are lengths, not BASIC DIM upper bounds. All words are big-endian.
; Data layout: address = base + ((index0 * count1) + index1) * element_size.
; C=0 success, C=1 invalid metadata/index or address arithmetic overflow.
; Preserves X, SP and IRQ mask; A/B/other flags and +14..20 are scratch.
; Does NOT allocate memory, access array elements or prove arena ownership.
; Caller must check the computed span is in its arena and exclude ROM/I/O.
        OPT H01
        ORG $6000

ARRAY_ELEMENT
        LDAA 0,X
        CMPA #1
        BEQ ARANK1
        CMPA #2
        BNE AERROR
        BRA ASHAPE
ARANK1  LDD 4,X
        SUBD #1
        BNE AERROR
        LDD 10,X
        BNE AERROR
ASHAPE  LDAA 1,X
        CMPA #1
        BEQ ACOUNTS
        CMPA #2
        BEQ ACOUNTS
        CMPA #4
        BEQ ACOUNTS
        CMPA #5
        BNE AERROR
ACOUNTS LDD 2,X
        BEQ AERROR
        LDD 4,X
        BEQ AERROR
        LDD 8,X
        SUBD 2,X
        BCC AERROR
        LDD 10,X
        SUBD 4,X
        BCC AERROR
; Validate the ENTIRE data span before producing any element address.
        LDD 2,X
        STD 16,X
        BSR AMULTIPLY
        BCS AERROR
        BSR ASCALE
        BCS AERROR
        STD 18,X
        SUBD #1
        ADDD 6,X
        BCS AERROR
; Span is valid: calculate the requested element's row-major offset.
        LDD 8,X
        STD 16,X
        BSR AMULTIPLY
        BCS AERROR
        ADDD 10,X
        BCS AERROR
        BSR ASCALE
        BCS AERROR
        ADDD 6,X
        BCS AERROR
        STD 12,X
        CLC
        RTS
AERROR  SEC
        RTS

; Unsigned 16-bit multiplication: scratch16 * count1. Shift-add, 16 rounds.
; Detect overflow even when the requested index happens to be small.
AMULTIPLY
        CLRA
        CLRB
        STD 14,X
        LDAA #16
        STAA 20,X
AMLOOP  LDD 14,X
        ASLD
        BCS AERROR
        STD 14,X
        LDD 16,X
        ASLD
        STD 16,X
        BCC AMNEXT
        LDD 14,X
        ADDD 4,X
        BCS AERROR
        STD 14,X
AMNEXT  DEC 20,X
        BNE AMLOOP
        LDD 14,X
        CLC
        RTS

; Multiply D by element size. PULB preserves CMP flags on HD6301.
ASCALE  STD 14,X ; Preserve unscaled value for the five-byte BCD case.
        PSHB
        LDAB 1,X
        CMPB #1
        PULB
        BEQ ASDONE
        ASLD
        BCS AERROR
        PSHB
        LDAB 1,X
        CMPB #2
        PULB
        BEQ ASDONE
        ASLD
        BCS AERROR
        PSHB
        LDAB 1,X
        CMPB #5
        PULB
        BNE ASDONE
        ADDD 14,X ; 5*n = 4*n + n, with independent overflow checks.
        BCS AERROR
ASDONE  CLC
        RTS
ARRAY_END EQU *
