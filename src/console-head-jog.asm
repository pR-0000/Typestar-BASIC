; Console-only CODE + LEFT/RIGHT MARGIN. One Courier pitch per poll.
; Debounced physical chords $81/$82 enter here; serial input stays on the
; ordinary GETC path. Repeating re-arms only this held key.
; PMMOVE supplies the existing heap, phase-ring and motor cleanup checks.
JGKEY JSR MCFREE
        JSR PMORIGIN
        LDD JGX
        LSRD
        STD PMX
        LDAA KHELD
        CMPA #$81
        BNE JGRIGHT
        LDD PMX
        SUBD #16
        BRA JGTARGET
JGRIGHT LDD PMX
        ADDD #16
JGTARGET SUBD #1152
        BHI JGDONE
        ADDD #1152
        STD PMTX
        LDX #0
        STX PMTY
        JSR LLPMCHECK
JGDONE CLR PMVALID
        CLR KHELD ; Re-arm this chord only; the next scan handles release.
        JMP KBDNONE
JGREADEND EQU *

; @island phase
; Every native X phase, including printing and HEAD, updates this position.
; Boot establishes the initial writing position before MOTORBOOT clears it.
; Count the native first-glyph approach in signed phases, including its
; temporary leftward excursion. The paper axis never changes this counter.
; Eight-entry rings have fixed high byte $6E; only the low byte wraps.
JGPHASE PSHX
        PSHB
        LDAA $41
        BITA #$20
        BNE JGPAPER
        LDX JGX
        BITA #$10
        BEQ JGXPLUS
        DEX
        BRA JGXSTORE
JGXPLUS INX
JGXSTORE STX JGX
        LDX #$4E
        BRA JGRING
JGPAPER LDX #$50
JGRING LDAB 1,X
        BITA #$10
        BEQ JGPLUS
        DECB
        DECB
JGPLUS INCB
        SUBB #$E9
        ANDB #7
        BITA #$20
        BEQ JGHEADBASE
        ADDB #8
JGHEADBASE ADDB #$E9
        STAB 1,X
        SUBB #$E9
        ANDB #7
        BITA #$10
        BEQ JGCARRY
        CLRB
JGCARRY NEGB ; Native forward carry is set except at ring wrap; reverse clears.
        LDX ,X ; Match native STX flags; retain A, B and caller's X.
        PULB
        PULX
        RTS
JGPHASEEND EQU *

; @island boot
MOTORBOOT CLRA
        CLRB
        STD JGX
        STAA PMVALID
        STAA GPRAN
        STAA SACTIVE
        RTS

; @island print
; Check a whole band before its first block: queued native glyphs temporarily
; run behind the logical cursor. GXNX includes repeats and tile/text columns.
; Every block advances 32 phases; no phase or heat is issued on rejection.
JGPRINT TST GXPRINTCOL
        BNE JGPRINTNEXT
        LDAA GXNX
        LDAB #32
        MUL
        ADDD JGX
        SUBD #2304
        BHI JGPRINTBAD
JGPRINTNEXT EQU *
        JMP MOTORPRINT
JGPRINTBAD LDAA #9 ; Distinct from RBJOB's retryable preflight/resource code 6.
        JMP GPABORT

; @island copy
; The four printer/motor workspace copies have identical lifetimes. Share
; this forward copy (X=source, PMPTR=destination, B=220), including restore.
JGCOPY LDAA ,X
        PSHX
        LDX PMPTR
        STAA ,X
        INX
        STX PMPTR
        PULX
        INX
        DECB
        BNE JGCOPY
        RTS
