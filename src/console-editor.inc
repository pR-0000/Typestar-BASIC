; Canon-only editor. UI state $19C1..$19CA; eight LCD rows $1A00..$1AFF.
; Input BUF remains 64 bytes including NUL. History is output, not program RAM.
EDWIDTH EQU $19DB ; Editable LCD width: 31 console, 14..30 during INPUT.
EDLEN EQU $19C1
EDPOS EQU $19C2
EDWIN EQU $19C3
HCOUNT EQU $19C4
HNEXT EQU $19C5
HVIEW EQU $19C6
HDEST EQU $19C7
EDCHAR EQU $19C9
HISTORY EQU $1A00
BOOTFLAG EQU $19E7 ; Raw key/Shift may dismiss startup; disabled afterwards.
OUTFLAG EQU $19E8 ; Output was produced, or RUN was invoked.
CURSORMODE EQU $19E9 ; Hardware modes 0C..0F, or 10 for software-only text blinking.
WAITSHIFT EQU $19EA ; Last Shift level during any-key wait.
UIINIT CLR SACTIVE
        CLR WAITSHIFT
        LDAA #16
        STAA CURSORMODE
        CLR $19FB
        LDAA #1
        STAA BOOTFLAG
        CLR HCOUNT
        CLR HNEXT
        CLR HVIEW
        CLR UIPENDING
        RTS
; Archive the current physical row. Ring slots are exactly 32 bytes.
HISTSAVE LDAB HNEXT
        ASLB
        ASLB
        ASLB
        ASLB
        ASLB
        LDX #HISTORY
        ABX
        STX HDEST
        LDX #LCDBUF
HISTCOPY LDAA ,X
        PSHX
        LDX HDEST
        STAA ,X
        INX
        STX HDEST
        PULX
        INX
        CPX #LCDBUF+32
        BNE HISTCOPY
        LDAA HNEXT
        INCA
        ANDA #7
        STAA HNEXT
        LDAA HCOUNT
        CMPA #8
        BEQ HISTEND
        INC HCOUNT
HISTEND RTS
; Clear text shadow only, avoiding CLS's parser/EOS check.
UICLEAR CLR LCDPOS
        CLR UIPENDING
        LDX #LCDBUF
        LDAA #32
UICLEARLOOP STAA ,X
        INX
        CPX #LCDBUF+32
        BNE UICLEARLOOP
        RTS
; Render input as > plus a 31-cell viewport. All 63 input bytes editable.
EDSHOW CLR HVIEW
        LDAA EDPOS
        CMPA EDWIN
        BCC EDWINRIGHT
        STAA EDWIN
EDWINRIGHT SUBA EDWIN
        CMPA EDWIDTH
        BCS EDWINDOWOK
        LDAA EDPOS
        SUBA EDWIDTH
        INCA
        STAA EDWIN
EDWINDOWOK JSR UICLEAR
        JSR $4206 ; Console or INPUT prefix; returns first editable cell.
        STX HDEST
        LDX #BUF
        LDAB EDWIN
        ABX
EDCOPY CPX #BUF+63
        BHI EDPAINT
        LDAA ,X
        BEQ EDPAINT
        PSHX
        LDX HDEST
        STAA ,X
        INX
        STX HDEST
        PULX
        INX
        LDAB HDEST+1
        CMPB #$C0
        BNE EDCOPY
EDPAINT JSR LCDREDRAW
        LDAA EDPOS
        SUBA EDWIN
        ADDA #32
        SUBA EDWIDTH
        ORAA #$80
        JSR LCDCMD
        JMP $480F ; Reset/apply hardware or software cursor mode.
; Browse output rows without copying them over BUF or the live shadow.
HISTSHOW LDAA #$0C
        JSR LCDCMD
        LDAA HNEXT
        SUBA HVIEW
        ANDA #7
        TAB
        ASLB
        ASLB
        ASLB
        ASLB
        ASLB
        LDX #HISTORY
        ABX
        STX HDEST
        LDAA #$80
        JSR LCDCMD
        LDAB #32
HISTPAINT LDAA ,X
        JSR LCDDATA
        INX
        DECB
        BNE HISTPAINT
        RTS
; A completed output/run stays on LCD. Only a fresh key event dismisses it;
; in particular, the still-held Return which launched it cannot dismiss it.
RESULTWAIT TST OUTFLAG
        BEQ RESULTRET
        LDAA $32
        ANDA #$80
        STAA WAITSHIFT
        LDAA #1
        STAA BOOTFLAG
RESULTKEY JSR GETC
        CLR BOOTFLAG
RESULTRET RTS
KCURSOR FCC "CURSOR"
        FCB 0
; 0 software block (default), 1..3 hardware, 4 disabled.
CURSORCMD JMP $4815
; CR and submission have already archived their row. Do not archive a
; second copy or a temporary prompt while entering the next input line.
READLINE LDAA #31
        STAA EDWIDTH
READINPUT TST UIPENDING
        BNE EDSTART
        TST LCDPOS
        BEQ EDSTART
        JSR HISTSAVE
EDSTART LDAA #1
        STAA $19FB
        CLR EDLEN
        CLR EDPOS
        CLR EDWIN
        CLR BUF
        JSR EDSHOW
READNEXT JSR GETC
        CMPA #3
        BNE EDNOTBREAK
        LDAA #$0C
        JSR LCDCMD
        JMP BREAK
EDNOTBREAK CMPA #13
        BNE EDNOTRETURN
        JMP EDDONE
EDNOTRETURN CMPA #$14  ; Raw $38: older output row.
        BNE EDNOTOLDER
        LDAA HVIEW
        CMPA HCOUNT
        BCC READNEXT
        INC HVIEW
        JSR HISTSHOW
        BRA READNEXT
EDNOTOLDER CMPA #$15  ; Raw $39: newer output row / active input.
        BNE EDNOTNEWER
        TST HVIEW
        BEQ READNEXT
        DEC HVIEW
        BEQ EDRESTORE
        JSR HISTSHOW
        BRA READNEXT
EDRESTORE JSR EDSHOW
        BRA READNEXT
EDNOTNEWER CMPA #$12  ; Left
        BNE EDNOTLEFT
        TST EDPOS
        BEQ EDRESTORE
        DEC EDPOS
        BRA EDRESTORE
EDNOTLEFT CMPA #$13  ; Right
        BNE EDNOTRIGHT
        LDAA EDPOS
        CMPA EDLEN
        BCC EDRESTORE
        INC EDPOS
        BRA EDRESTORE
EDNOTRIGHT CMPA #8
        BNE EDPRINTABLE
        TST EDPOS
        BEQ EDRESTORE
        DEC EDPOS
        DEC EDLEN
        LDX #BUF
        LDAB EDPOS
        ABX
EDDELETE LDAA 1,X
        STAA ,X
        INX
        TSTA
        BNE EDDELETE
        BRA EDRESTORE
EDPRINTABLE CMPA #32
        BCS EDIGNORE
        CMPA #126
        BHI EDIGNORE
        STAA EDCHAR
        LDAA EDLEN
        CMPA #63
        BCC EDFULL
        LDX #BUF
        LDAB EDPOS
        ABX
        STX HDEST
        LDX #BUF
        LDAB EDLEN
        ABX
; Shift suffix including NUL right; insertion at cursor, no overwrite.
EDSHIFT LDAA ,X
        STAA 1,X
        CPX HDEST
        BEQ EDINSERT
        DEX
        BRA EDSHIFT
EDINSERT LDAA EDCHAR
        STAA ,X
        INC EDLEN
        INC EDPOS
        JSR EDSHOW
EDIGNORE JMP READNEXT
; At the limit reject extra bytes; existing line remains editable/submittable.
EDFULL JSR EDSHOW
        BRA EDIGNORE
EDDONE CLR $19FB
        LDAA #$0C
        JSR LCDCMD
        ; Archive the visible submitted row; full program remains in BUF.
        JSR EDSHOW
        LDAA #$0C
        JSR LCDCMD
        JSR HISTSAVE
        INC UIPENDING
        RTS
