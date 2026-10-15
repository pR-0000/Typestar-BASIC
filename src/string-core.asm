; String expressions join atoms with '+'. Output mode: 0 -> inactive BUF,
; 1 -> LCD, 2 -> LPRINT staging buffer, 3 -> length/first-byte only,
; 4 -> private scratch payload at STDEST.
; Counted strings allow CHR$(0); no terminator is written beyond BUF[62].
STEXPR CLR STLEN
STNEXT JSR STPART
STEMIT TSTB
        BEQ STAFTER
        LDAA ,X
        PSHB
        LDAB STLEN
        BNE STNOTFIRST
        STAA STFIRST
STNOTFIRST CMPB #63
        BHS STTOOLONG
        INC STLEN
        LDAB STMODE
        BEQ STBUFFER
        CMPB #1
        BEQ STLCD
        CMPB #2
        BEQ STPAPER
        CMPB #4
        BEQ STBUFFER
        BRA STSKIPBYTE
STPAPER
        JSR LVAPPEND
        BRA STSKIPBYTE
STLCD JSR PUTC
        BRA STSKIPBYTE
STBUFFER PSHX
        LDX #BUF
        TST STMODE
        BEQ STBUFFERREADY
        LDX STDEST
STBUFFERREADY
        LDAB STLEN
        DECB
        ABX
        STAA ,X
        PULX
STSKIPBYTE PULB
        INX
        DECB
        BRA STEMIT
STAFTER JSR DSPACE
        CMPA #43
        BNE STRETURN
        JSR DADVANCE
        BRA STNEXT
STRETURN RTS
STTOOLONG JMP RANGEERROR
; Find a string object by tagged name A|$80. Reuse the named-object scanner
; and its span checks; string/array names occupy disjoint namespaces.
STFIND LDX #DIMJOB
        STAA 29,X
        JSR ARRAY_NAMED_FIND
        BCS STNOTFOUND
        LDX DIMJOB+25
        LDAB #8
        ABX
        CLC
STNOTFOUND RTS
; Allocate on the first nonempty assignment, then reuse 63 characters of
; capacity. No leaks from growing/shrinking strings; no moving array records.
STSTORE LDAA STLHS
        JSR STFIND
        BCC STCOPY
        CMPA #1
        BNE STHEAPBAD
        TST STLEN
        BEQ STSTORED
        LDX #DIMJOB
        LDD #$0101
        STD ,X
        LDD #64
        STD 2,X
        LDD #1
        STD 4,X
        JSR ANRESERVE
        BCS STFULL
        LDAA STLHS
        JSR STFIND
        BCS STHEAPBAD
STCOPY LDAA STLEN
        STAA ,X
        INX
        STX STDEST
        LDX #BUF
        LDAB STLEN
        BEQ STSTORED
STCOPYBYTE LDAA ,X
        PSHX
        LDX STDEST
        STAA ,X
        INX
        STX STDEST
        PULX
        INX
        DECB
        BNE STCOPYBYTE
STSTORED CLRA
        CLR DERR
        LDX DPTR
        RTS
STFULL JMP PMEMERROR
STHEAPBAD JMP PRAMERROR
STCOREEND EQU *
