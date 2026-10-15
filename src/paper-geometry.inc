; Logical paper units: one unit = one native horizontal column.
; Current measured approximation: one native vertical dot = two units.
; Geometry is quantized down at endpoints; vertical stroke thickness rounds up.
; Raw glyph matrices and the PC serial raster protocol remain native.
; B=tile count on entry, preserved until RBJOB. Parameters are already validated.
        ORG $4BC8
PGSTART LSR PBTOP+1
        LSR PBBOTTOM+1
        LDAA PBWIDTH
        INCA
        LSRA
        STAA PGYWIDTH
        LDAA PBBOTTOM+1
        LSRA
        LSRA
        LSRA
        LSRA
        INCA
        JMP RBJOB
PGSTARTEND EQU *
; D is an unsigned distance from a vertical boundary, in native rows.
        ORG $56E8
PGVNEAR TSTA
        BNE PGFAR
        CMPB PGYWIDTH
        RTS
PGFAR CLC
        RTS
PGVEND EQU *
