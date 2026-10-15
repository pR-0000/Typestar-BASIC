; Compact program records in bank-zero document RAM.
; Record: line number 1..255, NUL-terminated source. Zero line ends arena.
; PEND points at the final zero; records need not be sorted (RUN/LIST lookup).
PROGRAM EQU $20C0
PROGRAMEND EQU $37FF
PEND EQU $19CE
POLD EQU $19D0
OLDSZ EQU $19D2
NEWSZ EQU $19D4
PSRC EQU $19D6
PDST EQU $19D8
NEND EQU $19DA
; Find LINE. Carry clear: X points to text. Carry set: empty ROM string.
SLOT    LDX #PROGRAM
PFIND   CPX PEND
        BEQ PMISSING
        LDAA ,X
        CMPA LINE
        BEQ PFOUND
        INX
PSKIP   CPX PEND
        BCS PSKIPREAD
        JMP PRAMERROR
PSKIPREAD LDAA ,X
        INX
        TSTA
        BNE PSKIP
        BRA PFIND
PFOUND  PSHX
        INX
PVERIFY CPX PEND
        BCS PVERIFYREAD
        JMP PRAMERROR
PVERIFYREAD LDAA ,X
        INX
        TSTA
        BNE PVERIFY
        PULX
        INX
        CLC
        RTS
PMISSING LDX #PEMPTY
        SEC
        RTS
PEMPTY  FCB 0
CLEARALL JSR $4409
        LDX #PROGRAM
        STX PEND
        CLR ,X
        JSR $4406
        JMP CLEARVARS
; Atomic capacity check before any deletion. CUR points at source in BUF.
STORELINE LDX CUR
        STX PSRC
        LDAA ,X
        BEQ PDELETEONLY
        CLRB
PLENGTH INCB
        LDAA ,X
        INX
        TSTA
        BNE PLENGTH
        INCB            ; Include line-number byte.
        CLRA
        BRA PNEWSIZE
PDELETEONLY CLRA
        CLRB
PNEWSIZE STD NEWSZ
        JSR SLOT
        BCS PNOOLD
        DEX
        STX POLD
        INX
POLDLEN LDAA ,X
        INX
        TSTA
        BNE POLDLEN
        STX OLDSZ
        LDD OLDSZ
        SUBD POLD
        BRA POLDSIZE
PNOOLD  LDX PEND
        STX POLD
        CLRA
        CLRB
POLDSIZE STD OLDSZ
        LDD PEND
        SUBD OLDSZ
        ADDD NEWSZ
        STD NEND
        SUBD #PROGRAMEND
        BLS PCAPOK
        JMP PMEMERROR
PCAPOK  JSR $4409
        LDD POLD
        ADDD OLDSZ
        STD PSRC
        LDX POLD
        STX PDST
; Compact suffix including old sentinel. Writes cannot overwrite unread data.
PMOVE   LDX PSRC
        LDAA ,X
        INX
        STX PSRC
        LDX PDST
        STAA ,X
        CMPA ,X
        BNE PRAMERROR
        INX
        STX PDST
        LDX PSRC
        CPX PEND
        BLS PMOVE
        LDD PEND
        SUBD OLDSZ
        STD PEND
        LDD NEWSZ
        BEQ PSTORED
        LDX PEND
        LDAA LINE
        STAA ,X
        CMPA ,X
        BNE PRAMERROR
        INX
        STX PDST
        LDX CUR
PCOPY   LDAA ,X
        INX
        STX PSRC
        LDX PDST
        STAA ,X
        CMPA ,X
        BNE PRAMERROR
        INX
        STX PDST
        LDX PSRC
        TSTA
        BNE PCOPY
PSTORED LDX NEND
        STX PEND
        CLR ,X
        TST ,X
        BNE PRAMERROR
        ; During LOAD the signature stays invalid until the final CRC.
        TST SACTIVE
        BNE PSTOREEND
        JMP $4406
PSTOREEND RTS
; A failed hardware write invalidates program metadata instead of RUN garbage.
PRAMERROR JSR $4409
        LDX #PROGRAM
        STX PEND
        LDX #PRAMMSG
        JMP ERROR
PMEMERROR LDX #PMEMMSG
        JMP ERROR
PRAMMSG FCC "?PROGRAM RAM"
        FCB 13,10,0
PMEMMSG FCC "?PROGRAM FULL"
        FCB 13,10,0
