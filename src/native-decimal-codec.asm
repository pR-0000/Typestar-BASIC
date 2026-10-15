; Offline decimal storage codec. Fixed ABI: base=PACK, base+3=UNPACK.
; X -> writable 9-byte buffer. X preserved, A/flags volatile, B preserved.
; PACK: native unpacked digits[8], flags -> BCD[4], flags in first 5 bytes.
; UNPACK: first 5 bytes -> 9-byte native form; process backward for overlap.
; Precondition: digits 0..9 and valid sign/scale; no validation or rounding.
; Packing does not truncate decimals: this is only a storage representation.
        OPT H01
        ORG $9E00
        JMP PACK_DECIMAL
        JMP UNPACK_DECIMAL
PACK_DECIMAL
        LDAA 0,X
        ASLA
        ASLA
        ASLA
        ASLA
        ORAA 1,X
        STAA 0,X
        LDAA 2,X
        ASLA
        ASLA
        ASLA
        ASLA
        ORAA 3,X
        STAA 1,X
        LDAA 4,X
        ASLA
        ASLA
        ASLA
        ASLA
        ORAA 5,X
        STAA 2,X
        LDAA 6,X
        ASLA
        ASLA
        ASLA
        ASLA
        ORAA 7,X
        STAA 3,X
        LDAA 8,X
        STAA 4,X
        RTS
UNPACK_DECIMAL LDAA 4,X
        PSHA
        LDAA 3,X
        PSHA
        ANDA #15
        STAA 7,X
        PULA
        LSRA
        LSRA
        LSRA
        LSRA
        STAA 6,X
        LDAA 2,X
        PSHA
        ANDA #15
        STAA 5,X
        PULA
        LSRA
        LSRA
        LSRA
        LSRA
        STAA 4,X
        LDAA 1,X
        PSHA
        ANDA #15
        STAA 3,X
        PULA
        LSRA
        LSRA
        LSRA
        LSRA
        STAA 2,X
        LDAA 0,X
        PSHA
        ANDA #15
        STAA 1,X
        PULA
        LSRA
        LSRA
        LSRA
        LSRA
        STAA 0,X
        PULA
        STAA 8,X
        RTS
