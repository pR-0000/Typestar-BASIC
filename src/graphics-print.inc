; Console-only TPG1 printer, bounded 248x256 image, one job per boot.
; A valid CRC and the expected sequence/coordinates precede every motor call.
; ACK means the tile AND its possible row-return/feed have completed.
; Metadata, SCI frame and native printer scratch are disjoint. Editor and heap
; remain owned by BASIC. No retransmission: an uncertain ACK ends the job.
GXEDIT CMPA #$16
        BEQ GXSTART
        CMPA #32
        BCS GXIGNORE
        JMP EDPRINTABLE+4
GXIGNORE JMP EDIGNORE
GXSTART STS GPSP
        CLR $19FB
        LDAA #$0C
        JSR LCDCMD
        JSR UICLEAR
        CLR GPERROR
        CLR PRINT_GLYPH_BUSY
        TST GPRAN
        BEQ GXNEW
        LDX #GPAGAINMSG
        JMP GXRESULT
GXNEW INC GPRAN
        CLR GXSTATE
        CLR GXCOL
        CLR GXROW
        CLR GXSEQ
        CLR GXSEQ+1
        LDAA $08
        ANDA #$1F
        STAA GPSAVED08
        LDX #GXWAITMSG
        JSR PUTS
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
        ; All motor outputs are off before accepting another serial record.
        LDAA #6
        JSR GXTX
        BCS GXFAIL
        LDAA GXSTATE
        CMPA #3
        BNE GXLINE
        JSR GXRX ; Host drains the final ACK before SCI is closed.
        BCS GXFAIL
        CMPA #6
        BNE GXFAIL
        JSR SERIALCLOSE
        LDX #GXOKMSG
        BRA GXRESULT
GXFAIL SEI
        LDS GPSP ; Discard any parser/driver frames, preserve editor call stack.
        JSR GPOFF
        JSR SERIALCLOSE
        LDX #GXFAILMSG
GXRESULT PSHX
        JSR UICLEAR
        PULX
        JSR PUTS
        TST GPERROR
        BEQ GXWAITKEY
        LDAA GPERROR
        JSR SSTATUSHEX
GXWAITKEY JSR GETC
        TSTA
        BEQ GXWAITKEY
        CLR HVIEW
        INC $19FB
        JMP EDRESTORE

GXSTRUCT LDX #GXBUFFER
        LDAA GXSTATE
        BEQ GXHEADER
        CMPA #2
        BNE GXDATA
        JMP GXENDLINE
GXHEADER LDAA GXCOUNT
        CMPA #19
        BNE GXBAD
        LDD 0,X
        SUBD #$5450 ; TP
        BNE GXBAD
        LDD 2,X
        SUBD #$4731 ; G1
        BNE GXBAD
        LDAB #4
        ABX
        JSR GXCOLON
        JSR GXWORD
        TSTA
        BNE GXBAD
        TSTB
        BEQ GXBAD
        CMPB #248
        BHI GXBAD
        CLRA
GXWIDTH INCA
        SUBB #31
        BHI GXWIDTH
        STAA GXNX
        JSR GXCOLON
        JSR GXWORD
        SUBD #1
        BCS GXBAD
        TSTA ; height-1 must fit in one byte (1..256 rows).
        BNE GXBAD
        LSRD
        LSRD
        LSRD
        LSRD
        INCB
        STAB GXNY
        INC GXSTATE
        RTS
GXBAD JMP GXFAIL
GXDATA LDAA GXCOUNT
        CMPA #150
        BNE GXBAD
        LDAA 0,X
        CMPA #$44 ; D
        BNE GXBAD
        INX
        JSR GXSEQUENCE
        JSR GXCOLON
        JSR GXWORD
        TSTA
        BNE GXBAD
        CMPB GXROW
        BNE GXBAD
        JSR GXCOLON
        JSR GXWORD
        TSTA
        BNE GXBAD
        CMPB GXCOL
        BNE GXBAD
        JSR GXCOLON
        LDD #GXPATTERN
        STD GXPTR
        LDAA #62
        STAA GXLEFT
GXDECODE JSR GF_HEXBYTE
        BCS GXBAD
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
        JSR KBDSCAN ; BREAK is sampled between complete thermal glyphs.
        CMPA #$36
        BNE GXPRINTTILE
        JMP GXFAIL
GXPRINTTILE EQU *
        ; Host must wait for ACK, but also withdraw CTS while motors run.
        LDAA $69
        ORAA #2
        STAA $69
        STAA $03
        JSR GPPRINT
        INC GXCOL
        LDAA GXCOL
        CMPA GXNX
        BNE GXTILEDONE
        JSR GPROW ; Return X and advance one 16-row band, including final band.
        CLR GXCOL
        INC GXROW
        LDAA GXROW
        CMPA GXNY
        BNE GXTILEDONE
        INC GXSTATE
GXTILEDONE LDX GXSEQ
        INX
        STX GXSEQ
        LDAA $69
        ANDA #$FD
        STAA $69
        STAA $03
        RTS
GXENDLINE LDAA GXCOUNT
        CMPA #15
        BNE GXBAD2
        LDAA 0,X
        CMPA #$45 ; E
        BNE GXBAD2
        INX
        JSR GXSEQUENCE
        INC GXSTATE
        RTS
GXSEQUENCE JSR GXCOLON
        JSR GXWORD ; 32-bit wire sequence, high word must be zero for this cap.
        SUBD #0
        BNE GXBAD2
        JSR GXWORD
        SUBD GXSEQ
        BNE GXBAD2
        RTS
GXCOLON LDAA 0,X
        CMPA #$3A
        BNE GXBAD2
        INX
        RTS
GXWORD JSR GF_HEXBYTE
        BCS GXBAD2
        STAA GXHIGH
        JSR GF_HEXBYTE
        BCS GXBAD2
        TAB
        LDAA GXHIGH
        RTS
GXBAD2 JMP GXFAIL
GXIDENT FCC "TPG1 PRINT 0248 0256"
        FCB 13,10,0
GXWAITMSG FCC "GFX PRINT - PC / BREAK"
        FCB 0
GXOKMSG FCC "GFX PRINT OK - KEY"
        FCB 0
GXFAILMSG FCC "GFX STOP/ERROR "
        FCB 0
GPAGAINMSG FCC "RESTART FOR NEXT PRINT"
        FCB 0
