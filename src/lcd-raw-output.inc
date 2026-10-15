; .82: assembly equivalent of the guarded in-place patch in build_lcd_raw.py.
; Installed at the retired SOFTBLOCK entry. Called only by STLCD (counted
; string PRINT), not by PUTC's numeric/control output. Preserve A, B and X.
LCDRAWPUT PSHA
        PSHB
        PSHX
        PSHA
        LDAA #1
        STAA OUTFLAG
        PULA
        CMPA #16
        BCC LCDRAWREADY
        ANDA #7 ; canonicalize CGRAM aliases 08..0F for slot occupancy scans
LCDRAWREADY JSR LCDPRINTABLE+8 ; enter normal placement after both filters
        PULX
        PULB
        PULA
        RTS
; Cursor tick now emits native CGROM code $AB. SOFTAPPLY's call to the
; old slot-7 initializer is removed. TRINEXTSLOT allows 8 slots; LCTRI
; recognizes slot 7 as a customizable glyph, just like slots 0..6.
