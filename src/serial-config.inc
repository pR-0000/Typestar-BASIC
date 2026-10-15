; Shared rate for BASIC transfers, CODE+P and explicit SEROPEN sessions.
; HD6301Y0 handbook section 8.4.1: baud = E / (32*(TCONR+1)).
; E=1 MHz: 25 ->1201.923, 12 ->2403.846, 3 ->7812.5 baud.
; 7812 is the integer PC rate, not a mislabeled 9600 baud.
BAUDCONST EQU $1B8A
        ORG $8F13
; Numeric SERIN(0): nonblocking, -1 means empty, 0..127 is received data.
; No software receive queue: peers must pace data using an application ACK.
SBENTRY LDX DPTR
        LDAB #5
        PSHX
        LDX #SBINNAME
        STX DOUT
        PULX
SBCHAR LDAA ,X
        ANDA #$DF
        PSHX
        LDX DOUT
        CMPA ,X
        BNE SBMISS
        INX
        STX DOUT
        PULX
        INX
        DECB
        BNE SBCHAR
        STX DPTR
        JSR DSPACE
        CMPA #40
        BNE SBSYNTAX
        JSR DADVANCE
        JSR DEXPR
        TST DERR
        BNE SBRETURN2
        JSR DSPACE
        CMPA #41
        BNE SBSYNTAX
        JSR DADVANCE
        JSR $A400
        BCS SBARGERR
        SUBD #0
        BNE SBARGERR
        JSR SBACTIVE
        LDAA $11
        BITA #$40
        BNE SBSTATUS
        LDAA $1E
        BITA #$50
        BNE SBSTATUS
        LDAA $11
        BITA #$80
        BEQ SBEMPTY
        LDAA $1E
        LDAB $12
        ANDB #$7F
        CLRA
        STD DOUT
        JMP RDVALUE
SBEMPTY LDD #1
        STD DOUT
        JSR RDVALUE
        LDAA #$80
        STAA DW+8
SBRETURN2 RTS
SBSTATUS JMP SRXSTATUS
SBARGERR LDAA #4
        BRA SBERR
SBSYNTAX LDAA #1
SBERR STAA DERR
        RTS
SBMISS PULX
        JMP IKENTRY
SBINNAME FCC "SERIN"
SBEND EQU *

        ORG $9000
LXFONT CMPA #32
        BCS LXBAD
        CMPA #65
        BCS LXLOW
        CMPA #90
        BLS LXLETTER
        CMPA #97
        BCS LXMIDDLE
        CMPA #122
        BLS LXLOWER
        CMPA #126
        BHI LXBAD
        SUBA #84
        BRA LXINDEX
LXMIDDLE SUBA #58
        BRA LXINDEX
LXLOW SUBA #32
LXINDEX TAB
        CLRA
        STD TRIFONT
        ASLD
        ASLD
        ASLD
        SUBD TRIFONT
        ADDD #LCDEXTRA
        JMP TRIFONTSET
LXLOWER SUBA #6
LXLETTER JMP TRIUPPER
LXBAD JMP TRINOCHAR

SBBOOT JSR IKBOOT
        LDAA #25
        STAA BAUDCONST
        RTS
; Replace LDAA #25/STAA $1C with a checked load; leave the proven UART
; reset, parity, port latch, settle and shutdown sequences intact.
SBAPPLY LDAA BAUDCONST
        CMPA #12
        BEQ SBAPPLYOK
        CMPA #3
        BEQ SBAPPLYOK
        LDAA #25
SBAPPLYOK STAA $1C
        RTS
SBDISPATCH LDX #SBBAUD
        JSR MATCH
        BCS SBTRYOPEN
        JSR SBINACTIVE
        JSR SBPARSE
        STAA BAUDCONST
        RTS
SBTRYOPEN LDX #SBOPEN
        JSR MATCH
        BCS SBTRYCLOSE
        JSR SBINACTIVE
        JSR SBPARSE
        STAA BAUDCONST
        JMP SERIALINIT
SBTRYCLOSE LDX #SBCLOSE
        JSR MATCH
        BCS SBTRYOUT
        JSR EOS
        TST SACTIVE
        BEQ SBCLOSERET
        JSR SBDRAIN
        JMP SERIALCLOSE
SBCLOSERET RTS
SBTRYOUT LDX #SBOUT
        JSR MATCH
        BCS SBFALLBACK
        JSR SBACTIVE
        JSR EXPR
        TSTA
        BNE SBRANGE
        CMPB #127
        BHI SBRANGE
        PSHB
        JSR EOS
        PULA
        JMP STXBYTE
SBFALLBACK JMP PREVEXEC
SBPARSE JSR EXPR
        PSHB
        PSHA
        JSR EOS
        PULA
        PULB
        SUBD #1200
        BEQ SB1200
        SUBD #1200
        BEQ SB2400
        SUBD #5412
        BNE SBRANGE
        LDAA #3
        RTS
SB2400 LDAA #12
        RTS
SB1200 LDAA #25
        RTS
SBRANGE JMP RANGEERROR
SBINACTIVE TST SACTIVE
        BEQ SBRETURN
SBMODE JMP MODEERROR
SBACTIVE TST SACTIVE
        BEQ SBMODE
SBRETURN RTS
; SERIALINIT rejects nesting so LOAD/SAVE cannot overwrite an open session's
; saved registers. Replay its displaced first instruction, then continue.
SBINIT JSR SBINACTIVE
        CLR SCHAR
        JMP SERIALINIT+3
; TDR-empty does not mean shift-register-empty. At the slowest allowed rate
; one frame takes 8.34 ms. A fixed >16 ms tail is only paid on SERCLOSE.
SBDRAIN LDX #$FFFF
SBDRAINWAIT LDAA $11
        BITA #$20
        BNE SBDRAINTAIL
        DEX
        BNE SBDRAINWAIT
        JMP STXFAIL
SBDRAINTAIL LDX #$1000
SBTAIL DEX
        BNE SBTAIL
        RTS
SBBAUD FCC "BAUD"
        FCB 0
SBOPEN FCC "SEROPEN"
        FCB 0
SBCLOSE FCC "SERCLOSE"
        FCB 0
SBOUT FCC "SEROUT"
        FCB 0

SBMAINEND EQU *
