; Build one complete ASCII output before invoking the existing glyph cache.
; BUF is inactive during EXECUTE: direct commands were copied to $1D00,
; tokenized statements expand to $1C00. The final eight bytes occupy the
; retired integer A..D slots; decimal scalars now live in the dynamic heap.
; Keep runtime continuations $1D60..$1D6F and both source buffers untouched.
; Native math and printer workspaces are disjoint from this 72-byte buffer.
LVBUFFER EQU $1900
LVPARSE JSR MCFREE
        CLR LPREMAIN
        CLR LPSUPPRESS
        JSR SPACE
        TSTA
        BEQ LVDONE
        CMPA #58
        BEQ LVDONE
LVITEM CMPA #34
        BNE LVNUMBER
        INX
LVSTRING LDAA ,X
        INX
        CMPA #34
        BEQ LVQUOTED
        TSTA
        BNE LVCHAR
        JMP SYNTAX
LVCHAR JSR LVAPPEND
        BRA LVSTRING
LVQUOTED STX CUR
        BRA LVSEPARATOR
LVNUMBER LDX CUR
        JSR $A000 ; Decimal expression -> DW; X -> first unconsumed byte.
        STX CUR
        TSTA
        BEQ LVFORMAT
        JMP $A518 ; Common decimal error translation, no paper motion yet.
LVFORMAT JSR $A003 ; Canon decimal formatting -> NUL-terminated DTEXT.
LVNUMCOPY LDAA ,X
        BEQ LVSEPARATOR
        INX
        JSR LVAPPEND
        BRA LVNUMCOPY
LVSEPARATOR JSR SPACE
        CMPA #59
        BEQ LVCONTINUE
        CMPA #44
        BNE LVDONE
        ; Same compact comma convention as LCD PRINT: one space, no zones.
        LDAA #32
        JSR LVAPPEND
LVCONTINUE INX
        STX CUR
        JSR SPACE
        TSTA
        BEQ LVTRAILING
        CMPA #58
        BNE LVITEM
LVTRAILING INC LPSUPPRESS
LVDONE JSR EOS
        LDX #LVBUFFER
        STX LPREAD
        LDAA PMVALID
        CMPA #3
        BEQ LVWIDTH
        CLR LPCOLUMN
LVWIDTH JMP LPCHECKWIDTH ; Existing width preflight, then one cached job.
; Preserve source X and A. Never store a 73rd byte, including separators.
LVAPPEND CMPA #32
        BLO LVRANGE
        CMPA #126
        BHI LVRANGE
        LDAB LPREMAIN
        CMPB #72
        BHS LVRANGE
        PSHX
        LDX #LVBUFFER
        ABX
        STAA ,X
        PULX
        INC LPREMAIN
        RTS
LVRANGE JMP RANGEERROR
; The output may grow beyond the 63-byte source (decimal formatting).
; Keep the key dictionary within its 64-byte serial pattern buffer. With
; 64 keys present, a missing key is deferred to the existing last-slot cache
; replacement path. Returning B=0 makes the old builder skip the insertion.
LVLOOKUP JSR LPLOOKUP
        CMPB #64
        BLO LVLOOKDONE
        CLRB
LVLOOKDONE RTS
LVEND EQU *
