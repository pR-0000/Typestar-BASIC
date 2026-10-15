; Called instead of LPFORMAT, before the first glyph of each BASIC band.
; Text uses 96-byte cached glyphs: leave its count and path unchanged.
; Graphics tiles are 64 bytes including guard column. Trim only whole tiles.
; Keep RBTILES/RBBACKUP intact for rendering and workspace restoration.
PETAIL STAA GPDESC+1
        BNE PEDONE
        LDAA RBTILES
        STAA GXNX
        LDX RBBACKUP
PENEXT CLRA
        LDAB #64
PEBYTE DEX
        ORAA ,X
        DECB
        BNE PEBYTE
        TSTA
        BNE PEDONE
        DEC GXNX
        BNE PENEXT
        ; All blank: discard LPFORMAT return, feed without zero-distance
        ; carriage move, then continue RBROW after its LPROW call.
        PULX
        JSR GPROW+24
        JMP RBROW+3
PEDONE RTS
PEEND EQU *
