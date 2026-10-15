; 1200/7E1 from original Canon B916/MB906 table (format mask 01).
; TRCSR2: bit2 PEN, bit1 EOP (0=EVEN, 1=ODD), bit0 SBL.
; $04 = even/one stop; $06 was ODD and caused the reported RX timeout.
; Polling only under SEI: no native RX ISR or 1D33 ring buffer.
; Protocol: ACK ready; ASCII numbered lines CR; ACK each line; EOT/ACK end.
SACTIVE EQU $19DC
SLENGTH EQU $19DD
SCHAR EQU $19DE
SREGS EQU $19DF ; 10,1B,1C,1E low control bits,P2 output shadow,11 low control bits
SRXMIN EQU $19E5 ; AND of sampled P23 levels during receive waits (bit 3).
SRXMAX EQU $19E6 ; OR of sampled P23 levels; samples do not decode UART bits.
SERIALINIT CLR SCHAR ; Count received bytes, modulo 256, for timeout diagnosis.
        LDAA #8
        STAA SRXMIN
        CLR SRXMAX
        LDAA $10
        STAA SREGS
        LDAA $1B
        STAA SREGS+1
        LDAA $1C
        STAA SREGS+2
        LDAA $1E
        ANDA #$07
        STAA SREGS+3
        LDAA $69         ; Canon P2 OUTPUT latch shadow, not pin input levels.
        ORAA #$92        ; Canon F377 offline levels, even if shadow was stale.
        STAA SREGS+4
        LDAA $11
        ANDA #$1F
        STAA SREGS+5
        INC SACTIVE
        ; Native B990 offline reset before B916 configuration. Keep SEI:
        ; the Canon RX interrupt handler owns RAM occupied by BASIC.
        CLR $11
        CLR $1E
        CLR $1B
        LDAA #$24
        STAA $10
        LDAA #$19
        STAA $1C
        LDAA #$10
        STAA $1B
        LDAA #$34
        STAA $10
        LDAA #$04
        STAA $1E
        ; Allow the newly selected Timer2 clock to settle before the first frame.
        LDX #$1000
SSETTLE DEX
        BNE SSETTLE
        ; Exact native B952/B954 control value, including RIE. The global I bit
        ; stays SET throughout BASIC: no IRQ handler or Canon ring is used.
        ; RIE should only gate interrupts; this is a controlled comparison,
        ; not a claim that polling requires it.
        LDAA #$1A
        STAA $11
        NOP
        LDAA $1E
        LDAA $12
        ; B8EA asserts online only AFTER enabling and purging the receiver.
        ; P21 is an output from mask-ROM F07F (DDR2=$92); never read DDR2.
        LDAA SREGS+4
        ANDA #$7D
        STAA $69
        STAA $03
        RTS
SERIALCLOSE TST SACTIVE
        BEQ SCLOSED
        CLR $11
        LDAA SREGS
        STAA $10
        LDAA SREGS+1
        STAA $1B
        LDAA SREGS+2
        STAA $1C
        LDAA SREGS+3
        STAA $1E
        LDAA SREGS+4
        ORAA #$92        ; TXD idle high; RTS#/DTR# deasserted outside transfer.
        STAA $69
        STAA $03
        ; Leave TRCSR1 disabled. LOAD/SAVE own SCI only during the transfer;
        ; never revive a stale RE/RIE/TE snapshot after closing or an error.
        CLR SACTIVE
SCLOSED RTS
STXBYTE PSHX
        PSHA
        LDX #$FFFF
STXWAIT LDAA $11
        BITA #$20
        BNE STXREADY
        DEX
        BNE STXWAIT
        JMP STXFAIL
STXREADY PULA
        STAA $13
        PULX
        RTS
SRXBYTE PSHX
        LDX #$FFFF
SRXWAIT LDAA $03
        ANDA #8         ; Observe the MCU's P23 input without external probes.
        PSHA
        ANDA SRXMIN
        STAA SRXMIN
        PULA
        ORAA SRXMAX
        STAA SRXMAX
        LDAA $11
        BITA #$40
        BEQ SRXSECOND
        JMP SRXSTATUS
SRXSECOND EQU *
        ; TRCSR2 bit4 is PER, NOT bit6 (which mirrors ORFE from TRCSR1).
        ; Parity errors leave RDRF=0, ORFE=0: ignoring PER causes a timeout.
        LDAA $1E
        BITA #$10
        BEQ SRXPRIMARY
        JMP SRXSTATUS
SRXPRIMARY EQU *
        LDAA $11
        BITA #$80
        BNE SRXREADY
        PSHX
        JSR KBDSCAN
        PULX
        CMPA #$36
        BNE SRXCONTINUE
        JMP SERIALBREAK
SRXCONTINUE DEX
        BNE SRXWAIT
        BRA SRXTIMEOUT
SRXREADY LDAA $1E
        BITA #$50       ; Recheck ORFE/PER before consuming RDR.
        BNE SRXSTATUS
        LDAA $12
        INC SCHAR
        ANDA #$7F
        PULX
        RTS
STXFAIL LDX #STXMSG
        JMP ERROR
; Snapshot actual control/status BEFORE SERIALCLOSE restores offline values.
; Example: ?RX00 CF4 S3A/2C P00/08. P=min/max of sampled P23, not byte count.
SRXTIMEOUT LDAA $1E
        PSHA
        LDAA $11
        PSHA
        LDAA $10
        PSHA
        JSR SERIALCLOSE
        JSR UICLEAR
        LDX #SRXMSG
        JSR PUTS
        LDAA SCHAR
        JSR SSTATUSHEX
        LDX #SCLOCKMSG
        JSR PUTS
        PULA
        JSR SSTATUSHEX
        LDX #SREGMSG
        JSR PUTS
        PULA
        JSR SSTATUSHEX
        LDAA #47
        JSR PUTC
        PULA
        JSR SSTATUSHEX
        LDX #SPINMSG
        JSR PUTS
        LDAA SRXMIN
        JSR SSTATUSHEX
        LDAA #47
        JSR PUTC
        LDAA SRXMAX
        JSR SSTATUSHEX
        JSR ALERTBEEP
        JMP ERRORKEY
; Capture both status registers BEFORE disabling SCI (reading does not clear
; their RX flags without a subsequent RDR read). Print TRCSR1 then TRCSR2.
SRXSTATUS LDAA $1E
        PSHA
        LDAA $11
        PSHA
        JSR SERIALCLOSE
        JSR UICLEAR
        LDX #SSTATUSMSG
        JSR PUTS
        PULA
        JSR SSTATUSHEX
        LDAA #32
        JSR PUTC
        PULA
        JSR SSTATUSHEX
        JSR ALERTBEEP
        JMP ERRORKEY
SSTATUSHEX PSHA
        LSRA
        LSRA
        LSRA
        LSRA
        JSR HEXDIGIT
        PULA
        ANDA #15
        JMP HEXDIGIT
STXMSG FCC "?TX TIMEOUT"
        FCB 13,10,0
SRXMSG FCC "?RX"
        FCB 0
SCLOCKMSG FCC " C"
        FCB 0
SREGMSG FCC " S"
        FCB 0
SPINMSG FCC " P"
        FCB 0
SSTATUSMSG FCC "?RX STATUS "
        FCB 0
SERIALBREAK JMP BREAK
SERIALFAIL LDX #SFAILMSG
        JMP ERROR
SFAILMSG FCC "?SERIAL"
        FCB 13,10,0
SACK LDAA #6
        JMP STXBYTE
SWAITACK JSR SRXBYTE
        CMPA #6
        BEQ SACKOK
        LDX #SACKMSG
        JMP ERROR
SACKOK RTS
SACKMSG FCC "?BAD ACK"
        FCB 13,10,0
; SAVE waits for PC ACK after each line and final EOT before disabling TX.
SAVECMD JSR DIRECTONLY
        JSR EOS
        JSR SERIALINIT
        JSR SACK
        JSR SWAITACK
        LDAA #1
        STAA LINE
SAVENEXT JSR SLOT
        LDAA ,X
        BEQ SAVESKIP
        PSHX
        LDAB LINE
        LDX #LBUFFER
        JSR $4415
        LDAA #32
        STAA ,X
        INX
        CLR ,X
        LDX #LBUFFER
SAVENUM LDAA ,X
        BEQ SAVENUMDONE
        JSR STXBYTE
        INX
        BRA SAVENUM
SAVENUMDONE EQU *
        PULX
SAVETEXT LDAA ,X
        BEQ SAVEEOL
        JSR STXBYTE
        INX
        BRA SAVETEXT
SAVEEOL LDAA #13
        JSR STXBYTE
        JSR SWAITACK
SAVESKIP INC LINE
        LDAA LINE
        BNE SAVENEXT
        LDAA #4
        JSR STXBYTE
        JSR SWAITACK
        JSR SERIALCLOSE
        LDX #SAVEDMSG
        JMP PUTS
SAVEDMSG FCC "SAVE OK"
        FCB 13,10,0
; LOAD explicitly replaces program. ASCII only; input limit includes number.
; Accepted lines go through NUMBER/CHECKLINE/STORELINE, never EXECUTE.
LOAD    JSR DIRECTONLY
        JSR EOS
        JSR SERIALINIT
        JSR SACK
        JSR SWAITACK
        JSR CLEARALL
        JSR SACK       ; Explicit LOAD-ready reply BEFORE PC starts any text.
LOADLINE CLR SLENGTH
        LDX #BUF
LOADBYTE JSR SRXBYTE
        CMPA #4
        BEQ LOADEND
        CMPA #13
        BEQ LOADSTORE
        CMPA #32
        BCS SERIALFAIL2
        CMPA #126
        BHI SERIALFAIL2
        LDAB SLENGTH
        CMPB #63
        BCC SERIALFAIL2
        STAA ,X
        INX
        INC SLENGTH
        BRA LOADBYTE
LOADSTORE CLR ,X
        LDX #BUF
        STX CUR
        JSR SPACE
        CMPA #48
        BCS SERIALFAIL2
        CMPA #57
        BHI SERIALFAIL2
        JSR NUMBER
        JSR CHECKLINE
        STAB LINE
        JSR SPACE
        JSR STORELINE
        JSR SACK
        BRA LOADLINE
LOADEND TST SLENGTH
        BNE SERIALFAIL2
        JSR $4406     ; Commit once, before acknowledging the complete program.
        JSR SACK
        ; PC must acknowledge the final ACK so its last frame has completed.
        JSR SWAITACK
        JSR SERIALCLOSE
        LDX #LOADEDMSG
        JMP PUTS
SERIALFAIL2 LDX #STEXTMSG
        JMP ERROR
STEXTMSG FCC "?RX TEXT"
        FCB 13,10,0
LOADEDMSG FCC "LOAD OK"
        FCB 13,10,0
