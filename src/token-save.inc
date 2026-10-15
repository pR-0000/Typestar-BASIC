        ORG SAVECMD
; Keep the established serial handshake/UART routines unchanged. Only replace
; traversal and line formatting: text remains portable on the PC.
RSAVE JSR DIRECTONLY
        JSR EOS
        JSR SERIALINIT
        JSR SACK
        JSR SWAITACK
        LDX #PROGRAM
        STX RECORD
RSVNEXT LDX RECORD
        CPX PEND
        BCC RSVEND
        JSR REXPAND
        LDD RLINE
        JSR RFORMAT
        LDAA #32
        STAA ,X
        INX
        CLR ,X
        LDX #LBUFFER
        JSR RSVTEXT
        LDX #$1C00
        JSR RSVTEXT
        LDAA #13
        JSR STXBYTE
        JSR SWAITACK
        LDX RNEXT
        STX RECORD
        BRA RSVNEXT
RSVEND LDAA #4
        JSR STXBYTE
        JSR SWAITACK
        JSR SERIALCLOSE
        LDX #SAVEDMSG
        JMP PUTS
RSVTEXT LDAA ,X
        BEQ RSVRET
        JSR STXBYTE
        INX
        BRA RSVTEXT
RSVRET RTS
