; Lossless Canon font decoder. A=ASCII 32..126, X=93-byte destination.
; Output is 31 native triplets (lane A,B,C), not a 16-row approximation.
; C clear on success. C set on bad character/truncated stream/invalid code.
; HFSTATE is 25 bytes of exclusive temporary scratch, never persistent.
; Tables: [source word,length byte] per glyph; canonical counts/symbols shared.
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
        CLR HFPREV
        CLR HFPREV+1
        CLR HFPREV+2
        LDAA #93
        STAA HFLEFT
HFVALUE CLR HFCODE
        CLR HFCODE+1
        CLR HFFIRST
        CLR HFFIRST+1
        LDX #HFCOUNTS
        STX HFCPTR
        LDX #HFSYMBOLS
        STX HFSPTR
        LDAA #HFMAXBITS
        STAA HFLEN
HFLEVEL JSR HFGETBIT
        BCS HFBAD
        STAB HFBIT
        LDD HFCODE
        ASLB
        ROLA
        ORAB HFBIT
        STD HFCODE
        LDX HFCPTR
        LDD ,X
        STD HFCOUNT
        INX
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
        LDX #HFPREV
        LDAB HFCHAN
        ABX
        EORA ,X
        STAA ,X
        LDX HFDEST
        STAA ,X
        INX
        STX HFDEST
        INC HFCHAN
        LDAA HFCHAN
        CMPA #3
        BNE HFCHANNEL
        CLR HFCHAN
HFCHANNEL DEC HFLEFT
        BEQ HFDONE
        JMP HFVALUE
HFDONE EQU *
        CLC
        RTS
HFGETBIT TST HFBITS
        BNE HFSHIFT
        LDX HFSRC
        CPX HFSTOP
        BCC HFBAD
        LDAA ,X
        INX
        STX HFSRC
        STAA HFBYTE
        LDAA #8
        STAA HFBITS
HFSHIFT ASL HFBYTE
        LDAB #0
        ROLB
        DEC HFBITS
        CLC
        RTS
HFEND EQU *
