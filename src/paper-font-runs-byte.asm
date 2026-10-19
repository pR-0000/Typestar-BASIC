; Lossless Canon font decoder with short Huffman run tokens. A=ASCII 32..126, X=93-byte destination.
; Output is 31 native triplets (lane A,B,C), not a 16-row approximation.
; C clear on success. C set on bad character/truncated stream/invalid code.
; HFSTATE is 26 bytes of exclusive temporary scratch, never persistent.
; Tables: [source word,length byte] per glyph; byte-sized canonical counts.
HFRUN EQU HFSTATE+25 ; Private byte before the motor temporaries at $1DA5.
HFSRC EQU HFSTATE
HFSTOP EQU HFSTATE+2
HFDEST EQU HFSTATE+4
HFLEFT EQU HFSTATE+6
HFBITS EQU HFSTATE+7
HFBYTE EQU HFSTATE+8
HFCODE EQU HFSTATE+9
HFFIRST EQU HFSTATE+11
HFLEN EQU HFSTATE+13
HFCPTR EQU HFSTATE+14
HFSPTR EQU HFSTATE+16
HFCOUNT EQU HFSTATE+18
HFPREV EQU HFSTATE+20
HFCHAN EQU HFSTATE+23
HFBIT EQU HFSTATE+24
HFDECODE STX HFDEST
        SUBA #32
        CMPA #94
        BLS HFVALID
        JMP HFBAD
HFVALID EQU *
        TAB
        LDAA #3
        MUL
        ADDD #HFGLYPHS
        XGDX
        LDD ,X
        STD HFSRC
        CLRA
        LDAB 2,X
        ADDD HFSRC
        STD HFSTOP
        CLR HFBITS
        CLR HFCHAN
        CLR HFRUN
        CLRA
        CLRB
        STD HFPREV
        CLR HFPREV+2
        LDAA #93
        STAA HFLEFT
HFVALUE TST HFRUN
        BEQ HFNEWVALUE
        DEC HFRUN
        CLRA
        BRA HFXOR
HFNEWVALUE CLRA
        CLRB
        STD HFCODE
        STD HFFIRST
        LDX #HFCOUNTS
        STX HFCPTR
        LDX #HFSYMBOLS
        STX HFSPTR
        LDAA #HFMAXBITS
        STAA HFLEN
HFLEVEL JSR HFGETBIT
        BCS HFBAD
        LSRB ; Append the returned 0/1 bit directly through carry.
        ROL HFCODE+1
        ROL HFCODE
        LDX HFCPTR
        CLRA
        LDAB ,X
        STD HFCOUNT
        INX
        STX HFCPTR
        LDD HFCODE
        SUBD HFFIRST
        BCS HFBAD
        SUBD HFCOUNT
        BCS HFFOUND
        LDD HFSPTR
        ADDD HFCOUNT
        STD HFSPTR
        LDD HFFIRST
        ADDD HFCOUNT
        ASLB
        ROLA
        STD HFFIRST
        DEC HFLEN
        BNE HFLEVEL
HFBAD SEC
        RTS
HFFOUND ADDD HFCOUNT
        ADDD HFSPTR
        XGDX
        LDAA ,X
        CMPA #$B1 ; Unused byte values encode zero-delta runs 8..22.
        BLO HFXOR
        CMPA #$BF
        BHI HFXOR
        SUBA #$AA
        STAA HFRUN
        CLRA
HFXOR   LDX #HFPREV
        LDAB HFCHAN
        ABX
        EORA ,X
        STAA ,X
        LDX HFDEST
        STAA ,X
        INX
        STX HFDEST
        INCB ; B still holds the old lane index.
        CMPB #3
        BLO HFCHANNEL
        CLRB
HFCHANNEL STAB HFCHAN
        DEC HFLEFT
        BEQ HFDONE
        JMP HFVALUE
HFDONE EQU *
        ; The 93rd byte closes lane 2: CMPB #3 already cleared carry.
        RTS
HFGETBIT TST HFBITS
        BNE HFSHIFT
        LDX HFSRC
        CPX HFSTOP
        BCC HFZERO
        LDAA ,X
        INX
        STX HFSRC
        STAA HFBYTE
        LDAA #8
        STAA HFBITS
HFSHIFT ASL HFBYTE
        LDAB #0 ; Preserve the extracted bit in carry for ROLB.
        ROLB
        DEC HFBITS
        ; ROLB of the zero/one bit already cleared carry.
        RTS
HFZERO CLRB
        RTS
HFEND EQU *
