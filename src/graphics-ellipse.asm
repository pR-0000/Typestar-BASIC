; Typestar BASIC: integer ellipse/disc rasterizer for one native glyph band.
; No timer/motor/bank accesses; standalone module, test origin inherited.
        INCLUDE "src/graphics-shapes.asm"

; X points to a 29-byte caller-owned job, disjoint from buffer and CPU stack:
; +0 buffer pointer word; +2 cx, +3 cy; +4 rx=1..15, +5 ry=1..7
; +6 inward thickness=1..16, +7 fill=0 outline / 1 solid
; +8..28 scratch: x,y,box bounds,squared radii,limits,offsets,partial sum.
; Bounding box must fit x=0..30,y=0..15. Radii/centres are raw grid units.
; Outer equation: dx^2*ry^2 + dy^2*rx^2 <= rx^2*ry^2.
; Outline removes the inner ellipse with radii rx-thickness,ry-thickness;
; if either inner radius is <=0, fill the outer ellipse. Always keep the
; discrete outer boundary (a four-neighbour pixel lies outside), so shallow
; ellipses do not acquire gaps when the inner ellipse is quantized.
; Not a uniform
; physical-width stroke: pitch compensation belongs to the higher layer.
; rx<=15, ry<=7 keep each square byte-sized and all sums <=22050.
; Add pixels by OR, keep guard untouched, preserve X/SP/IRQ mask.
; C=0 success; C=1 invalid inputs, with no buffer/job mutation.
GFX_ELLIPSE
        LDAA 4,X
        BEQ GEBAD
        CMPA #16
        BCC GEBAD
        LDAA 5,X
        BEQ GEBAD
        CMPA #8
        BCC GEBAD
        LDAA 6,X
        BEQ GEBAD
        CMPA #17
        BCC GEBAD
        LDAA 7,X
        CMPA #2
        BCC GEBAD
        LDAA 2,X
        SUBA 4,X
        BCS GEBAD
        LDAA 2,X
        ADDA 4,X
        BCS GEBAD
        CMPA #31
        BCC GEBAD
        LDAA 3,X
        SUBA 5,X
        BCS GEBAD
        LDAA 3,X
        ADDA 5,X
        BCS GEBAD
        CMPA #16
        BCC GEBAD
        BRA GEINIT
GEBAD   SEC
        RTS

GEINIT  LDAA 4,X
        TAB
        MUL
        STAB 14,X
        LDAA 5,X
        TAB
        MUL
        STAB 15,X
        LDAA 14,X
        MUL
        STD 16,X
        CLR 22,X
        LDAA 7,X
        BNE GEBOX
        LDAA 4,X
        SUBA 6,X
        BCS GEBOX
        BEQ GEBOX
        TAB
        MUL
        STAB 18,X
        LDAA 5,X
        SUBA 6,X
        BCS GEBOX
        BEQ GEBOX
        TAB
        MUL
        STAB 19,X
        LDAA 18,X
        MUL
        STD 20,X
        INC 22,X
GEBOX   LDAA 2,X
        SUBA 4,X
        STAA 10,X
        LDAA 2,X
        ADDA 4,X
        STAA 11,X
        LDAA 3,X
        SUBA 5,X
        STAA 9,X
        STAA 12,X
        LDAA 3,X
        ADDA 5,X
        STAA 13,X

GEROW   LDAA 10,X
        STAA 8,X
; Squared vertical distance is invariant for the whole row.
        LDAA 9,X
        SUBA 3,X
        BPL GEYPOS
        COMA
        INCA
GEYPOS  STAA 28,X
        TAB
        MUL
        STAB 24,X
GEPIXEL LDAA 8,X
        SUBA 2,X
        BPL GEXPOS
        COMA
        INCA
GEXPOS  STAA 27,X
        TAB
        MUL
        STAB 23,X
        LDAA 15,X
        MUL
        STD 25,X
        LDAA 24,X
        LDAB 14,X
        MUL
        ADDD 25,X
        SUBD 16,X
        BCS GEINSIDE
        BEQ GEINSIDE
        JMP GENEXT
GEINSIDE LDAA 22,X
        BEQ GEDRAW
        LDAA 23,X
        LDAB 19,X
        MUL
        STD 25,X
        LDAA 24,X
        LDAB 18,X
        MUL
        ADDD 25,X
        SUBD 20,X
        BCS GEBORDER
        BEQ GEBORDER
        BRA GEDRAW
; The pixel is inside the inner ellipse. Retain it if either outward axial
; neighbour falls outside the outer ellipse. By symmetry only +abs(dx) and
; +abs(dy) are needed. Check extrema first to keep squares byte-sized.
GEBORDER LDAA 27,X
        CMPA 4,X
        BCC GEDRAW
        LDAA 28,X
        CMPA 5,X
        BCC GEDRAW
        LDAA 27,X
        INCA
        TAB
        MUL
        LDAA 15,X
        MUL
        STD 25,X
        LDAA 24,X
        LDAB 14,X
        MUL
        ADDD 25,X
        SUBD 16,X
        BCS GEYEDGE
        BEQ GEYEDGE
        BRA GEDRAW
GEYEDGE LDAA 28,X
        INCA
        TAB
        MUL
        LDAA 14,X
        MUL
        STD 25,X
        LDAA 23,X
        LDAB 15,X
        MUL
        ADDD 25,X
        SUBD 16,X
        BCS GENEXT
        BEQ GENEXT
GEDRAW  LDAA 8,X
        LDAB 9,X
        PSHX
        LDX 0,X
        JSR GFX_PSET
        PULX
GENEXT  LDAA 8,X
        CMPA 11,X
        BEQ GEENDROW
        INC 8,X
        JMP GEPIXEL
GEENDROW LDAA 9,X
        CMPA 13,X
        BEQ GEDONE
        INC 9,X
        JMP GEROW
GEDONE  CLC
        RTS
GFX_ELLIPSE_END EQU *
