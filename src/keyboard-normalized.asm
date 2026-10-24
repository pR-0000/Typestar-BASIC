; Lossless 40-map tree: lowercase normalization, aliases and byte parent links.
KDENTRY LDAA KLOCALE
        CMPA #10
        BCS KDVALID
        JMP KBDNONE
KDVALID ASLA
        ASLA
        TST KMODE
        BEQ KDSHIFT
        ADDA #2
KDSHIFT LDAB $32
        BPL KDINDEX
        INCA
KDINDEX TAB
KDPARENT LDX #KDTABLE
        ABX
        LDAB ,X
        CLRA
        ASLB
        ROLA
        ADDD #KDDATA
        XGDX
KDSCAN LDAA ,X
        BMI KDLINK
        CMPA KRAW
        BEQ KDFOUND
        INX
        INX
        BRA KDSCAN
KDFOUND LDAA 1,X
KDCASE TST $32
        BPL KDRETURN
        CMPA #97
        BLO KDRETURN
        CMPA #122
        BHI KDRETURN
        SUBA #32
KDRETURN JMP KBDRETURN
KDLINK INX
        CMPA #$FF
        BEQ KDROOT
        LDAB ,X
        BRA KDPARENT
KDROOT LDAB KRAW
        CMPB #26
        BCC KDROOTTAIL
        ADDB #97
        TBA
        BRA KDCASE
KDROOTTAIL SUBB #26
        ABX
        LDAA ,X
        BRA KDCASE
KDCODEEND EQU *
