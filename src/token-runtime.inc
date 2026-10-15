; OFFLINE runtime bridge, not a released firmware. Production startup unchanged.
; Token records are expanded into $1C00 only for the existing expression parser.
; Sequential RUN uses record spans; it never searches all line numbers.
RECORD EQU $1D60
RNEXT EQU $1D62
RLINE EQU $1D64
RLOW EQU $1D66
RHIGH EQU $1D68
RFMT EQU $1D6A
RFPTR EQU $1D6C
RFDIG EQU $1D6E
RFSTART EQU $1D6F
GCDEPTH EQU $1BB0 ; Caller loop depth for each GOSUB frame.
RCALLS EQU $1BA0 ; Eight token-stream continuations (possibly after a colon).
        ORG NEXTCOMMAND+3
SEGONE
RGCALL JSR RTARGET
        STX RECORD
        LDAB GCOUNT
        CMPB #8
        BCS RGSPACE
        LDX #GDEPTHMSG
        JMP ERROR
RGSPACE LDX #GCDEPTH
        ABX
        LDAA FCOUNT
        STAA ,X
        ASLB
        LDX #RCALLS
        ABX
        LDD RNEXT
        STD ,X
        INC GCOUNT
        LDX RECORD
        STX RNEXT
        RTS
RGRETURN TST RUNNING
        BNE RGRETOK
        JMP MODEERROR
RGRETOK JSR EOS
        LDAB GCOUNT
        BNE RGPOP
        JMP GPAIRERROR
RGPOP DECB
        LDX #GCDEPTH
        ABX
        LDAA FCOUNT
        CMPA ,X
        BEQ RGPOPOK
        JMP FORPAIRERROR
RGPOPOK STAB GCOUNT
        ASLB
        LDX #RCALLS
        ABX
        LDX ,X
        STX RNEXT
        RTS
; LIST start[,end] uses the same unsigned target and sequential record walk.
SEGONEEND EQU *
        ORG $9F60
SEGTWO
RCHECK STD $1D42
        BNE RVALID
        JMP RANGEERROR
RVALID RTS
RSTORE LDX CUR
        CLRB
RSLENGTH LDAA ,X
        BEQ RSREADY
        INX
        INCB
        CMPB #64
        BCS RSLENGTH
        JMP LONGERROR
RSREADY LDX PEND
        STX $1D40
        LDX $19FC
        PSHX ; Failed tokenization/capacity checks must retain old validity.
        LDX CUR
; Never leave a valid signature across a program mutation. TSTORE errors
; precede every write, so only that failure path may restore the signature.
        CLR $19FC
        CLR $19FD
        JSR $A809
        BCC RSOK
        PULX
        STX $19FC
        CMPA #2
        BNE RRAMERROR
        JMP PMEMERROR
RSOK PULX
        LDX $1D40
        STX PEND
        TST SACTIVE
        BNE RSHEAP ; LOAD commits once at EOT, never once per received line.
        JSR $4406 ; New-format validator and CRC, then signature $5424.
        BCS RRAMERROR
RSHEAP JMP $A509 ; Reset decimal heap only after successful edit.
RRAMERROR JMP PRAMERROR
; Validate current record and expand into transient execution/listing buffer.
; Used by LIST/SAVE: expand the whole line, preserving all colons.
; TSTORE builds the sorted arena; startup validates structure and CRC.
REXPAND LDX RECORD
        CPX PEND
        BCC RRAMERROR
        LDAB ,X
        CMPB #4
        BCS RRAMERROR
        CMPB #66
        BHI RRAMERROR
        ABX
        CPX PEND
        BHI RRAMERROR
        STX RNEXT
        LDX RECORD
        LDD 1,X
        STD RLINE
        LDAB ,X
        SUBB #3
        INX
        INX
        INX
        JSR $A803
        BCS RRAMERROR
        LDX #$1C00
        STX CUR
        RTS
SEGTWOEND EQU *
        ORG $A330
SEGTHREE
RLIST JSR DIRECTONLY
        LDD #1
        STD RLOW
        LDD #$FFFF
        STD RHIGH
        JSR SPACE
        TSTA
        BEQ RLREADY
        JSR REXPRLINE
        STD RLOW
        STD RHIGH
        JSR SPACE
        CMPA #44
        BNE RLEOS
        INX
        STX CUR
        JSR REXPRLINE
        STD RHIGH
RLEOS JSR EOS
RLREADY LDD RHIGH
        SUBD RLOW
        BCC RLRANGE
        JMP RANGEERROR
RLRANGE LDD RLOW
        STD $1D42
        LDX PEND
        STX $1D40
        LDX #PROGRAM
        JSR $A800
        BCC RLFOUND
        TSTA
        BNE RLBAD
        JMP RLEND
RLBAD JMP RRAMERROR
RLFOUND STX RECORD
RLLOOP LDX RECORD
        CPX PEND
        BCC RLEND
        LDD RHIGH
        SUBD 1,X
        BCS RLEND
        JSR REXPAND
        LDD RLINE
        JSR RFORMAT
        LDAA #32
        STAA ,X
        INX
        STX RFPTR
        LDX #$1C00
RLCOPY LDAA ,X
        PSHX
        LDX RFPTR
        STAA ,X
        INX
        STX RFPTR
        PULX
        INX
        TSTA
        BNE RLCOPY
        LDAA RFPTR+1
        SUBA #$80 ; LBUFFER now starts at $1D80, not $1B00.
        DECA
        STAA LLEN ; Expanded listing length <=69 fits one byte.
        CLR LWIN
        JSR LISTSHOW
RLWAIT JMP LISTWAIT ; Reuse the established Return/arrows/BREAK loop.
RLACK JSR HISTSAVE
        LDX RNEXT
        STX RECORD
        JMP RLLOOP
RLEND INC UIPENDING
        RTS
SEGTHREEEND EQU *
        ORG $A480
SEGFOUR
RRUN JSR DIRECTONLY
        JSR EOS
        JSR CLEARVARS
        CLR $1CD3 ; Statement record cache is invalid after every edit/RUN.
        CLR $1CD4
        LDX #PROGRAM
        STX RNEXT
        LDAA #1
        STAA RUNNING
RRLOOP LDX RNEXT
        CPX PEND
        BCC RRFINISH
        STX RECORD
        JSR KBDFAST
        CMPA #3
        BNE RRGO
        JMP BREAK
RRGO LDX RECORD
RREXEC JSR $574C ; Expand only the next colon-delimited statement.
        JSR EXECUTE
        TST RUNNING
        BNE RRLOOP
RRFINISH CLR RUNNING
        TST GCOUNT
        BEQ RRRETURN
        JMP GPAIRERROR
RRRETURN TST FCOUNT
        BEQ RRDONE
        JMP FORPAIRERROR
RRDONE RTS
RRERROR JMP RRAMERROR
; Shared target parsing checks exact integer conversion (EXPR bridge),
; nonzero 16-bit range, direct/program mode, and exact target existence.
SEGFOUREND EQU *
        ORG $A780
SEGFIVE
REXPRLINE JSR EXPR
; The integer bridge also accepts signed words for PEEK/POKE. A negative
; target must not be reinterpreted as a high unsigned line (e.g. -1=65535).
        TST $1E9C
        BPL REXPRPOS
        JMP RANGEERROR
REXPRPOS JMP RCHECK
RTARGET JSR REXPRLINE
        STD RLOW
        JSR EOS
        TST RUNNING
        BNE RTMODE
        JMP MODEERROR
RTMODE LDD RLOW
        JSR RCHECK
        LDX PEND
        STX $1D40
        LDX #PROGRAM
        JSR $A800
        BCS RTMISSING
        LDD 1,X
        SUBD RLOW
        BNE RTMISSING
        RTS
RTMISSING JMP UNDEFINED
RGOTO JSR RTARGET
        STX RNEXT
        RTS
SEGFIVEEND EQU *
