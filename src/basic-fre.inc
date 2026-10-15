; FRE(0): same instantaneous free-byte calculation as MEM.
; No collection, allocation or persistent scratch. Argument must be zero.
        ORG $912A
FRENTRY LDX DPTR
        LDAB #3
        PSHX
        LDX #FRINNAME
        STX DOUT
        PULX
FRCHAR LDAA ,X
        ANDA #$DF
        PSHX
        LDX DOUT
        CMPA ,X
        BNE FRMISS
        INX
        STX DOUT
        PULX
        INX
        DECB
        BNE FRCHAR
        STX DPTR
        JSR DSPACE
        CMPA #40
        BNE FRSYNTAX
        JSR DADVANCE
        JSR DEXPR
        TST DERR
        BNE FRRETURN2
        JSR DSPACE
        CMPA #41
        BNE FRSYNTAX
        JSR DADVANCE
        JSR $A400
        BCS FRARGERR
        SUBD #0
        BNE FRARGERR
        LDD $1EBE ; downward variable heap limit
        SUBD $1EC0 ; DFLOOR includes program sentinel and named arrays
        STD DOUT
        JMP RDVALUE
FRARGERR LDAA #4
        BRA FRERR
FRSYNTAX LDAA #1
FRERR STAA DERR
FRRETURN2 RTS
FRMISS PULX
        JMP SBENTRY
FRINNAME FCC "FRE"
FREEND EQU *
