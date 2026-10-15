; Offline BASIC integration bridge. Main symbol ABI supplied by builder.
; Unsupported integer numeric paths fail explicitly; never read stale VARS.
        ORG $A500
        JMP DPRINTBRIDGE
        JMP DLETBRIDGE
        JMP DCLEARBRIDGE
        JMP DHEAPBRIDGE
        JMP DMEMBRIDGE
        JMP DNOTYET
DPRINTBRIDGE LDX CUR
        JSR $A000
        STX CUR
        TSTA
        BNE DFAIL
        JSR $A003
        JMP PUTS
DLETBRIDGE LDX CUR
        JSR $A006
        STX CUR
        TSTA
        BNE DFAIL
        RTS
DCLEARBRIDGE CLR $1974
        CLR $197F
        LDX #VARS
DCLEARLOOP CLR ,X
        INX
        CPX #VARS+52
        BNE DCLEARLOOP
DHEAPBRIDGE LDX PEND
        INX
        JSR $A009
        TSTA
        BNE DFAIL
        RTS
DMEMBRIDGE JSR EOS
        LDD $1EBE
        SUBD PEND
        SUBD #1
        JSR OUTNUM
        LDX #MEMTEXT
        JMP PUTS
DFAIL   CMPA #1
        BNE DFNOTSYNTAX
        JMP SYNTAX
DFNOTSYNTAX CMPA #5
        BNE DFNOTRAM
        JMP PRAMERROR
DFNOTRAM CMPA #3
        BNE DFNOTDEPTH
        LDX #DDEPTHMSG
        JMP ERROR
DFNOTDEPTH CMPA #2
        BNE DFNOTMATH
        LDX #DMATHMSG
        JMP ERROR
DFNOTMATH JMP RANGEERROR
DNOTYET LDX #DTODOMSG
        JMP ERROR
DDEPTHMSG FCC "?EXPR DEPTH"
        FCB 0
DMATHMSG FCC "?DECIMAL MATH"
        FCB 0
DTODOMSG FCC "?DECIMAL TODO"
        FCB 0
