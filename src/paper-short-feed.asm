; Experimental short positive paper travel, called instead of $74B9 at $7158.
; Mirrors the short-carriage counter strategy at $74BE, for paper only.
; Applies only to 1..8 with 013E=0. Other paths retain original preparation.
; No extra stack frame, new coil values or timer table. Counts are changed.
        OPT H01
        ORG $6230
PAPER_SHORT_PREPARE TST $013E
        BNE PAPER_ORIGINAL
        LDD $B8
        BEQ PAPER_ORIGINAL
        BMI PAPER_ORIGINAL
        SUBD #8
        BGT PAPER_ORIGINAL
        LDD $B8
        SUBD #1
        ASLD
        ASLD
        ADDD #1
        STD $52          ; Initial counter = 4(N-1)+1, instead of 33.
        LDD #9
        STD $B8          ; Subsequent (B8-8)*4-1 yields 3, never underflows.
        LDAA #1
        STAA $49         ; Same initial divider as original $74B9.
        RTS
PAPER_ORIGINAL JMP $74B9
PAPER_SHORT_END EQU *
