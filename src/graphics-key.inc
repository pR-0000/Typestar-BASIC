; Private CPU prototype: CODE ($3B) + P ($0F), no BASIC token/command.
; Call from KBDREAD instead of KBDSCAN. The original scan chooses CODE's
; higher row first, hiding P; explicitly sample row FD, bit7 for the chord.
; No event while a program, INPUT, serial transfer or startup is active.
GRAPHICS_SCAN JSR KBDSCAN
        CMPA #$3B
        BNE GRAPHICS_SCAN_END
        TST RUNNING
        BNE GRAPHICS_SCAN_END
        TST BOOTFLAG
        BNE GRAPHICS_SCAN_END
        TST SACTIVE
        BNE GRAPHICS_SCAN_END
        TST $19FB ; Editor active; cleared before dispatching a command.
        BEQ GRAPHICS_SCAN_END
        LDAA #$FD
        STAA $31
        LDAA $30
        ORAA $30
        TAB
        LDAA #$FF
        STAA $31 ; Always release matrix rows, even on a failed chord.
        BITB #$80
        BNE GRAPHICS_CODE_ONLY
        LDAA #$80 ; Outside physical matrix 0..63; existing debounce accepts it.
        RTS
GRAPHICS_CODE_ONLY LDAA #$3B
GRAPHICS_SCAN_END RTS

; Replace KBDCHAR's four-byte CMPA/BCC pair. Event $16 is reserved for the
; future console-owned graphic session; never interpreted as BASIC text.
GRAPHICS_KEYCHAR CMPA #$80
        BNE GRAPHICS_KEY_NORMAL
        LDAA #$16
        JMP KBDRETURN
GRAPHICS_KEY_NORMAL CMPA #44
        BCC GRAPHICS_KEY_NONE
        JMP KBDCHAR+4
GRAPHICS_KEY_NONE JMP KBDNONE
GRAPHICS_KEY_END EQU *
