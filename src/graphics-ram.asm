; S-70 runtime graphics primitives, HD6301. NOT a complete NH7 firmware.
; Caller owns a 64-byte buffer: 31 printable format-0 columns + one blank guard.
; Paper rows 0..15 run top-to-bottom using the hardware-validated permutation.
; No absolute RAM, bank writes, motor calls or changes to the IRQ mask.
; All entries preserve X and SP; A/B/flags otherwise scratch, C=0 success,
; C=1 invalid coordinates (no buffer/job writes on validation failure).
        OPT H01
        ORG $6000

; X=buffer. Clear all 64 bytes, including the trailing guard.
GFX_CLEAR PSHX
        CLRA
        LDAB #64
GCLOOP  STAA 0,X
        INX
        DECB
        BNE GCLOOP
        PULX
        CLC
        RTS

; X=buffer, A=x (0..30 pattern columns), B=y (0..15 paper rows).
GFX_PSET PSHX
        CMPA #31
        BCC GPOINTBAD
        CMPB #16
        BCC GPOINTBAD
        PSHB
        TAB
        ASLB
        ABX
        PULB
        PSHX
        ASLB
        LDX #GFX_ROW_MASKS
        ABX
        LDD 0,X
        PULX
        ORAA 0,X
        ORAB 1,X
        STD 0,X
        PULX
        CLC
        RTS
GPOINTBAD PULX
        SEC
        RTS

; X=14-byte job, disjoint from buffer:
; +0 buffer pointer (big endian), +2 x0, +3 y0, +4 x1, +5 y1.
; +6..13 scratch CX,CY,DX,DY,SX,SY,ERR,E2. Inputs +0..5 retained.
; Integer Bresenham includes both endpoints; x/y refer to the non-square grid.
GFX_LINE LDAA 2,X
        CMPA #31
        BCC GLBAD
        LDAA 4,X
        CMPA #31
        BCC GLBAD
        LDAA 3,X
        CMPA #16
        BCC GLBAD
        LDAA 5,X
        CMPA #16
        BCC GLBAD
        BRA GLINIT
GLBAD   SEC
        RTS
GLINIT  LDAA 2,X
        STAA 6,X
        LDAA 3,X
        STAA 7,X
        LDAB #1
        LDAA 4,X
        SUBA 2,X
        BPL GLDX
        COMA
        INCA
        LDAB #$FF
GLDX    STAA 8,X
        STAB 10,X
        LDAB #1
        LDAA 5,X
        SUBA 3,X
        BMI GLDYNEG
        COMA
        INCA
        BRA GLDY
GLDYNEG LDAB #$FF
GLDY    STAA 9,X
        STAB 11,X
        ADDA 8,X
        STAA 12,X
GLLOOP  PSHX
        LDAA 6,X
        LDAB 7,X
        LDX 0,X
        JSR GFX_PSET
        PULX
        LDAA 6,X
        CMPA 4,X
        BNE GLSTEP
        LDAA 7,X
        CMPA 5,X
        BEQ GLDONE
GLSTEP  LDAA 12,X
        ASLA
        STAA 13,X
        CMPA 9,X
        BLT GLYSTEP
        LDAA 12,X
        ADDA 9,X
        STAA 12,X
        LDAA 6,X
        ADDA 10,X
        STAA 6,X
GLYSTEP LDAA 13,X
        CMPA 8,X
        BGT GLLOOP
        LDAA 12,X
        ADDA 8,X
        STAA 12,X
        LDAA 7,X
        ADDA 11,X
        STAA 7,X
        BRA GLLOOP
GLDONE  CLC
        RTS

; Format-0 packed masks, not a linear electrical-bit row order.
GFX_ROW_MASKS FDB $1000,$2000,$4000,$8000
        FDB $0001,$0002,$0004,$0008,$0010,$0020,$0040,$0080
        FDB $0100,$0200,$0400,$0800
GFX_END EQU *
