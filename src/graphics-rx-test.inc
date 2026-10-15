; CODE+P reception diagnostic, deliberately NO motor calls and NO BASIC command.
; Only a complete 62x32 TPG1 image (four 31x16 tiles) is accepted.
; Workspace temporarily owns decimal expression/native arithmetic scratch:
; no program may be running; persistent program/heap and editor BUF stay intact.
; Header/data/end require valid CRC before structure/content decoding.
; Wire: identification, then ACK for each accepted line. Final PC ACK drains TX.
; Decoded glyphs are discarded after validation; ACK never means printed here.
GXEDIT CMPA #$16
        BEQ GXSTART
        CMPA #32
        BCS GXIGNORE
        JMP EDPRINTABLE+4
GXIGNORE JMP EDIGNORE
GXSTART CLR $19FB ; Suspend software cursor while showing session messages.
        LDAA #$0C
        JSR LCDCMD
        JSR UICLEAR
        LDX #GXWAITMSG
        JSR PUTS
        CLR GXINDEX
        JSR SERIALINIT
        LDX #GXIDENT
GXHELLO LDAA 0,X
        BEQ GXLINE
        JSR GXTX
        BCS GXFAIL
        INX
        BRA GXHELLO
GXLINE CLR GXCOUNT
        LDX #GXBUFFER
GXREAD JSR GXRX
        BCS GXFAIL
        CMPA #10
        BEQ GXCHECK
        LDAB GXCOUNT
        CMPB #150
        BCC GXFAIL
        STAA 0,X
        INX
        INC GXCOUNT
        BRA GXREAD
GXCHECK LDX #GXBUFFER
        LDAB GXCOUNT
        JSR GRAPHICS_FRAME
        BCS GXFAIL
        JSR GXSTRUCT
        BCS GXFAIL
        INC GXINDEX
        LDAA #6
        JSR GXTX
        BCS GXFAIL
        LDAA GXINDEX
        CMPA #6
        BNE GXLINE
        JSR GXRX ; Host confirms the last acknowledgement before SCI shutdown.
        BCS GXFAIL
        CMPA #6
        BNE GXFAIL
        JSR SERIALCLOSE
        LDX #GXOKMSG
        BRA GXRESULT
GXFAIL JSR SERIALCLOSE
        LDX #GXFAILMSG
GXRESULT PSHX
        JSR UICLEAR
        PULX
        JSR PUTS
GXWAITKEY JSR GETC
        TSTA
        BEQ GXWAITKEY
        CLR HVIEW
        INC $19FB ; Restore console ownership before EDSHOW enables its cursor.
        JMP EDRESTORE ; Re-render the untouched input line and cursor.

; Compare complete header/end bodies or the exact next data prefix.
; This diagnostic rejects retries, duplicates, reordering and wrong dimensions.
GXSTRUCT LDAB GXINDEX
        ASLB
        LDX #GXPREFIXES
        ABX
        LDX 0,X
        STX GXPTR
        LDAA GXINDEX
        BEQ GXHEADER
        CMPA #5
        BEQ GXENDLINE
        LDAA #150
        BRA GXLENGTH
GXHEADER LDAA #19
        BRA GXLENGTH
GXENDLINE LDAA #15
GXLENGTH CMPA GXCOUNT
        BNE GXINVALID
        LDX #GXBUFFER
GXCMP PSHX
        LDX GXPTR
        LDAA 0,X
        INX
        STX GXPTR
        PULX
        TSTA
        BEQ GXMATCH
        CMPA 0,X
        BNE GXINVALID
        INX
        BRA GXCMP
GXMATCH LDAA GXINDEX
        BEQ GXVALID
        CMPA #5
        BEQ GXVALID
        ; Decode 124 hex characters to 62 bytes plus Canon zero terminator.
        LDD #GXPATTERN
        STD GXPTR
        LDAA #62
        STAA GXLEFT
GXDECODE JSR GF_HEXBYTE
        BCS GXINVALID
        PSHX
        LDX GXPTR
        STAA 0,X
        INX
        STX GXPTR
        PULX
        DEC GXLEFT
        BNE GXDECODE
        LDX #GXPATTERN+62
        CLR 0,X
        CLR 1,X
GXVALID CLC
        RTS
GXINVALID SEC
        RTS

; Local bounded SCI routines return errors to this session, never ERRORWAIT:
; that would discard the editor line and reset the caller's stack.
GXRX PSHX
        LDX #$FFFF
GXRXWAIT LDAA $11
        BITA #$40
        BNE GXIOBAD
        LDAA $1E
        BITA #$10
        BNE GXIOBAD
        LDAA $11
        BITA #$80
        BNE GXRXREADY
        PSHX
        JSR KBDSCAN
        PULX
        CMPA #$36 ; Margin release: BREAK while waiting for serial input.
        BEQ GXIOBAD
        DEX
        BNE GXRXWAIT
GXIOBAD PULX
        SEC
        RTS
GXRXREADY LDAA $1E
        BITA #$50
        BNE GXIOBAD
        LDAA $12
        ANDA #$7F
        PULX
        CLC
        RTS
GXTX PSHX
        PSHA
        LDX #$FFFF
GXTXWAIT LDAA $11
        BITA #$20
        BNE GXTXREADY
        DEX
        BNE GXTXWAIT
        PULA
        BRA GXIOBAD
GXTXREADY PULA
        STAA $13
        PULX
        CLC
        RTS
GXIDENT FCC "TPG1 RX ONLY"
        FCB 13,10,0
GXWAITMSG FCC "GFX RX TEST - PC / BREAK"
        FCB 0
GXOKMSG FCC "GFX RX OK 4 - KEY"
        FCB 0
GXFAILMSG FCC "GFX RX STOP/ERROR - KEY"
        FCB 0
GXPREFIXES FDB GXHEAD,GXTILE0,GXTILE1,GXTILE2,GXTILE3,GXEND
GXHEAD FCC "TPG1:003E:0020"
        FCB 0
GXTILE0 FCC "D:00000000:0000:0000:"
        FCB 0
GXTILE1 FCC "D:00000001:0000:0001:"
        FCB 0
GXTILE2 FCC "D:00000002:0001:0000:"
        FCB 0
GXTILE3 FCC "D:00000003:0001:0001:"
        FCB 0
GXEND FCC "E:00000004"
        FCB 0
GRAPHICS_RX_END EQU *
