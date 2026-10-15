; LIST uses a separate 68-byte staging buffer: number + space + 63 + NUL.
; It never alters BUF (input), PROGRAM, or the live editor cursor.
LWIN EQU $19CB
LLEN EQU $19CC
LLAST EQU $19CD
LBUFFER EQU $1B00
LIST    JSR DIRECTONLY
        JSR SPACE
        TSTA
        BNE LISTONE
        LDAA #255
        STAA LLAST
        LDAA #1
        BRA LISTSET
LISTONE JSR EXPR
        JSR CHECKLINE
        PSHB
        STAB LLAST
        JSR SPACE
        CMPA #44
        BNE LISTEXACT
        INX
        STX CUR
        JSR EXPR
        JSR CHECKLINE
        STAB LLAST
LISTEXACT JSR EOS
        PULA
        CMPA LLAST
        BLS LISTSET
        JMP RANGEERROR
LISTSET STAA LINE
LISTNEXT JSR SLOT
        LDAA ,X
        BNE LISTPRESENT
        JMP LISTSKIP
LISTPRESENT LDX #LBUFFER
        LDAB LINE
        JSR $4415
        LDAA #32
        STAA ,X
        INX
        STX HDEST
        JSR SLOT
LISTCOPY LDAA ,X
        PSHX
        LDX HDEST
        CPX #LBUFFER+68
        BCS LISTCOPYSAFE
        JMP PRAMERROR
LISTCOPYSAFE STAA ,X
        INX
        STX HDEST
        PULX
        INX
        TSTA
        BNE LISTCOPY
        LDAA HDEST+1
        DECA
        STAA LLEN
        CLR LWIN
        JSR LISTSHOW
LISTWAIT JSR GETC
        CMPA #3
        BNE LISTNOTBREAK
        JMP BREAK
LISTNOTBREAK CMPA #13
        BEQ LISTACK
        CMPA #$12
        BNE LISTRIGHT
        TST LWIN
        BEQ LISTWAIT
        DEC LWIN
        BRA LISTREDRAW
LISTRIGHT CMPA #$13
        BNE LISTWAIT
        LDAA LWIN
        ADDA #32
        CMPA LLEN
        BCC LISTWAIT
        INC LWIN
LISTREDRAW JSR LISTSHOW
        BRA LISTWAIT
LISTACK JSR HISTSAVE
LISTSKIP LDAA LINE
        CMPA LLAST
        BEQ LISTEND
        INC LINE
        JMP LISTNEXT
LISTEND INC UIPENDING
        RTS
LISTSHOW JSR UICLEAR
        LDX #LCDBUF
        STX HDEST
        LDX #LBUFFER
        LDAB LWIN
        ABX
LISTPAINT LDAA ,X
        BEQ LISTPAINTEND
        PSHX
        LDX HDEST
        STAA ,X
        INX
        STX HDEST
        PULX
        INX
        LDAB HDEST+1
        CMPB #$C0
        BNE LISTPAINT
LISTPAINTEND JMP LCDREDRAW
