; Experimental continuation for one RAW GLYPH, not the entire print request.
; Enter by native JMP [0045], in an interrupt context with the original
; seven-byte CPU frame still on the stack. Never call with JSR.
; PRINT_GLYPH_BUSY is supplied by the integrator (test address $1B94 only).
; The foreground owns the request and sets BUSY=1 before enabling its IRQ.
; Do not restore native position/phase state: subsequent glyphs need it.
; The tested entry is native timer dispatcher $77EF, stage12 ($747C).
; Dispatcher masks $08 with $F5 (clears bits1/3) before invoking the stage.
; Neither this callback nor stage12 rearms bit3. Do not bypass $77EF and
; assume this callback alone masks interrupts. Pending hardware flags and
; other interrupt sources remain outside the CPU-only validation.
PRINT_GLYPH_COMPLETE
        CLR PRINT_GLYPH_BUSY
        RTI
