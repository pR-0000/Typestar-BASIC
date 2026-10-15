; Offline compositor: several shapes, ONE shared logical page origin.
; No motor calls. Not yet a BASIC command or part of the release image.
; X=validated 8-byte record list, B=count (0..32), PCOX/PCOY=native tile origin.
; Record: kind (0 box,1 line), x1,y1,x2,y2,width,fill,reserved.
; All coordinates are absolute in the SAME drawing, never relative to the
; previous primitive. Renderer converts logical Y into native rows.
; PCOUT is a separate 64-byte tile, PBOUT/PLOUT the shared shape scratch.
; Caller must validate records, extent and RAM bounds before submission.
; C=0 completed; C=1 invalid kind/count/renderer error, discard entire output.
; Source records untouched. X/A/B and renderer scratch clobbered.
PCPTR EQU PCSTATE
PCLEFT EQU PCSTATE+2
PCOX EQU PCSTATE+3
PCOY EQU PCSTATE+4
PCDEST EQU PCSTATE+5
PCRENDER CMPB #32
        BLS PCVALID
        SEC
        RTS
PCVALID STX PCPTR
        STAB PCLEFT
        LDX #PCOUT
        LDAB #64
PCZERO CLR ,X
        INX
        DECB
        BNE PCZERO
        TST PCLEFT
        BNE PCNEXT
PCOK CLC
        RTS
PCNEXT LDX PCPTR
        LDAA ,X
        BEQ PCBOX
        CMPA #1
        BEQ PCLINE
PCBAD SEC
        RTS
PCLINE LDD 1,X
        STD PLSTATE
        LDD 3,X
        STD PLSTATE+2
        LDAA 5,X
        STAA PLWIDTH
        LDAA PCOX
        STAA PLOX
        LDAA PCOY
        STAA PLOY
        JSR PLLINE
        BRA PCMERGE
PCBOX CLRA
        LDAB 1,X
        STD PBLEFT
        LDAB 3,X
        STD PBRIGHT
        LDAB 2,X
        LSRB
        STD PBTOP
        LDAB 4,X
        LSRB
        STD PBBOTTOM
        LDAB PCOX
        STD PBTX
        LDAB PCOY
        STD PBTY
        LDAA 5,X
        STAA PBWIDTH
        INCA
        LSRA
        STAA PGYWIDTH
        LDAA 6,X
        STAA PBFILL
        JSR PBRECT
PCMERGE BCS PCBAD
        ; OR means overlap stays black, independent of primitive order.
        LDX #PCOUT
        STX PCDEST
        LDX #PBOUT
        LDAB #64
PCOR LDAA ,X
        PSHX
        LDX PCDEST
        ORAA ,X
        STAA ,X
        INX
        STX PCDEST
        PULX
        INX
        DECB
        BNE PCOR
        LDX PCPTR
        LDAB #8
        ABX
        STX PCPTR
        DEC PCLEFT
        BNE PCMORE
        CLC
        RTS
PCMORE JMP PCNEXT
PCEND EQU *
