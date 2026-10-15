; Foreground repair after PRINT_CALL_STAGE returns, before the next timer stage.
; Experimental single-raw-glyph owner ONLY. I must remain set: no IRQ can use
; 0045 between the native yield and this repair. Do not call for arbitrary jobs.
; 728B can enter 70CF, which replaces our completion pointer with 70D6.
; Keep Canon's entire paper movement intact, but return to raw-glyph startup
; rather than the Canon editor/request dispatcher once that movement finishes.
; No native ROM patch, no test of an uninitialized mode flag during boot.
; X preserved, condition flags clobbered; A/B untouched; no added state RAM.
PRINT_REPAIR_PAPER_CONTINUATION PSHX
        LDX $45
        CPX #$70D6
        BNE PRINT_REPAIR_PAPER_END
        LDX #PRINT_RAW_PAPER_DONE
        STX $45
PRINT_REPAIR_PAPER_END PULX
        RTS

; Enter from native JMP [0045], with the interrupt-style frame still on stack.
; Native reverse-paper completion sets 18F7=$80; 728B consumes that latch and
; performs the required head preparation. Do not clear 18F4/18F7 ourselves.
PRINT_RAW_PAPER_DONE LDX #PRINT_GLYPH_COMPLETE
        STX $45
        JMP $728B
PRINT_PAPER_CONTINUATION_END EQU *
