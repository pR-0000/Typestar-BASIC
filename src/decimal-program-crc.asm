; Prototype retention primitive for a shared program/variable arena.
; CRC-16/CCITT-FALSE over bounded records THROUGH the final zero sentinel.
; No retained pointer is trusted, and no free/variable byte participates.
; Returns C=0, D=CRC, X=sentinel; C=1 for malformed/unterminated records.
; Scratch 1EC6..1EC9 is volatile; never writes program bytes.
; Existing retention signature/boot hooks are NOT changed by this module.
        OPT H01
DCHECK  EQU $1EC6
DLENGTH EQU $1EC8
DBITS   EQU $1EC9
        ORG $A400
PROGRAM_CRC LDD #$FFFF
        STD DCHECK
        LDX #$1B80
PC_RECORD CPX #$1DCA
        BHI PC_BAD
        LDAA ,X
        BEQ PC_LAST
        CMPA #32
        BHI PC_BAD
        JSR PC_BYTE
        LDAA #64
        STAA DLENGTH
PC_TEXT INX
        CPX #$1DCA
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
