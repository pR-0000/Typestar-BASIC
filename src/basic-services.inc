; Explicit services; no IRQ or native editor-buffer reuse.
KMEM FCC "MEM"
        FCB 0
KSAVE FCC "SAVE"
        FCB 0
KLOAD FCC "LOAD"
        FCB 0
MEMORY  JSR EOS
        LDD #PROGRAMEND
        SUBD PEND
        JSR OUTNUM
        LDX #MEMTEXT
        JMP PUTS
MEMTEXT FCC " BYTES FREE"
        FCB 13,10,0
; Errors remain visible until Return. SCI errors also shut down transfer first.
ERRORWAIT LDS #$1FFF
        CLR $1974
        CLR $197F
        CLR $19FB
        PSHX
        JSR SERIALCLOSE
        JSR UICLEAR
        PULX
        JSR PUTS
        JSR ALERTBEEP
ERRORKEY JSR GETC
        CMPA #13
        BNE ERRORKEY
        JMP READY
; Known ASIC buzzer gate bit, preserving every other control-shadow bit.
; Brief bounded pulse; modulation is not a hardware frequency selection.
ALERTBEEP LDAA $1801
        ORAA #$40
        STAA $34
        LDX #$6000
ALERTDELAY DEX
        BNE ALERTDELAY
        LDAA $1801
        ANDA #$BF
        STAA $34
        RTS
