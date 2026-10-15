; Arithmetic ABI: $4200 expression, $4203 parenthesized atom.
; Operands/operators live on the CPU stack across recursive evaluations.
; Arithmetic scratch uses existing parser words only, never DEST.
        JMP MEXPR
        JMP MGROUP
        JMP IPREFIX ; $4206
        JMP MFUNC ; $4209
MEXPR TSX
        CPX #$1F60
        BHI MEXPRSAFE
        LDX #MDEPTHMSG
        JMP ERROR
MEXPRSAFE JSR MTERM
MELOOP PSHB
        PSHA
        JSR SPACE
        CMPA #43
        BEQ MEOP
        CMPA #45
        BEQ MEOP
        PULA
        PULB
        RTS
MEOP PSHA
        INX
        STX CUR
        JSR MTERM
        STD TEMP
        PULA
        STAA OP
        PULA
        PULB
        PSHA
        LDAA OP
        CMPA #45
        PULA
        BEQ MESUB
        ADDD TEMP
        BRA MELOOP
MESUB SUBD TEMP
        BRA MELOOP
MTERM JSR ATOM
MTLOOP PSHB
        PSHA
        JSR SPACE
        CMPA #42
        BEQ MTOP
        CMPA #47
        BEQ MTOP
        PULA
        PULB
        RTS
MTOP PSHA
        INX
        STX CUR
        JSR ATOM
        STD TEMP
        PULA
        STAA OP
        PULA
        PULB
        STD TOTAL
        LDAA OP
        CMPA #47
        BEQ MTDIV
        JSR MMULT
        BRA MTLOOP
MTDIV JSR MDIV
        BRA MTLOOP
MGROUP LDAA SIGN
        PSHA
        INX
        STX CUR
        JSR MEXPR
        PSHB
        PSHA
        JSR SPACE
        CMPA #41
        BEQ MGCLOSE
        JMP SYNTAX
MGCLOSE INX
        STX CUR
        PULA
        PULB
        STD TEMP
        PULA
        STAA SIGN
        LDD TEMP
        JMP ATOMSIGN
; Low 16 bits of a signed or unsigned product are identical. Fixed 16 steps.
MMULT CLR VALUE
        CLR VALUE+1
        LDAA #16
        STAA COUNT
MMLOOP LSR TEMP
        ROR TEMP+1
        BCC MMSHIFT
        LDD VALUE
        ADDD TOTAL
        STD VALUE
MMSHIFT LDD TOTAL
        ASLD
        STD TOTAL
        DEC COUNT
        BNE MMLOOP
        LDD VALUE
        RTS
; Signed integer division, truncated toward zero. Magnitudes are unsigned
; (including abs(-32768)=32768). Restoring division takes exactly 16 steps.
MDIV LDD TEMP
        BNE MDNONZERO
        LDX #MZEROMSG
        JMP ERROR
MDNONZERO LDAA TOTAL
        EORA TEMP
        ANDA #$80
        STAA OP
        LDD TEMP
        BPL MDPOSRIGHT
        COMA
        COMB
        ADDD #1
        STD TEMP
MDPOSRIGHT LDD TOTAL
        BPL MDPOSLEFT
        COMA
        COMB
        ADDD #1
        STD TOTAL
MDPOSLEFT CLR VALUE
        CLR VALUE+1
        LDAA #16
        STAA COUNT
MDLOOP LDD TOTAL
        ASLD
        STD TOTAL
        ROL VALUE+1
        ROL VALUE
        LDD VALUE
        SUBD TEMP
        BCS MDKEEP
        STD VALUE
        INC TOTAL+1 ; Shift left guarantees low bit zero, so no carry.
MDKEEP DEC COUNT
        BNE MDLOOP
        LDD TOTAL
        TST OP
        BEQ MDRETURN
        COMA
        COMB
        ADDD #1
MDRETURN RTS
MZEROMSG FCC "?DIVISION BY ZERO"
        FCB 13,10,0
MDEPTHMSG FCC "?EXPR DEPTH"
        FCB 13,10,0

        INCLUDE "src/input-prefix.inc"

        INCLUDE "src/basic-math-functions.inc"
