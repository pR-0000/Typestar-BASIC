; Bank-zero program retention. ABI entries stay fixed for main/module calls.
        JMP RETPREP
        JMP RETRESTORE
        JMP RETCOMMIT
        JMP RETINVALID
        JMP FORDISPATCH
        JMP FORFINISH
        JMP IDISPATCH
        JMP FORMATLINE ; $4415: B=line number, X=destination, returns X=end
        JMP RUNFIND ; $4418: next occupied program line
RETMAGIC EQU $19FC
RETCRC EQU $19FE
RETFLAG EQU $1B00
RETFIRST EQU $1B01 ; Original first program byte, hidden during native startup.
RETEXPECT EQU $1B02
DCHECK EQU $1B04
DLENGTH EQU $1B06
DBITS EQU $1B08
; Signature changes because the program moved. Old programs must be SAVE/LOAD
; migrated; never guess old RAM contents are valid new-format records.
RETINVALID CLR RETMAGIC
        CLR RETMAGIC+1
        RTS
RETCOMMIT JSR RETINVALID
        JSR RETCRC16
        BCS RETCOMMITEND
        STD RETCRC
        LDX #$5423
        STX RETMAGIC
RETCOMMITEND RTS
; F066 does not guarantee bank zero on a warm reset. Select it before CRC.
; The program no longer overlaps Canon work RAM, so no boot shadow is needed.
RETPREP SEI
        LDS #$1FFF ; Same explicit empty stack as the validated recovery entry.
; Keep the native B990 call at $6806. The early-call variant in 0.4.32
; regressed on hardware; its electrical/timing cause is not yet established.
        CLR $36
; Entered by JMP from the reset chain, with interrupts masked and no return
; frame. Clean retained Canon/BASIC work state BEFORE native startup enables
; interrupts for carriage homing. Preserve only the four retention metadata
; bytes and the independent document program arena. F066 has initialized
; hardware shadows 1800..1802: leave them intact. No JSR while clearing stack.
        LDX #$1803
RETCLEANLOW CLR ,X
        INX
        CPX #RETMAGIC
        BNE RETCLEANLOW
        LDX #$1A00
RETCLEANHIGH CLR ,X
        INX
        CPX #$2000
        BNE RETCLEANHIGH
        CLR RETFLAG
        LDX RETMAGIC
        CPX #$5423
        BNE RETNATIVE
; Snapshot only; do not traverse program RAM before native hardware startup.
; RETFLAG means candidate, NOT CRC-validated. Validation occurs at $4403.
        LDAA PROGRAM
        STAA RETFIRST
        LDD RETCRC
        STD RETEXPECT
        LDAA #$C7
        STAA RETFLAG
; Present the same empty first record as the validated recovery image while
; Canon initializes hardware. Save only a possible first byte above: all other
; program bytes stay in place. Do not scan/clear the 6 KiB arena here.
; A native nested reset can reject the candidate; never auto-run its contents.
RETNATIVE CLR PROGRAM
        LDX #$2000
RETHEADER CLR ,X
        INX
        CPX #PROGRAM
        BNE RETHEADER
RETWORKREADY CLR $1C25
        CLR $1F52
        LDAA #4
        STAA $35
        STAA $32
        JMP $6806
RETRESTORE CLR $36
        LDAA RETFLAG
        CMPA #$C7
        BNE RETEMPTY
        LDAA RETFIRST
        STAA PROGRAM
        JSR RETCRC16
        BCS RETEMPTY
        SUBD RETEXPECT
        BNE RETEMPTY
        STX PEND
        BRA RETREADY
RETEMPTY LDX #PROGRAM
        STX PEND
        CLR ,X
RETREADY CLR RETFLAG
        JMP RETCOMMIT
RETCRC16 LDD #$FFFF
        STD DCHECK
        LDX #PROGRAM
PC_RECORD CPX #PROGRAMEND
        BHI PC_BAD
        LDAA ,X
        BEQ PC_LAST
        JSR PC_BYTE
        LDAA #64
        STAA DLENGTH
PC_TEXT INX
        CPX #PROGRAMEND
        BCC PC_BAD
        LDAA ,X
        BEQ PC_EOL
        CMPA #32
        BCS PC_BAD
        CMPA #126
        BHI PC_BAD
        JSR PC_BYTE
        DEC DLENGTH
        BNE PC_TEXT
        BRA PC_BAD
PC_EOL  JSR PC_BYTE
        INX
        BRA PC_RECORD
PC_LAST JSR PC_BYTE
        LDD DCHECK
        CLC
        RTS
PC_BAD  SEC
        RTS
PC_BYTE EORA DCHECK
        LDAB DCHECK+1
        PSHA
        LDAA #8
        STAA DBITS
        PULA
PC_BIT  ASLD
        BCC PC_NEXT
        EORA #$10
        EORB #$21
PC_NEXT DEC DBITS
        BNE PC_BIT
        STD DCHECK
        RTS

; Decimal line-number rendering shared by LIST and SAVE (1..255).
; No NUL/space appended: caller chooses LCD staging or serial framing.
FORMATLINE CLR TEMP
        CLRA
FMTHUND CMPB #100
        BCS FMTHDONE
        SUBB #100
        INCA
        BRA FMTHUND
FMTHDONE TSTA
        BEQ FMTTINIT
        ADDA #48
        STAA ,X
        INX
        INC TEMP
FMTTINIT CLRA
FMTTENS CMPB #10
        BCS FMTTDONE
        SUBB #10
        INCA
        BRA FMTTENS
FMTTDONE TSTA
        BNE FMTTWRITE
        TST TEMP
        BEQ FMTUNITS
FMTTWRITE ADDA #48
        STAA ,X
        INX
FMTUNITS ADDB #48
        STAB ,X
        INX
        RTS

        INCLUDE "src/basic-for.inc"

        INCLUDE "src/basic-input.inc"

; Next occupied line >= LINE, even when edits have changed physical order.
; B holds the smallest candidate number, VALUE its record pointer. Exact
; matches return immediately. No match ends RUN without scanning 255 slots.
RUNFIND LDX #PROGRAM
        CLRB
RFINDLOOP CPX PEND
        BEQ RFINDEND
        LDAA ,X
        CMPA LINE
        BCS RFINDNEXT
        BEQ RFINDEXACT
        TSTB
        BEQ RFINDSAVE
        CBA
        BCC RFINDNEXT
RFINDSAVE TAB
        STX VALUE
RFINDNEXT INX
RFINDSKIP LDAA ,X
        INX
        TSTA
        BNE RFINDSKIP
        BRA RFINDLOOP
RFINDEND TSTB
        BEQ RFINDNONE
        STAB LINE
        LDX VALUE
        INX
        CLC
        RTS
RFINDEXACT INX
        CLC
        RTS
RFINDNONE SEC
        RTS
