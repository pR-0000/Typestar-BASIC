; Forty locale/mode/shift maps share a minimum spanning tree of differences.
; Each node contains (key,value) pairs followed by $FE,parent-address.
; The root starts with $FF then the complete 44-key map. No recursion/RAM.
; Search a child first: its differing keys override the inherited mapping.
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
        ASLB
        LDX #KDTABLE
        ABX
        LDX ,X
KDSCAN LDAA ,X
        BMI KDLINK
        CMPA KRAW
        BEQ KDFOUND
        INX
        INX
        BRA KDSCAN
KDFOUND LDAA 1,X
        JMP KBDRETURN
KDLINK INX
        CMPA #$FF
        BEQ KDROOT
        LDX ,X
        BRA KDSCAN
KDROOT LDAB KRAW
        ABX
        LDAA ,X
        JMP KBDRETURN
KDCODEEND EQU *
