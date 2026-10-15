; Keep the whole direct command separate from BUF, which INPUT reuses.
; A stack continuation survives RUN and nested calls; ERROR resets the stack.
DCSOURCE EQU $1CDC
DCBUFFER EQU $1D00
        ORG $5470 ; Retired integer ATOM, before NUMBER at $54DD.
DCHAIN LDX CUR
        STX DCSOURCE
        LDX #DCBUFFER
DCCOPY PSHX
        LDX DCSOURCE
        LDAA ,X
        INX
        STX DCSOURCE
        PULX
        STAA ,X
        INX
        TSTA
        BNE DCCOPY
        LDX #DCBUFFER
DCNEXT STX CUR
        PSHX
        LDX #KREM
        JSR MATCH
        PULX
        BCC DCDONE
        STX CUR
        CLRB
DCSCAN LDAA ,X
        BEQ DCLAST
        CMPA #34
        BNE DCNOTQUOTE
        COMB
DCNOTQUOTE TSTB
        BNE DCCHAR
        CMPA #58
        BEQ DCCOLON
DCCHAR INX
        BRA DCSCAN
DCCOLON CLR ,X
        INX
        BRA DCCALL
DCLAST LDX #0
DCCALL PSHX
        JSR EXECUTE
        PULX
        CPX #0
        BNE DCNEXT
DCDONE RTS
DCEND EQU *
