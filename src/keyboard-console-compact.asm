; Same debounced key events as the previous decoder, with a shared table
; for the eight fixed control keys. CODE shortcuts remain editor-only.
JGKREAD JSR CXSCAN
        STAA KRAW
        CMPA KPREV
        BEQ JGKSTABLE
        STAA KPREV
        BRA JGKNONE
JGKSTABLE CMPA KHELD
        BEQ JGKNONE
        STAA KHELD
        CMPA #$FF
        BEQ JGKNONE
        TST BOOTFLAG
        BEQ JGKREADY
        LDAA #13
        BRA JGKRETURN
JGKREADY CMPA #$3A
        BNE JGKSPECIAL
        LDX #KMODE
        EIM #1,0,X
        JSR LCDMODE
        BRA JGKNONE
JGKSPECIAL TSTA
        BMI JGKSYNTH
        SUBA #$2C
        BCS JGKNORMAL
        CMPA #13
        BHI JGKNONE
        LDX #JGKTABLE
        TAB
        ABX
        LDAA ,X
JGKRETURN JMP KBDRETURN
JGKNORMAL JMP KDENTRY
JGKNONE JMP KBDNONE
JGKSYNTH CMPA #$81
        BCS JGKGRAPHICS
        CMPA #$82
        BHI JGKMASK
        JMP JGKEY
JGKGRAPHICS LDAA #$96
JGKMASK ANDA #$7F
        BRA JGKRETURN
JGKEND EQU *
; @island table
JGKTABLE FCB 32,13,0,8,0,$12,$13,0,0,0,3,0,$14,$15
