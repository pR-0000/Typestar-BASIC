; Typestar BASIC: allocate a zeroed array from a caller-owned linear arena.
; Standalone prototype. Includes the checked array-address module unchanged.
; X = 29-byte private job, disjoint from arena and stack:
; +0 rank, +1 element bytes, +2 count0 word, +4 count1 word
; +6..20 scratch for ARRAY_ELEMENT (indices set to zero here)
; +21 next-free address word (updated only on success)
; +23 arena exclusive-end word (preserved)
; +25 returned descriptor address word (preserved on failure)
; +27 candidate next-free address word (scratch)
;
; Descriptor at returned address: rank byte, element-size byte, count0 word,
; count1 word, payload-byte-count word; zeroed payload immediately follows.
; Header = 8 bytes. Signedness belongs to the future variable/type descriptor.
;
; C=0 success, C=1 invalid shape/span or insufficient space. On error the
; arena, cursor and returned descriptor are unchanged (scratch may change).
; Preserves X/SP/IRQ mask; clobbers A/B and other flags.
; The caller guarantees arena ownership, excludes hardware/ROM/stack/jobs,
; and serializes allocation. This is not interrupt-atomic or a general heap.
        INCLUDE "src/array-index.asm"

ARRAY_CREATE
        LDD 21,X
        SUBD 23,X
        BCC ACFAIL           ; empty or reversed arena cannot fit any object
        LDD 21,X
        ADDD #8
        BCS ACFAIL
        STD 6,X             ; prospective payload base, not published yet
        CLRA
        CLRB
        STD 8,X
        STD 10,X
        JSR ARRAY_ELEMENT   ; rank, shape, size and complete span validated
        BCS ACFAIL
        LDD 6,X
        ADDD 18,X
        BCS ACFAIL           ; exclusive end must itself fit in 16 bits
        STD 27,X
        SUBD 23,X
        BCS ACCOMMIT
        BEQ ACCOMMIT        ; exact fit is permitted
ACFAIL  SEC
        RTS

; All possible failures precede the first arena write. Copy descriptor words
; while retaining the private job pointer on the stack; no global RAM used.
ACCOMMIT
        LDD 0,X
        PSHX
        LDX 21,X
        STD 0,X
        PULX
        LDD 2,X
        PSHX
        LDX 21,X
        STD 2,X
        PULX
        LDD 4,X
        PSHX
        LDX 21,X
        STD 4,X
        PULX
        LDD 18,X
        PSHX
        LDX 21,X
        STD 6,X
        PULX

        LDD 18,X            ; nonzero byte count, independent of element type
        PSHX
        LDX 6,X
ACZERO  CLR 0,X
        INX
        SUBD #1
        BNE ACZERO
        PULX
; Publish only after the complete header and zeroed payload exist.
        LDD 21,X
        STD 25,X
        LDD 27,X
        STD 21,X
        CLC
        RTS
ARRAY_CREATE_END EQU *
