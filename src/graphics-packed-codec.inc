; X is the payload input pointer, GXLEFT=62 output bytes remaining.
; Decode into fixed 64-byte scratch, never user RAM. Only a fully valid block
; may commit the print job, reclaim RAM and touch the band buffer.
GXPACKED LDAA GXCOUNT
        CMPA #109 ; 21-byte prefix + 83 packed symbols + 5-byte CRC trailer.
        BNE GXCFAIL
        CLR GXBITS
        CLR GXBYTE
GXPACKCHAR LDAA 0,X
        INX
        SUBA #48
        BCS GXCFAIL
        CMPA #63
        BHI GXCFAIL
        ASLA
        ASLA
        STAA GXPACK
        LDAA #6
        STAA GXSIX
GXPACKBIT ASL GXPACK
        ROL GXBYTE
        INC GXBITS
        LDAA GXBITS
        CMPA #8
        BNE GXPACKNEXT
        LDAA GXBYTE
        JSR GXEMIT
        CLR GXBITS
GXPACKNEXT DEC GXSIX
        BNE GXPACKBIT
        TST GXLEFT
        BNE GXPACKCHAR
        LDAA GXBYTE
        ANDA #3 ; Last two encoded bits are canonical zero padding.
        BNE GXCFAIL
        BRA GXCODEEND
GXRUNS JSR GF_HEXBYTE
        BCS GXCFAIL
        TSTA
        BEQ GXCFAIL
        CMPA GXLEFT
        BHI GXCFAIL
        STAA GXSIX ; Count fits remaining output; no buffer overflow possible.
        JSR GF_HEXBYTE
        BCS GXCFAIL
        STAA GXBYTE
GXRUNLOOP LDAA GXBYTE
        JSR GXEMIT
        DEC GXSIX
        BNE GXRUNLOOP
        TST GXLEFT
        BNE GXRUNS
GXCODEEND STX GXPTR
        LDX GXENDPTR
        CPX GXPTR ; Reject extra input and truncated/noncanonical representations.
        BNE GXCFAIL
        RTS
GXCFAIL JMP GXFAIL
GXEMIT PSHX
        LDX GXOUTPTR
        STAA 0,X
        INX
        STX GXOUTPTR
        PULX
        DEC GXLEFT
        RTS
