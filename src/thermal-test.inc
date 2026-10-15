; One raw thermal glyph per boot, CODE+P console diagnostic. No serial traffic.
; Foreground timer polling, I=1 throughout. Canon stages execute with a real
; RTI-shaped frame via PRINT_CALL_STAGE, never with unrestricted native IRQs.
; Native timer compare deadlines are used, not artificial software delays.
GPINIT CLR GPRAN
        CLR SACTIVE ; Replaces the first CLR of UIINIT exactly.
        RTS
GPSTART STS GPSP
        CLR $19FB
        LDAA #$0C
        JSR LCDCMD
        JSR UICLEAR
        TST GPRAN
        BEQ GPONCE
        LDX #GPAGAINMSG
        JMP GPRESULT
GPONCE INC GPRAN
        LDX #GPRUNMSG
        JSR PUTS
        CLR GPERROR
        LDAA $08
        ANDA #$1F
        STAA GPSAVED08
        ; Keep the actual phase pointers established by Canon's startup/homing.
        LDX $4E
        CPX #$6EE9
        BCS GPBADSTATE
        CPX #$6EF1
        BCC GPBADSTATE
        LDX $50
        CPX #$6EF1
        BCS GPBADSTATE
        CPX #$6EF9
        BCC GPBADSTATE
        LDD #GXPATTERN
        STD GPPTR
        LDX #GPDATA
        LDAB #64
GPCOPY LDAA 0,X
        PSHX
        LDX GPPTR
        STAA 0,X
        INX
        STX GPPTR
        PULX
        INX
        DECB
        BNE GPCOPY
        BRA GPBEGIN
GPBADSTATE LDAA #4
        JMP GPABORT

; Preserve native head/paper preparation latches; never pretend they are ready.
GPBEGIN LDAA #$0C ; Same output enables as native request entry 70B9.
        STAA $35
        LDAA #4
        STAA $32
        CLR $B7
        LDAA #$42
        STAA $BC
        CLR $BD
        CLRA
        CLRB
        STD $C0
        STD $71
        STD $B8
        STD $BA
        STD $BE
        STAA $40
        STAA $43
        LDD #64
        STD $6F
        LDX #GPDESC
        STX $5E ; Still a descriptor: 7379 will call 75AE exactly once.
        LDX #PRINT_GLYPH_COMPLETE
        STX $45
        LDAA #1
        STAA PRINT_GLYPH_BUSY
        LDD #4096
        STD GPTICKS
        LDX #$728B
        JSR PRINT_CALL_STAGE
GPLOOP JSR PRINT_REPAIR_PAPER_CONTINUATION
        TST PRINT_GLYPH_BUSY
        BEQ GPSUCCESS
        LDX GPTICKS
        DEX
        STX GPTICKS
        BEQ GPTOOMANY
        LDX #$FFFF
GPWAIT LDAA $08
        BITA #$40
        BNE GPTICK
        DEX
        BNE GPWAIT
        LDAA #2
        BRA GPABORT
GPTICK LDX #$77EF
        JSR PRINT_CALL_STAGE
        BRA GPLOOP
GPTOOMANY LDAA #3
        BRA GPABORT
GPSUCCESS JSR GPOFF
        LDX #GPOKMSG
        BRA GPRESULT
GPABORT STAA GPERROR
        SEI
        LDS GPSP ; Discard nested native calls/RTI frame on a bounded wait failure.
        JSR GPOFF
        JSR UICLEAR
        LDX #GPERRMSG
        JSR PUTS
        LDAA GPERROR
        JSR SSTATUSHEX
        LDX #GPSTAGEMSG
        JSR PUTS
        LDAA $44
        JSR SSTATUSHEX
        BRA GPKEY
GPRESULT PSHX
        JSR UICLEAR
        PULX
        JSR PUTS
GPKEY JSR GETC
        TSTA
        BEQ GPKEY
        INC $19FB
        JMP EDRESTORE

; Bounded form of native 7716 ASIC byte transfer, same output writes/order.
GPASIC PSHA
        PSHX
        LDX #$0100 ; Short bound: normal ASIC exchange is only a few cycles.
GPASICWAIT LDAA $34
        BITA #$80
        BEQ GPASICREADY
        DEX
        BNE GPASICWAIT
        LDAA #1
        JMP GPABORT
GPASICREADY PULX
        PULA
        STAA $33
        LDAA $1801
        ORAA #$80
        STAA $34
        RTS
; Native phase waits at 770E and 773E share this bounded helper.
GPPHASEWAIT PSHA
        PSHX
        LDX #$0100 ; Covers the native <=785-tick compare, limits fault heating.
GPPHASELOOP LDAA $0F
        BITA #$20
        BNE GPPHASEDONE
        DEX
        BNE GPPHASELOOP
        LDAA #5
        JMP GPABORT
GPPHASEDONE PULX
        PULA
        RTS

; Immediate output shutdown uses the same safe values as Canon 77B1/74EB.
; No homing or waiting here, so it works even on a stuck peripheral timeout.
GPOFF LDAA $1801
        ANDA #$3F
        STAA $34
        LDAA $0F
        ANDA #$27
        STAA $0F
        LDAA #$0F
        STAA $15
        CLR $17
        CLR $0125
        CLR $0123
        CLR $18F4
        CLR $40
        CLR PRINT_GLYPH_BUSY
        LDAA #4
        STAA $32
        STAA $35
        LDAA GPSAVED08
        ANDA #$F5
        STAA $08
        RTS
GPDESC FCB $20,$00
        FDB GXPATTERN
GPRUNMSG FCC "THERMAL TEST - ONE GLYPH"
        FCB 0
GPOKMSG FCC "THERM OK - KEY"
        FCB 0
GPAGAINMSG FCC "RESTART FOR NEXT PRINT"
        FCB 0
GPERRMSG FCC "THERM ERR "
        FCB 0
GPSTAGEMSG FCC " STAGE "
        FCB 0
        INCLUDE "build/thermal-test/pattern.inc"
THERMAL_TEST_END EQU *
