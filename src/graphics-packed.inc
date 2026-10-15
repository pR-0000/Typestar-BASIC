; Console-only band-buffered TPG2 printer, 248x256, one job per boot.
; A valid CRC and the expected sequence/coordinates precede every motor call.
; ACK before end of band means BUFFERED, not printed. Last ACK in each band
; means the entire band, row-return and feed have completed. Distinct identity.
; Metadata, SCI frame and native printer scratch are disjoint. Conditional NEW
; is authorized by TPG2 only on first valid tile, when free band RAM is short.
; No retransmission: an uncertain ACK ends the job.
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
        CLR GXBASE
        CLR GXBASE+1
        CLR GXCLEARED
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
        SUBD #$4732 ; G2: explicitly authorizes conditional NEW on job commit.
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
        CMPA #30 ; prefix21 + at least one count/value pair4 + CRC5
        BCS GXBAD
        SUBA #5
        TAB
        ABX
        STX GXENDPTR
        LDX #GXBUFFER
        LDAA 0,X
        CMPA #$42 ; B = compact six-bit symbols
        BEQ GXKINDOK
        CMPA #$52 ; R = hexadecimal byte runs
        BNE GXBAD
GXKINDOK STAA GXKIND
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
        STD GXOUTPTR
        LDAA #62
        STAA GXLEFT
        LDAA GXKIND
        CMPA #$42
        BNE GXUSERUNS
        JSR GXPACKED
        BRA GXVALIDBLOCK
GXUSERUNS JSR GXRUNS
GXVALIDBLOCK EQU *
        ; Commit ONLY after a full CRC/sequence/payload-validated first tile.
        ; Header-only sessions and malformed first tiles never reach NEW.
        LDX GXBASE
        BNE GXCOPYBLOCK
        JSR KBDSCAN
        CMPA #$36
        BNE GXCOMMIT
        JMP GXFAIL
GXCOMMIT JSR GXALLOC
GXCOPYBLOCK LDD GXWRITE
        STD GXPTR
        LDX #GXPATTERN
        LDAB #62
GXCOPYBYTE LDAA 0,X
        PSHX
        LDX GXPTR
        STAA 0,X
        INX
        STX GXPTR
        PULX
        INX
        DECB
        BNE GXCOPYBYTE
        LDX GXPTR
        CLR 0,X
        CLR 1,X
        INX
        INX
        STX GXWRITE
        INC GXCOL
        LDAA GXCOL
        CMPA GXNX
        BNE GXTILEDONE
        JSR KBDSCAN ; BREAK before a band; no keyboard wait in the fast chain.
        CMPA #$36
        BNE GXPRINTTILE
        JMP GXFAIL
GXPRINTTILE EQU *
        ; Host must wait for ACK, but also withdraw CTS while motors run.
        LDAA $69
        ORAA #2
        STAA $69
        STAA $03
        LDX GXBASE
        STX GXPATPTR
        CLR GXPRINTCOL
GXPRINTNEXT JSR GPPRINT
        INC GXPRINTCOL
        LDAA GXPRINTCOL
        CMPA GXNX
        BEQ GXPRINTDONE
        LDD GXPATPTR
        ADDD #64
        STD GXPATPTR
        BRA GXPRINTNEXT
GXPRINTDONE EQU *
        JSR GPROW ; Return X and advance one 16-row band, including final band.
        LDX GXBASE
        STX GXWRITE
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
; Borrow only the free interval between upward arrays and downward scalars.
; No heap pointer is advanced: BASIC cannot allocate while this mode owns it.
; Preserve program/variables if the gap suffices. On shortage, invoke the
; actual NEW core once, seal the empty program for retention, and retry.
GXALLOC LDX PEND
        INX
        CPX DFLOOR
        BHI GXNOMEM
        LDX DFLOOR
        CPX #$20C1
        BCS GXNOMEM
        CPX DHEAP
        BHI GXNOMEM
        STX GXBASE
        STX GXWRITE
        LDX DHEAP
        CPX #$3800
        BHI GXNOMEM
        LDAB GXNX
        LDAA #64
        MUL
        ADDD GXBASE
        BCS GXNOMEM
        SUBD DHEAP
        BHI GXRECLAIM
        LDAA #$20
        STAA GPDESC
        CLR GPDESC+1
        RTS
GXRECLAIM TST GXCLEARED
        BNE GXNOMEM
        JSR CLEARALL ; The actual NEW core, including retained-program CRC.
        INC GXCLEARED
        LDAA #$18 ; Host notification: NEW has actually happened, not a request.
        JSR GXTX
        BCS GXNOMEM
        JMP GXALLOC
GXNOMEM LDAA #6
        STAA GPERROR
        JMP GXFAIL
GXIDENT FCC "TPG2 PACK 0248 0256"
        FCB 13,10,0
GXWAITMSG FCC "GFX PRINT - PC / BREAK"
        FCB 0
GXOKMSG FCC "GFX PRINT OK - KEY"
        FCB 0
GXFAILMSG FCC "GFX STOP/ERROR "
        FCB 0
GPAGAINMSG FCC "RESTART FOR NEXT PRINT"
        FCB 0
