; This replaces BOOT in the LCD-only diagnostic build. Other BASIC code is
; present but unreachable. No program-RAM clearing, SCI setup, matrix scan,
; control34/control3F writes, or Canon interrupt enabling after mask startup.
BOOT    SEI
        LDS #$1FFF
        JSR CONSOLEINIT
        CLR KRAW
        LDX #DIAGMSG
DIAGPRINT LDAA ,X
        BEQ DIAGLOOP
        PSHX
        JSR LCDPUT
        PULX
        INX
        BRA DIAGPRINT
DIAGLOOP LDX #$FFFF
DIAGWAIT DEX
        BNE DIAGWAIT
        INC KRAW
        LDAA KRAW
        ANDA #3
        STAA KRAW
        LDAB KRAW
        LDX #DIAGFRAMES
        ABX
        LDAA ,X
        PSHA
        LDAA #$9F
        JSR LCDCMD
        PULA
        JSR LCDDATA
        BRA DIAGLOOP
DIAGMSG FCC "LCD ONLY 0.2.2"
        FCB 0
DIAGFRAMES FCB $7C,$2F,$2D,$5C
