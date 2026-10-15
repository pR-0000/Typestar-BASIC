; OFFLINE token-record reader. No native calls, no startup changes.
; A800: seek first record >= target. X=arena, TEND=sentinel address,
;       TTARGET=u16 line. C=0 X=record; C=1 A=0 end, A=1 corruption.
; A803: expand X=payload, B=length into $1C00 (63 chars + NUL).
;       C=0 success, C=1 malformed/oversized; partial buffer on failure.
; Scratch is experimental, not yet allocated in production's RAM map.
TEND EQU $1D40
TTARGET EQU $1D42
TNEXT EQU $1D44
TSOURCE EQU $1D46
TLEFT EQU $1D48
TOUT EQU $1D49
TMODE EQU $1D4A ; 0 code, 1 string, 2 REM tail.
TWLEN EQU $1D4B
TNUMBER EQU $1D4C
TWORDPTR EQU $1D4D
TCOMPARE EQU $1D4F
TCHAR EQU $1D51
TPOS EQU $1D52
TOLD EQU $1D54
TNEW EQU $1D55
TNEWEND EQU $1D56
TMOVSRC EQU $1D58
TMOVDST EQU $1D5A
TMOVLOW EQU $1D5C
        OPT H01
        ORG $A800
        JMP TSEEK
        JMP TEXPAND
        JMP TTOKENIZE ; A806: X=ASCII, B=length, output at $1C00, C=status.
        JMP TSTORE ; A809: edit TTARGET, source X/B; update TEND on success.
TSEEK CPX TEND
        BHI TBAD
        BEQ TATEND
        LDAB ,X
        CMPB #4
        BCS TBAD
        CMPB #66
        BHI TBAD
        PSHX
        ABX ; Record span skips the complete body, including REM, in O(1).
        STX TNEXT
        CPX TEND
        PULX
        BHI TBAD
        LDD 1,X
        BEQ TBAD ; Zero is never a valid BASIC line number.
        SUBD TTARGET ; Unsigned comparison: line numbers may exceed 32767.
        BCC TFOUND
        LDX TNEXT
        BRA TSEEK
TATEND TST ,X
        BNE TBAD
        CLRA
        SEC
        RTS
TFOUND CLRA
        CLC
        RTS
TBAD LDAA #1
        SEC
        RTS
TEXPAND STX TSOURCE
        STAB TLEFT
        CLR TOUT
        CMPB #63
        BHI TBAD
TELOOP TST TLEFT
        BEQ TEDONE
        LDX TSOURCE
        LDAA ,X
        INX
        STX TSOURCE
        DEC TLEFT
        CMPA #128
        BCC TETOKEN
        CMPA #32
        BCS TBAD
        CMPA #126
        BHI TBAD
        JSR TEMIT
        BCS TBAD
        BRA TELOOP
TETOKEN SUBA #128
        CMPA #TOKENCOUNT
        BCC TBAD
        ASLA
        TAB
        LDX #TOKENPTRS
        ABX
        LDX ,X
TEWORD LDAA ,X
        BEQ TELOOP
        JSR TEMIT
        BCS TBAD
        INX
        BRA TEWORD
TEDONE CLRA
        LDX #$1C00
        LDAB TOUT
        ABX
        STAA ,X
        CLC
        RTS
; Preserve the dictionary pointer while writing one expanded character.
TEMIT LDAB TOUT
        CMPB #63
        BCC TEMITBAD
        PSHX
        LDX #$1C00
        ABX
        STAA ,X
        PULX
        INC TOUT
        CLC
        RTS
TEMITBAD SEC
        RTS
; Tokenize at edit/LOAD time. Never tokenize strings, REM text or a prefix
; of an identifier (PRINTABLE must not become PRINT + ABLE). Output cannot
; exceed input length. Spaces are retained so LIST and SAVE stay readable.
TTOKENIZE STX TSOURCE
        STAB TLEFT
        CLR TOUT
        CLR TMODE
        CMPB #63
        BLS TKLOOP
TKBAD JMP TBAD
TKLOOP TST TLEFT
        BNE TKREAD
        JMP TEDONE
TKREAD LDX TSOURCE
        LDAA ,X
        CMPA #32
        BCS TKBAD
        CMPA #126
        BHI TKBAD
        LDAB TMODE
        CMPB #2
        BEQ TKRAW
        CMPA #34
        BNE TKNOTQUOTE
        EORB #1
        STAB TMODE
        BRA TKRAW
TKNOTQUOTE TSTB
        BNE TKRAW
        JSR TKUPPER
        CMPA #65
        BCS TKRAW
        CMPA #90
        BHI TKRAW
        JMP TKWORD
TKRAW JSR TKCOPY
        BCS TKBAD
        BRA TKLOOP
TKCOPY LDX TSOURCE
        LDAA ,X
        INX
        STX TSOURCE
        DEC TLEFT
        JMP TEMIT
TKUPPER CMPA #97
        BCS TKUPRET
        CMPA #122
        BHI TKUPRET
        SUBA #32
TKUPRET RTS
; Determine maximal identifier length, bounded by the caller's input length.
TKWORD CLR TWLEN
        LDAB TLEFT
TKSCAN LDAA ,X
        JSR TKUPPER
        CMPA #65
        BCS TKDIGIT
        CMPA #90
        BLS TKSCANNEXT
TKDIGIT CMPA #36
        BEQ TKSCANNEXT
        CMPA #48
        BCS TKSCANDONE
        CMPA #57
        BHI TKSCANDONE
TKSCANNEXT INC TWLEN
        INX
        DECB
        BNE TKSCAN
TKSCANDONE CLR TNUMBER
TKTRY LDAA TNUMBER
        ASLA
        TAB
        LDX #TOKENPTRS
        ABX
        LDX ,X
        STX TWORDPTR
        LDX TSOURCE
        STX TCOMPARE
        LDAB TWLEN
TKMATCH LDX TCOMPARE
        LDAA ,X
        INX
        STX TCOMPARE
        JSR TKUPPER
        STAA TCHAR
        LDX TWORDPTR
        LDAA ,X
        CMPA TCHAR
        BNE TKMISS
        INX
        STX TWORDPTR
        DECB
        BNE TKMATCH
        TST ,X
        BNE TKMISS
; Matched whole keyword. Emit its stable one-byte id.
        LDAA TNUMBER
        CMPA #2 ; Stable id $82 = REM (asserted by builder).
        BNE TKNORMAL
        LDAA #2
        STAA TMODE
TKNORMAL LDAA TNUMBER
        ADDA #128
        JSR TEMIT
        BCS TKFAIL
        LDAB TWLEN
        LDX TSOURCE
        ABX
        STX TSOURCE
        LDAA TLEFT
        SUBA TWLEN
        STAA TLEFT
        JMP TKLOOP
TKMISS INC TNUMBER
        LDAA TNUMBER
        CMPA #TOKENCOUNT
        BCS TKTRY
TKIDENT JSR TKCOPY
        BCS TKFAIL
        DEC TWLEN
        BNE TKIDENT
        JMP TKLOOP
TKFAIL JMP TBAD
; Sorted insertion/replacement/deletion. An empty input deletes a line.
; Tokenization and capacity checking finish BEFORE the first program write.
; Caller must handle retention invalidation/CRC around mutation when deployed.
; Fixed candidate arena $20C0..$37FF, TEND points at its final zero byte.
; C=1 A=1 invalid input/record, A=2 insufficient room; C=0 success.
TSENDFAIL PULX
TSERROR JMP TBAD
TSTORE LDAA TTARGET
        ORAA TTARGET+1
        BEQ TSERROR
        PSHX
        LDX TEND
        CPX #$20C0
        BCS TSENDFAIL
        CPX #$37FF
        BHI TSENDFAIL
        PULX
        JSR TTOKENIZE
        BCS TSERROR
; The interactive editor treats whitespace-only statements as deletions.
        LDX #$1C00
TSBLANK LDAA ,X
        BEQ TSEMPTY
        CMPA #32
        BNE TSNONEMPTY
        INX
        BRA TSBLANK
TSEMPTY CLR TOUT
TSNONEMPTY
        LDAA TOUT
        BEQ TSNEWSIZE
        ADDA #3
TSNEWSIZE STAA TNEW
        CLR TOLD
        LDX #$20C0
        JSR TSEEK
        BCC TSFOUND
        TSTA
        BNE TSERROR
        BRA TSPOSITION
TSFOUND LDD 1,X
        SUBD TTARGET
        BNE TSPOSITION
        LDAA ,X
        STAA TOLD
TSPOSITION STX TPOS
        CLRA
        LDAB TOLD
        STD TMOVLOW
        LDD TEND
        SUBD TMOVLOW
        STD TNEWEND
        CLRA
        LDAB TNEW
        ADDD TNEWEND
        STD TNEWEND
        SUBD #$37FF
        BHI TSFULL
; Source tail starts just beyond the old record. Include sentinel in moves.
        LDAB TOLD
        ABX
        STX TMOVLOW
        STX TMOVSRC
        LDX TPOS
        LDAB TNEW
        ABX
        STX TMOVDST
        LDAA TNEW
        CMPA TOLD
        BHI TSBACKSET
        BEQ TSWRITE
TSFORWARD LDX TMOVSRC
        LDAA ,X
        INX
        STX TMOVSRC
        LDX TMOVDST
        STAA ,X
        INX
        STX TMOVDST
        LDX TMOVSRC
        CPX TEND
        BLS TSFORWARD
        BRA TSWRITE
TSFULL LDAA #2
        SEC
        RTS
TSBACKSET LDX TEND
        STX TMOVSRC
        LDX TNEWEND
        STX TMOVDST
TSBACKWARD LDX TMOVSRC
        LDAA ,X
        DEX
        STX TMOVSRC
        LDX TMOVDST
        STAA ,X
        DEX
        STX TMOVDST
        LDX TMOVSRC
        CPX TMOVLOW
        BCC TSBACKWARD
TSWRITE LDAA TNEW
        BEQ TSFINISH
        LDX TPOS
        STAA ,X
        LDD TTARGET
        STD 1,X
        LDAB #3
        ABX
        STX TMOVDST
        LDX #$1C00
        STX TMOVSRC
TSBODY LDX TMOVSRC
        LDAA ,X
        INX
        STX TMOVSRC
        LDX TMOVDST
        STAA ,X
        INX
        STX TMOVDST
        DEC TOUT
        BNE TSBODY
TSFINISH LDX TNEWEND
        STX TEND
        CLRA
        CLC
        RTS
; TOKENCOUNT, TOKENPTRS and words are generated from basic_tokens.json.
