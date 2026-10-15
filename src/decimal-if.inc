; Replace obsolete integer expression module. Decimal EXPR already uses A000.
; Compare aligned decimal digits directly: subtraction could overflow for
; 99999999 versus -99999999. No rounding or conversion to an integer.
CLHS EQU $1ED0
CLSCALE EQU $1ED9
CRSCALE EQU $1EDA
CINDEX EQU $1EDB
CMASK EQU $1EDC
CTRUTH EQU $1EDD
CDIGIT EQU $1EDE
CSIGN EQU $1EDF
        ORG $420C ; Keep console prefix/math ABI jumps at $4206/$4209.
        JMP DECIF
        JMP DCONDITION
DECIF JSR DCONDITION
        STAB CTRUTH
        LDX #KTHEN
        JSR MATCH
        BCC CTHEN
        JMP SYNTAX
CTHEN TST RUNNING
        BNE CIFMODE
        JMP MODEERROR
CIFMODE TST CTRUTH
        BNE CIFDISPATCH
        LDX $1CD5 ; False IF skips the rest of this physical source line.
        STX RNEXT
        RTS
CIFDISPATCH JMP $674C ; Reclaimed legacy integer PEEK; classify THEN body.
CIFTARGET JSR REXPRLINE
        JSR EOS
CIFTAKE
        LDX PEND
        STX $1D40
        LDX #PROGRAM
        JSR $A800
        BCS CIFMISSING
        LDD 1,X
        SUBD $1D42
        BNE CIFMISSING
        STX RNEXT
CIFRETURN RTS
CIFMISSING JMP UNDEFINED
CEVAL LDX CUR
        JSR $A000
        STX CUR
        TSTA
        BEQ CEVALOK
        JMP $A518
CEVALOK RTS
DCONDITION JSR CEVAL
        JSR SPACE
        CMPA #60
        BEQ CLESSOP
        CMPA #62
        BEQ CGREATEROP
        CMPA #61
        BEQ CEQUALOP
; A bare fractional expression has its ordinary nonzero truth value.
        LDX #$1E94
        JSR CANY
        JMP CBOOL
CEQUALOP LDAB #2
        INX
        BRA COPDONE
CLESSOP LDAB #1
        INX
        LDAA ,X
        CMPA #62
        BNE CMAYBEEQUAL
        LDAB #5
        INX
        BRA COPDONE
CGREATEROP LDAB #4
        INX
CMAYBEEQUAL LDAA ,X
        CMPA #61
        BNE COPDONE
        ORAB #2
        INX
COPDONE STAB CMASK
        STX CUR
        LDX #$1E94
        LDAB #9
CCOPY LDAA ,X
        STAA CLHS-$1E94,X
        INX
        DECB
        BNE CCOPY
        JSR CEVAL
; Normalize negative zero before comparing signs.
CCMPVALUE LDX #CLHS
        JSR CANY
        BEQ CLSZERO
        LDAA CLHS+8
        ANDA #$80
CLSZERO STAA CSIGN
        LDX #$1E94
        JSR CANY
        BEQ CRSZERO
        LDAA $1E9C
        ANDA #$80
CRSZERO EORA CSIGN
        BEQ CSAMESIGN
        LDAA CSIGN
        BNE CNEGLESS
        LDAA #4
        BRA CRESULT
CNEGLESS LDAA #1
        BRA CRESULT
CSAMESIGN LDAA CLHS+8
        ANDA #7
        STAA CLSCALE
        LDAA $1E9C
        ANDA #7
        STAA CRSCALE
        CLR CINDEX
; Fixed conceptual grid: eight integer digits followed by seven fraction
; digits. Operand coefficient starts at index=scale; outside it is zero.
CDIGITS LDAA CINDEX
        SUBA CLSCALE
        LDX #CLHS
        JSR CGETDIGIT
        STAA CDIGIT
        LDAA CINDEX
        SUBA CRSCALE
        LDX #$1E94
        JSR CGETDIGIT
        CMPA CDIGIT
        BHI CMAGLESS
        BCS CMAGGREATER
        INC CINDEX
        LDAA CINDEX
        CMPA #15
        BCS CDIGITS
        LDAA #2
        BRA CRESULT
CMAGLESS LDAA #1
        BRA CSIGNED
CMAGGREATER LDAA #4
CSIGNED TST CSIGN
        BEQ CRESULT
        EORA #5 ; Reverse less/greater when both operands are negative.
CRESULT ANDA CMASK
CBOOL TSTA
        BEQ CFALSE
        LDD #1
        RTS
CFALSE CLRA
        CLRB
        RTS
CGETDIGIT CMPA #8 ; Underflow from subtraction is >=128, also rejected.
        BCC CDZERO
        TAB
        ABX
        LDAA ,X
        RTS
CDZERO CLRA
        RTS
CANY LDAB #8
        CLRA
CANYLOOP ORAA ,X
        INX
        DECB
        BNE CANYLOOP
        TSTA
        RTS
