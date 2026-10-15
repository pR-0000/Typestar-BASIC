; Original standalone console drivers; ROM-derived register/protocol evidence
; is documented in docs/console.md. All addresses below are owned by BASIC.
UIPENDING EQU $19CA ; Deferred newline for Canon UI; unused by legacy console
LCDPOS  EQU $1996
LCDOK   EQU $1997
KPREV   EQU $1998
KHELD   EQU $1999
KRAW    EQU $199A
KBASE   EQU $199B
KROW    EQU $199C
KLOCALE EQU $199D
KDIAGLAST EQU $199E
LCDBUF  EQU $19A0
; Provisional physical legends; raw command paths are established in NH7.
KENTER  EQU $2D
KERASE  EQU $2F
KBREAK  EQU $3C

CONSOLEINIT CLR LCDPOS
        CLR LCDOK
        LDAA #$FF
        STAA KPREV
        STAA KHELD
        LDAA $3C
        ANDA #15
        CMPA #10
        BCS LOCALEOK
        CLRA
LOCALEOK STAA KLOCALE
        LDX #LCDBUF
        LDAA #32
LCDZERO STAA ,X
        INX
        CPX #LCDBUF+32
        BNE LCDZERO
        ; Long initial wait, then 8-bit function writes as in Canon DE07.
        JSR LCDDELAY
        LDAA #$30
        STAA $38
        JSR LCDDELAY
        STAA $38
        JSR LCDDELAY
        STAA $38
        JSR LCDDELAY
        STAA $38
        JSR LCDDELAY
        INC LCDOK
        LDAA #$08
        JSR LCDCMD
        LDAA #$01
        JSR LCDCMD
        JSR LCDDELAY
        LDAA #$06
        JSR LCDCMD
        LDAA #$38
        JSR LCDCMD
        LDAA #$0C
        JSR LCDCMD
        RTS
LCDDELAY PSHX
        LDX #$4000
LCDDELAY1 DEX
        BNE LCDDELAY1
        PULX
        RTS
; Bounded busy wait. A/B/X preserved. LCDOK is sticky-failed until reset.
LCDWAIT PSHA
        PSHX
        LDX #$1000
LCDWAIT1 LDAA $38
        BITA #$80
        BEQ LCDWAITEND
        DEX
        BNE LCDWAIT1
        CLR LCDOK
LCDWAITEND PULX
        PULA
        RTS
LCDCMD  TST LCDOK
        BEQ LCDCMDEND
        JSR LCDWAIT
        TST LCDOK
        BEQ LCDCMDEND
        STAA $38
LCDCMDEND RTS
LCDDATA TST LCDOK
        BEQ LCDDATAEND
        JSR LCDWAIT
        TST LCDOK
        BEQ LCDDATAEND
        STAA $39
LCDDATAEND RTS
; Rolling 32-character ASCII window. CR becomes a separator, LF ignored.
; A/B/X saved by PUTC. Destructive BS is completed by READLINE's BS-space-BS.
LCDPUT  CMPA #10
        BEQ LCDPUTEND
        CMPA #13
        BNE LCDNOTCR
        LDAA #32
LCDNOTCR CMPA #8
        BNE LCDPRINTABLE
        TST LCDPOS
        BEQ LCDPUTEND
        DEC LCDPOS
        RTS
LCDPRINTABLE CMPA #32
        BCS LCDPUTEND
        CMPA #126
        BHI LCDPUTEND
        PSHA
        LDAA LCDPOS
        CMPA #32
        BCS LCDPLACE
        LDX #LCDBUF
LCDSCROLL LDAA 1,X
        STAA ,X
        INX
        CPX #LCDBUF+31
        BNE LCDSCROLL
        DEC LCDPOS
LCDPLACE LDAB LCDPOS
        LDX #LCDBUF
        ABX
        PULA
        STAA ,X
        INC LCDPOS
LCDREDRAW LDAA #$80
        JSR LCDCMD
        LDX #LCDBUF
LCDREFRESH LDAA ,X
        JSR LCDDATA
        INX
        CPX #LCDBUF+32
        BNE LCDREFRESH
LCDPUTEND RTS

; One active-low scan. A=raw position 0..63 or FF. Selectors run 7F..FE.
; First pressed position wins; no rollover/chord guarantees in this prototype.
KBDSCAN LDAA #56
        STAA KBASE
        LDAA #$7F
        STAA KROW
KSCANROW STAA $31
        LDAA $30
        ORAA $30
        CMPA #$FF
        BNE KSCANBITS
        LDAA KBASE
        BEQ KSCANNONE
        SUBA #8
        STAA KBASE
        LDAA KROW
        LSRA
        ORAA #$80
        STAA KROW
        BRA KSCANROW
KSCANBITS LDAB KBASE
KSCANBIT LSRA
        BCC KSCANFOUND
        INCB
        BRA KSCANBIT
KSCANFOUND TBA
        ; Canon performs the ninth selector write FF after sampling FE.
        ; Early returns must also release all rows, not latch a row active.
        PSHA
        LDAA #$FF
        STAA $31
        PULA
        RTS
KSCANNONE LDAA #$FF
        STAA $31
        RTS

; Two matching scans (including release), with a fixed delay between calls.
; No auto-repeat. Modifier bit sampled only after a new stable raw key.
KBDPOLL PSHB
        PSHX
        LDX #$0800
KBDDELAY DEX
        BNE KBDDELAY
; Fast entry: caller supplies spacing between samples (sound periods).
; Both entries save B/X; fast entry must do so independently.
        BRA KBDREAD
KBDFAST PSHB
        PSHX
KBDREAD JSR KBDSCAN
        STAA KRAW
        CMPA KPREV
        BEQ KBDSTABLE
        STAA KPREV
        BRA KBDNONE
KBDSTABLE CMPA KHELD
        BEQ KBDNONE
        STAA KHELD
        CMPA #$FF
        BEQ KBDNONE
        CMPA #KENTER
        BNE KBDNOTENTER
        LDAA #13
        BRA KBDRETURN
KBDNOTENTER CMPA #KERASE
        BNE KBDNOTERASE
        LDAA #8
        BRA KBDRETURN
KBDNOTERASE CMPA #KBREAK
        BNE KBDNOTBREAK
        LDAA #3
        BRA KBDRETURN
KBDNOTBREAK CMPA #$2C
        BNE KBDCHAR
        LDAA #32
        BRA KBDRETURN
KBDCHAR CMPA #44
        BCC KBDNONE
        LDAB KLOCALE
        ASLB
        LDX #KEYTABLES
        ABX
        LDX ,X
        LDAB KRAW
        ABX
        LDAA $32
        BITA #$80
        BEQ KBDLOOKUP
        LDAB #44
        ABX
KBDLOOKUP LDAA ,X
        BRA KBDRETURN
KBDNONE CLRA
KBDRETURN PULX
        PULB
        RTS

; Calibration console: stable raw positions in hex, before ASCII mapping.
; Exit with serial Ctrl-C/ESC, or the provisional raw break position.
KKEYS   FCC "KEYS"
        FCB 0
KEYDIAG JSR DIRECTONLY
        JSR EOS
        LDAA #$FF
        STAA KDIAGLAST
KEYDIAGLOOP LDAA $11
        BITA #$80
        BEQ KEYDIAGSCAN
        LDAA $1E
        LDAA $12
        CMPA #3
        BEQ KEYDIAGEND
        CMPA #27
        BEQ KEYDIAGEND
KEYDIAGSCAN JSR KBDPOLL
        LDAA KHELD
        CMPA KDIAGLAST
        BEQ KEYDIAGLOOP
        STAA KDIAGLAST
        CMPA #$FF
        BEQ KEYDIAGLOOP
        CMPA #KBREAK
        BEQ KEYDIAGEND
        PSHA
        LSRA
        LSRA
        LSRA
        LSRA
        JSR HEXDIGIT
        PULA
        ANDA #15
        JSR HEXDIGIT
        LDAA #32
        JSR PUTC
        BRA KEYDIAGLOOP
KEYDIAGEND JMP CRLF
HEXDIGIT CMPA #10
        BCS HEXNUMBER
        ADDA #7
HEXNUMBER ADDA #48
        JMP PUTC
