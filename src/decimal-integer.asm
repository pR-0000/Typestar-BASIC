; OFFLINE integration: exact conversion of native DW to a 16-bit parameter.
; No truncation: fractional nonzero digits fail. Accept -32768..65535;
; positive 32768..65535 keep their unsigned bit pattern for PEEK/POKE etc.
; Caller applies command-specific range rules. X preserved, C=error, D=result.
        OPT H01
        ORG $A400
DW EQU $1E94
DIACC EQU $1ECA
DITMP EQU $1ECC
DIDIG EQU $1ECE
DICOUNT EQU $1ECF
DINTEGER PSHX
        LDAA DW+8
        ANDA #15
        CMPA #7
        BHI DIBAD
        LDAB #8
        SBA
        NEGA
        STAA DICOUNT
; Check every fractional digit before accumulating the integer coefficient.
        TAB
        LDX #DW
        ABX
DIFRACT CPX #DW+8
        BEQ DIBEGIN
        TST ,X
        BNE DIBAD
        INX
        BRA DIFRACT
DIBEGIN CLRA
        CLRB
        STD DIACC
        LDX #DW
DILOOP LDAA ,X
        STAA DIDIG
        LDD DIACC
        SUBD #6553
        BCS DIMUL
        BNE DIBAD
        LDAA DIDIG
        CMPA #5
        BHI DIBAD
DIMUL LDD DIACC
        ASLD
        STD DITMP
        ASLD
        ASLD
        ADDD DITMP
        ADDB DIDIG
        BCC DIDIGITOK
        INCA
DIDIGITOK STD DIACC
        INX
        DEC DICOUNT
        BRA DICONTINUE
DIHEADEND EQU *
; Preserve native A45E..A466: a flag query used by the motion scheduler.
; The builder restores those nine original bytes inside this sparse module.
        ORG $A467
DICONTINUE
        BNE DILOOP
        TST DW+8
        BPL DIOK
        SUBD #32768
        BHI DIBAD
        CLRA
        CLRB
        SUBD DIACC
DIOK PULX
        CLC
        RTS
DIBAD PULX
        SEC
        RTS
