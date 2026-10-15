; Numeric DATA/READ/RESTORE, source remains in the existing token records.
; No token ABI change: DATA/READ/RESTORE are currently stored as ASCII.
; Three-byte record headers and REM/string boundaries are never read as data.
; The cursor occupies retired integer-variable slots beyond LPRINT's buffer.
; Heap reset (boot/NEW/RUN/successful edit/LOAD) resets it through $A009.
DANEXT EQU $1948
DASTOP EQU $194A
DAACTIVE EQU $194C
DASIGN EQU $194D
DADST EQU $194E
DASAVE EQU $1950
DATRIAL EQU $1952
DACOPY EQU $1954
DALHS EQU $1956
; Each destination is validated before fetching a value; a successful store
; commits exactly one item. Earlier stores remain on a later READ error.
DAREAD JSR SPACE
        JSR UPPER
        CMPA #65
        BHS DALETTER
        JMP SYNTAX
DALETTER
        CMPA #90
        BHI DASYNTAX
        STAA DALHS
        STX DPTR
        INX
        STX CUR
        JSR SPACE
        CMPA #40
        BEQ DAARRAY
        CLR DADST
        CLR DADST+1
        BRA DATARGETEND
DAARRAY CLR DERR
        JSR ARADDRESS
        LDAA DERR
        BNE DAFAIL
        STX DADST
        LDX DPTR
        STX CUR
DATARGETEND JSR SPACE
        TSTA
        BEQ DAFETCH
        CMPA #44
        BNE DASYNTAX
DAFETCH STX DASAVE
        JSR DAGET
        LDAA DALHS
        STAA DLHS
        LDX DADST
        BEQ DASCALAR
        STX DCOPY
        LDX #DW
        JSR $9E00
        LDX #DW
        LDAB #5
        JSR ARWRITE
        BRA DACOMMITTED
DASCALAR JSR $A00C
DACOMMITTED TSTA
        BNE DAFAIL
        LDX DATRIAL
        STX DANEXT
        LDX DASAVE
        STX CUR
        LDAA ,X
        BEQ DARETURN
        INX ; Destination separator was checked before fetching the value.
        STX CUR
        JMP DAREAD
DARETURN RTS
DAFAIL JMP $A518
DASYNTAX JMP SYNTAX

; Forward-only scanner: each raw statement is visited once between RESTOREs.
; Match uses CUR temporarily; READ keeps its live source pointer in DASAVE.
DAGET LDX DANEXT
        BNE DAKNOWN
        LDX #PROGRAM
        STX DASTOP
DAKNOWN CPX DASTOP
        BHS DARECORD
        TST DAACTIVE
        BEQ DAHEAD
        JSR DAWHITE
        CPX DASTOP
        BHS DARECORD
        CMPA #58
        BEQ DANEXTHEAD
        JMP DAVALUE
DANEXTHEAD
        INX
        BRA DAHEAD
DARECORD CPX PEND
        BHS DAOUT
        CLR DAACTIVE
        LDAB ,X
        CMPB #4
        BLO DARAM
        CMPB #66
        BHI DARAM
        PSHX
        ABX
        CPX PEND
        BHI DABADRECORD
        STX DASTOP
        PULX
        INX
        INX
        INX
DAHEAD CLR DAACTIVE
        JSR DAWHITE
        STX CUR
        LDD DASTOP
        SUBD CUR
        SUBD #4
        BLS DASKIPLINE ; MATCH must not look into the next record header.
        LDX #DANAME
        JSR MATCH
        BCS DASKIP
        LDX CUR
        STX DANEXT
        INC DAACTIVE
        BRA DAKNOWN
DASKIP LDX CUR
        CLRB
DASCAN CPX DASTOP
        BHS DARECORD
        LDAA ,X
        INX
        CMPA #34
        BNE DANOTQUOTE
        COMB
DANOTQUOTE TSTB
        BNE DASCAN
        CMPA #$82 ; REM consumes all remaining bytes, even a quoted colon.
        BEQ DASKIPLINE
        CMPA #58
        BNE DASCAN
        BRA DAHEAD
DASKIPLINE LDX DASTOP
        BRA DARECORD
DABADRECORD PULX
DARAM JMP PRAMERROR
DAOUT LDX #DAOUTMSG
        JMP ERROR

; Copy one bounded, comma/colon-delimited literal into inactive input BUF.
; A NUL is essential: a following record length can itself be ASCII '0'..'9'.
DAVALUE LDD #BUF
        STD DACOPY
DACOPYITEM CPX DASTOP
        BHS DAITEMEND
        LDAA ,X
        CMPA #44
        BEQ DACOMMA
        CMPA #58
        BEQ DAITEMEND
        PSHX
        LDX DACOPY
        STAA ,X
        INX
        STX DACOPY
        PULX
        INX
        BRA DACOPYITEM
DACOMMA INX
        JSR DAWHITE
        CPX DASTOP
        BHS DABADVALUE
        CMPA #58
        BEQ DABADVALUE
        CMPA #44
        BEQ DABADVALUE
DAITEMEND STX DATRIAL
        LDX DACOPY
        CLR ,X
        LDX #BUF
        STX DPTR
        CLR DERR
        CLR DASIGN
        JSR DSPACE
        CMPA #45
        BNE DAPLUS
        LDAA #$80
        STAA DASIGN
        BRA DASIGNED
DAPLUS CMPA #43
        BNE DALITERAL
DASIGNED JSR DADVANCE
        JSR DSPACE
DALITERAL JSR RDLITERAL ; Decimal, %binary or &Hhex only, no evaluation.
        LDAA DERR
        BEQ DACHECKEND
        JMP $A518
DACHECKEND
        JSR DSPACE
        TSTA
        BNE DABADVALUE
        LDAA DW+8
        EORA DASIGN
        STAA DW+8
        RTS
DABADVALUE JMP SYNTAX
DAEND EQU *
