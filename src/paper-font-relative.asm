; Same canonical Huffman/RLE stream and native 93-byte glyphs as .94.
; Relative canonical codes avoid a second 16-bit accumulator.
; Descriptor bit 7 reverses native columns for exact mirror pairs.
HFSRC EQU HFSTATE
HFSTOP EQU HFSTATE+2
HFDEST EQU HFSTATE+4
HFLEFT EQU HFSTATE+6
HFBITS EQU HFSTATE+7
HFBYTE EQU HFSTATE+8
HFCODE EQU HFSTATE+9
HFMIRROR EQU HFSTATE+11
HFLEN EQU HFSTATE+13
HFCPTR EQU HFSTATE+14
HFSPTR EQU HFSTATE+16
HFPREV EQU HFSTATE+20
HFCHAN EQU HFSTATE+23
HFRUN EQU HFSTATE+25
HFDECODE STX HFDEST
        SUBA #32
        CMPA #94
        BLS HFVALID
        SEC
        RTS
HFVALID TAB
        LDAA #3
        MUL
        ADDD #HFGLYPHS
        XGDX
        LDD ,X
        STD HFSRC
        LDAA 2,X
        STAA HFMIRROR
        ANDA #127
        STAA HFSTOP
        TST HFMIRROR
        BPL HFFORWARD
        LDD HFDEST
        ADDD #90
        STD HFDEST
HFFORWARD CLR HFBITS
        CLR HFCHAN
        CLR HFRUN
        LDD #0
        STD HFPREV
        CLR HFPREV+2
        LDAA #93
        STAA HFLEFT
HFVALUE TST HFRUN
        BEQ HFNEWVALUE
        DEC HFRUN
        CLRA
        BRA HFXOR
HFNEWVALUE LDD #0
        STD HFCODE
        LDAB HFCHAN
        ASLB
        LDX #HFTABLES
        ABX
        LDX ,X
        STX HFCPTR
        LDAB #11
        ABX
        STX HFSPTR
HFLEVEL JSR HFGETBIT
        LDD HFCODE
        ROLB
        ROLA
        LDX HFCPTR
        SUBB ,X
        SBCA #0
        BCS HFFOUND
        STD HFCODE
        LDD HFSPTR
        ADDB ,X
        ADCA #0
        STD HFSPTR
        INX
        STX HFCPTR
        BRA HFLEVEL
HFBAD SEC
        RTS
HFFOUND ADDB ,X
        ADCA #0
        ADDD HFSPTR
        XGDX
        LDAA ,X
        CMPA #$B1
        BLO HFXOR
        CMPA #$BF
        BHI HFXOR
        SUBA #$A5
        STAA HFRUN
        CLRA
HFXOR LDX #HFPREV
        LDAB HFCHAN
        ABX
        EORA ,X
        STAA ,X
        LDX HFDEST
        STAA ,X
        INX
        STX HFDEST
        INCB
        CMPB #3
        BLO HFCHANNEL
        CLRB
        TST HFMIRROR
        BPL HFCHANNEL
        DEX
        DEX
        DEX
        DEX
        DEX
        DEX
        STX HFDEST
HFCHANNEL STAB HFCHAN
        DEC HFLEFT
        BEQ HFDONE
        JMP HFVALUE
HFDONE RTS
HFGETBIT TST HFBITS
        BNE HFSHIFT
        ; Trusted ROM streams use a one-bit zero code. At most 93 virtual
        ; zero bits are needed, so this signed exhausted count cannot wrap.
        DEC HFSTOP
        BMI HFZERO
        LDX HFSRC
        LDAA ,X
        INX
        STX HFSRC
        STAA HFBYTE
        LDAA #8
        STAA HFBITS
HFSHIFT ASL HFBYTE
        DEC HFBITS
        RTS
HFZERO CLC
        RTS
HFEND EQU *
