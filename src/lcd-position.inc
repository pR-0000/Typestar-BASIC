; Text cursor, one row / 32 columns, 1-based BASIC arguments.
; Parse and validate everything before changing the logical cursor.
; The rolling console shadow is authoritative; next LCDPUT refreshes DDRAM.
; No access to the indicator bank and no native Canon editor/IRQ calls.
LOCATE  JSR EXPR
        TSTA
        BNE LOCRANGE
        CMPB #1
        BNE LOCRANGE
        JSR SPACE
        CMPA #44
        BNE LOCSYNTAX
        INX
        STX CUR
        JSR EXPR
        TSTA
        BNE LOCRANGE
        TSTB
        BEQ LOCRANGE
        CMPB #32
        BHI LOCRANGE
        PSHB
        JSR EOS
        PULB
        DECB
        CLR UIPENDING
        STAB LCDPOS
        RTS
LOCRANGE JMP RANGEERROR
LOCSYNTAX JMP SYNTAX
; CLS clears text/triangles and LCDLINE-owned lower cells, preserving ICON/I-II.
CLS     JSR EOS
        CLR UIPENDING
        CLR LCDPOS
        LDX #LCDBUF
        LDAA #32
CLSLOOP STAA ,X
        INX
        CPX #LCDBUF+32
        BNE CLSLOOP
        JSR LCDREDRAW
        JMP $480C ; LOWCLEAR module entry
