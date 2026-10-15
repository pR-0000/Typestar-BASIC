; First RND API: RND(1), decimal result 0..0.9999, four fractional digits.
; Deterministic 16-bit Galois LFSR, eight steps/sample. State zero seeds to 1.
; Reject state-1 >=60000, then modulo 10000: each result has six preimages.
; State has period 65535; no division or additional native workspace needed.
RNDSTATE EQU $1EC6
        ORG $47DF
RNDDISPATCH CMPB #4
        BEQ RNDCHECK
        JMP FNAPPLY
RNDCHECK JSR $A400
        BCS RNDARGERROR
        SUBD #1
        BNE RNDARGERROR
        JMP RNDNEXT
RNDARGERROR LDAA #4
        STAA DERR
        RTS
RNDDISPATCHEND EQU *

; Extend THEN's numeric-function classification without shifting its module.
; RND and REM share R; the second letter distinguishes them.
        ORG $54C4
RNDTHEN CMPA #83
        BNE RNDTHENR
        JMP THENTARGET
RNDTHENR CMPA #82
        BNE RNDTHENNO
        LDAA 1,X
        ANDA #$DF
        CMPA #78
        BNE RNDTHENNO
        JMP THENTARGET
RNDTHENNO JMP THENEXEC
RNDTHENEND EQU *

        ORG $9BC7
RNDNEXT LDD RNDSTATE
        BNE RNDSEEDED
        LDD #1
RNDSEEDED LDX #8
RNDBIT LSRD
        BCC RNDNOSHIFT
        EORA #$B4
RNDNOSHIFT DEX
        BNE RNDBIT
        STD RNDSTATE
        SUBD #1
        SUBD #60000
        BCC RNDNEXT
        ADDD #60000
RNDMOD SUBD #10000
        BCC RNDMOD
        ADDD #10000
        STD DOUT
        JSR RDVALUE
        LDAA #4
        STAA DW+8
        RTS
RNDEND EQU *
