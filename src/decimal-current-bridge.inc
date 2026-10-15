; OFFLINE bridge for the current production core. Never modifies reset/CRC.
; Decimal variables live in the unused upper part of document RAM (6 bytes each).
; Existing numeric hardware commands receive only exactly integral values.
        ORG $A500
        JMP DPRINTBRIDGE
        JMP DLETBRIDGE
        JMP DCLEARBRIDGE
        JMP DHEAPBRIDGE
        JMP DMEMBRIDGE
        JMP DINTBRIDGE
        JMP DEDITBRIDGE
        JMP DNOTYET
        JMP DFAIL ; A518: shared decimal error translation.
DPRINTBRIDGE LDX CUR
        JSR $A000
        STX CUR
        TSTA
        BNE DFAIL
        JSR $A003
        JMP PUTS
DLETBRIDGE LDX PEND
        INX
        STX $1EC0 ; DFLOOR always follows the current program sentinel.
        LDX CUR
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
; Called at STORELINE PCAPOK, after capacity validation, before mutation.
; Discard volatile variables on successful line editing; never protect them
; with the program CRC or let them constrain an edit that discards them.
DEDITBRIDGE JSR $4409
        JMP DHEAPBRIDGE
DMEMBRIDGE JSR EOS
        LDD $1EBE
        SUBD PEND
        SUBD #1
        JSR OUTNUM
        LDX #MEMTEXT
        JMP PUTS
DINTBRIDGE LDX CUR
        JSR $A000
        STX CUR
        TSTA
        BNE DFAIL
        JSR $A400
        BCS DIRANGE
        RTS
DIRANGE JMP RANGEERROR
DFAIL CMPA #1
        BNE DFNOTSYNTAX
        JMP SYNTAX
DFNOTSYNTAX CMPA #5
        BNE DFNOTRAM
        JMP PMEMERROR ; Allocation refusal must not invalidate program/PEND.
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
