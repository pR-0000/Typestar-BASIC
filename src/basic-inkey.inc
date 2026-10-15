; Nonblocking numeric keyboard API. One pending translated event, first wins.
; Keep BREAK visible to the caller even when an earlier character is pending.
; This byte is outside retention scratch ($1B80..89) and graphics ($1B91..).
IKPENDING EQU $1B90
        ORG $8E7B
IKBOOT JSR GPINIT
        CLR IKPENDING
        RTS
IKRUN CLR IKPENDING
        JMP CLEARVARS
IKPOLL JSR KBDFAST
        TSTA
        BEQ IKRETURN
        CMPA #3
        BEQ IKRETURN
        TST IKPENDING
        BNE IKRETURN
        STAA IKPENDING
IKRETURN RTS
; Preserve the existing five-function parser and all variable/array names.
; Only INKEY is intercepted; spelling is case insensitive.
IKENTRY LDX DPTR
        LDAB #5
        PSHX
        LDX #IKNAME
        STX DOUT
        PULX
IKCHAR LDAA ,X
        ANDA #$DF
        PSHX
        LDX DOUT
        CMPA ,X
        BNE IKMISS
        INX
        STX DOUT
        PULX
        INX
        DECB
        BNE IKCHAR
        STX DPTR
        JSR DSPACE
        CMPA #40
        BNE IKSYNTAX
        JSR DADVANCE
        JSR DEXPR
        TST DERR
        BNE IKRETURN
        JSR DSPACE
        CMPA #41
        BNE IKSYNTAX
        JSR DADVANCE
        JSR $A400
        BCS IKRANGE
        SUBD #0
        BNE IKRANGE
        JSR IKPOLL
        CMPA #3
        BNE IKVALUE
        JMP BREAK
IKVALUE LDAB IKPENDING
        CLR IKPENDING
        CLRA
        STD DOUT
        JMP RDVALUE
IKRANGE LDAA #4
        BRA IKERROR
IKSYNTAX LDAA #1
IKERROR STAA DERR
        RTS
IKMISS PULX
        LDX #FNAMES
        JMP FNENTRY+3
IKNAME FCC "INKEY"
IKEND EQU *
