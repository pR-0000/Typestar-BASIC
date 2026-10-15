; PBOX x1,y1,x2,y2,thickness,fill. Shared prototype/linker source.
; The .56 linker supplies real RAM and BASIC error routing. The .57 linker
; redirects RBJOB through PGSTART, converting public logical Y and thickness
; to native raster rows. This standalone source retains the raw test path.
; Entire syntax/ranges checked before RBJOB: 0<=x<=247, 0<=y<=255,
; x1<=x2, y1<=y2, thickness 1..16, fill 0 or 1.
; PXSTATE has 6 staged bytes plus one index byte; independent of EXPR scratch.
PXINDEX EQU PXSTATE+6
PXDISPATCH LDX #PXNAME
        JSR MATCH
        BCC PXPARSE
        JMP RZDISPATCH
PXNAME FCC "PBOX"
        FCB 0
PXPARSE CLR PXINDEX
PXARG JSR EXPR
        TSTA
        BNE PXRANGE
        TST DW+8
        BMI PXRANGE
        PSHB
        LDX #PXSTATE
        LDAB PXINDEX
        ABX
        PULB
        STAB ,X
        INC PXINDEX
        LDAA PXINDEX
        CMPA #6
        BEQ PXCHECK
        JSR SPACE
        CMPA #44
        BNE PXSYNTAX
        INX
        STX CUR
        BRA PXARG
PXRANGE JMP RANGEERROR
PXSYNTAX JMP SYNTAX
PXCHECK JSR EOS
        LDAA PXSTATE
        CMPA PXSTATE+2
        BHI PXRANGE
        LDAA PXSTATE+2
        CMPA #247
        BHI PXRANGE
        LDAA PXSTATE+1
        CMPA PXSTATE+3
        BHI PXRANGE
        LDAA PXSTATE+4
        BEQ PXRANGE
        CMPA #16
        BHI PXRANGE
        LDAA PXSTATE+5
        CMPA #1
        BHI PXRANGE
; Only now commit renderer parameters. EXPR scratch will be saved by RBJOB.
        CLRA
        LDAB PXSTATE
        STD PBLEFT
        LDAB PXSTATE+2
        STD PBRIGHT
        LDAB PXSTATE+1
        STD PBTOP
        LDAB PXSTATE+3
        STD PBBOTTOM
        LDAA PXSTATE+4
        STAA PBWIDTH
        LDAA PXSTATE+5
        STAA PBFILL
; Number of tiles is floor(x2/31)+1; bands floor(y2/16)+1.
        LDAA PXSTATE+2
        CLRB
PXDIV INCB
        SUBA #31
        BCC PXDIV
        LDAA PXSTATE+3
        LSRA
        LSRA
        LSRA
        LSRA
        INCA
        JSR RBJOB
        BCS PXRANGE
        RTS
PXEND EQU *
