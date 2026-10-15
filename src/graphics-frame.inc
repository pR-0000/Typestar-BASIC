; TPG1 envelope validation only; no UART, parsing, ACK or mechanical output.
; X -> buffered line WITHOUT LF, B = byte length (6..150).
; Caller guarantees that B bytes are accessible. No input bytes are changed.
; Return C=0 for valid uppercase CRC envelope, C=1 for invalid input.
; A/B/X clobbered. Six bytes of caller-owned scratch, never shared with IRQ:
; GFCRC(2), GFLEFT(1), GFBITS(1), GFVALUE(1), GFHIGH(1).
; No placement here: this module is currently assembled only in the CPU bench.
GRAPHICS_FRAME CMPB #6
        BCS GF_BAD
        CMPB #150
        BHI GF_BAD
        SUBB #5
        STAB GFLEFT
        LDD #$FFFF
        STD GFCRC
GF_BODY LDAA 0,X
        BMI GF_BAD ; TPG1 uses seven-bit ASCII, not parity-bearing bytes.
        CMPA #10
        BEQ GF_BAD
        CMPA #13
        BEQ GF_BAD
        CMPA #$2A
        BEQ GF_BAD ; Exactly one separator, at the expected position.
        EORA GFCRC
        STAA GFCRC
        LDAA #8
        STAA GFBITS
GF_BIT ASL GFCRC+1
        ROL GFCRC
        BCC GF_NEXTBIT
        LDAA GFCRC
        EORA #$10
        STAA GFCRC
        LDAA GFCRC+1
        EORA #$21
        STAA GFCRC+1
GF_NEXTBIT DEC GFBITS
        BNE GF_BIT
        INX
        DEC GFLEFT
        BNE GF_BODY
        LDAA 0,X
        CMPA #$2A
        BNE GF_BAD
        INX
        JSR GF_HEXBYTE
        BCS GF_BAD
        STAA GFHIGH
        JSR GF_HEXBYTE
        BCS GF_BAD
        CMPA GFCRC+1
        BNE GF_BAD
        LDAA GFHIGH
        CMPA GFCRC
        BNE GF_BAD
        CLC
        RTS
GF_BAD SEC
        RTS
; Strict hexadecimal decoding. Carry survives RTS; INX changes only Z.
GF_HEXBYTE JSR GF_NIBBLE
        BCS GF_HEXRET
        ASLA
        ASLA
        ASLA
        ASLA
        STAA GFVALUE
        JSR GF_NIBBLE
        BCS GF_HEXRET
        ORAA GFVALUE
        CLC
GF_HEXRET RTS
GF_NIBBLE LDAA 0,X
        INX
        CMPA #$30
        BCS GF_BAD
        CMPA #$39
        BLS GF_DIGIT
        CMPA #$41
        BCS GF_BAD
        CMPA #$46
        BHI GF_BAD
        SUBA #$37
        CLC
        RTS
GF_DIGIT SUBA #$30
        CLC
        RTS
GRAPHICS_FRAME_END EQU *
