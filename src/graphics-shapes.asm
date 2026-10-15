; Typestar BASIC: rectangle raster primitive, no physical printer output.
; Includes existing point/line primitives unchanged. Test origin only.
        INCLUDE "src/graphics-ram.asm"

; X = caller-owned job, disjoint from 64-byte glyph buffer and CPU stack:
; +0 buffer pointer word; +2 x0, +3 y0, +4 x1, +5 y1 (inclusive corners)
; +6 border thickness 1..16; +7 fill 0=outline, 1=solid
; +8 current x, +9 current y (scratch)
; Require 0<=x0<=x1<=30 and 0<=y0<=y1<=15; no clipping/reordering.
; Outline grows INWARD from the bounding box, so dimensions remain fixed.
; Points are added by OR. A thick border covering the interior becomes solid.
; C=0 success, C=1 invalid arguments (no useful RAM mutation on error).
; Preserve X/SP/IRQ mask; A/B/other flags scratch. Not a BASIC command yet.
GFX_RECT
        LDAA 4,X
        CMPA #31
        BCC GRBAD
        CMPA 2,X
        BCS GRBAD
        LDAA 5,X
        CMPA #16
        BCC GRBAD
        CMPA 3,X
        BCS GRBAD
        LDAA 6,X
        BEQ GRBAD
        CMPA #17
        BCC GRBAD
        LDAA 7,X
        CMPA #2
        BCC GRBAD
        LDAA 3,X
        STAA 9,X
        BRA GRROW
GRBAD   SEC
        RTS

GRROW   LDAA 2,X
        STAA 8,X
GRPIXEL LDAA 7,X
        BNE GRDRAW
; Distance to each edge in raw raster cells, not calibrated millimetres.
        LDAA 8,X
        SUBA 2,X
        CMPA 6,X
        BCS GRDRAW
        LDAA 4,X
        SUBA 8,X
        CMPA 6,X
        BCS GRDRAW
        LDAA 9,X
        SUBA 3,X
        CMPA 6,X
        BCS GRDRAW
        LDAA 5,X
        SUBA 9,X
        CMPA 6,X
        BCC GRNEXT
GRDRAW  LDAA 8,X
        LDAB 9,X
        PSHX
        LDX 0,X
        JSR GFX_PSET
        PULX
GRNEXT  LDAA 8,X
        CMPA 4,X
        BEQ GRROWEND
        INC 8,X
        BRA GRPIXEL
GRROWEND LDAA 9,X
        CMPA 5,X
        BEQ GRDONE
        INC 9,X
        BRA GRROW
GRDONE  CLC
        RTS
GFX_SHAPES_END EQU *
