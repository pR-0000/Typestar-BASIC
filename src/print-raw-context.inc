; Prototype only: prepare the native column consumer, NOT a full print job.
; No ORG: eventual placement belongs to the printer integration/linker.
; Preconditions: IRQs masked, no active mechanical operation, setup completed.
; X -> immutable 4-byte descriptor: $20,$00, pattern pointer (big endian).
; Pattern = 31 format-0 words + one zero word (64 bytes) in accessible RAM.
; No argument validation here: internal ABI, never call directly from BASIC.
; No motion/output start, wait, cancellation or completion acknowledgement.
; A/B/X clobbered; caller must preserve live CPU registers and native ownership.
PRINT_PREPARE_RAW_COLUMNS STX $5E
        CLR $B7 ; Normal width, no underline.
        LDAA #$42 ; Ordinary character code; avoid special $B0 output handling.
        STAA $BC
        CLR $BD ; No secondary/composed glyph.
        CLR $C0 ; No repeat/fill request: advance primary pointer each decode.
        CLR $C1
        CLR $71 ; No secondary width.
        CLR $72
        CLR $6A ; First decode/output phase.
        LDAA #$48
        STAA $41
        LDAA #2
        STAA $49
        LDD #$6EE9
        STD $4E
        LDD #$6F6D
        STD $4A
        LDD #64 ; Normal 32/2 character advance, four intervals per unit.
        STD $6F
        JMP $75AE ; Native descriptor decode and interval-counter preparation.
PRINT_PREPARE_RAW_COLUMNS_END EQU *
