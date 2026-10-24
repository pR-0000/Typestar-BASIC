; .98: continuous, cycle-counted gate playback. No timer or keyboard polling.
; X counts complete periods (31-bit patterns for noise); D handles delays.
; An RTS trampoline calls the generated kernel without clobbering X.
; SOUND keeps the original requested milliseconds in SNDLEFT for Studio.
; @island delaycode
; Exact delay D >= 0: 3+8*n clocks and 0..7 NOPs, or a short NOP run.
; D is free after each cached gate write; X remains the period counter.
SNDDELAYCODE SUBD #11
        BCS SNDNOPSRESTORE
        ADDD #8
        PSHB
        LSRD
        LSRD
        LSRD
        PSHB
        PSHA
        LDAA #$CC
        BSR SNDEMIT
        PULA
        PULB
        BSR SNDEMIT2
        LDD #$8300
        BSR SNDEMIT2
        LDD #$0101
        BSR SNDEMIT2
        LDD #$0126
        BSR SNDEMIT2
        LDAA #$F9
        BSR SNDEMIT
        PULB
        ANDB #7
        BRA SNDNOPS
SNDNOPSRESTORE ADDB #11
SNDNOPS BEQ SNDNOPSEND
        LDAA #1
SNDNOPLOOP BSR SNDEMIT
        DECB
        BNE SNDNOPLOOP
SNDNOPSEND RTS
; @island play
SNDPLAYPREP LDD SNDPER
        STD SNDDIVISOR
        LDAA SNDMODE
        CMPA #3
        BNE SNDCOUNTLOOPS
        ; The noise kernel contains 31 bit periods, at most 31000 clocks.
        LDD SNDPER
        ASLD
        ASLD
        ASLD
        ASLD
        ASLD
        SUBD SNDPER
        STD SNDDIVISOR
SNDCOUNTLOOPS LDX #SNDLEFT
        LDAA #232
        JSR SNDMUL8
        ; 1000 = 232 + 3*256. Product fits in 24 bits (<= 2000000).
        LDD SNDLEFT
        ASLD
        ADDD SNDLEFT
        ADDB SNDWIDE
        ADCA SNDHIGH
        STAB SNDWIDE
        STAA SNDHIGH
        JSR SNDDIV
        ; Whole cycles round down; very short requests play one minimum cycle.
        BNE SNDCONTSTART
        INX
SNDCONTSTART LDD #SNDSTOP
        PSHB
        PSHA
        LDD SNDBASE
        PSHB
        PSHA
SNDCALL RTS
SNDPLAYPREPEND EQU *
; @island multiply
; Unsigned byte A * word at X -> SNDHIGH:SNDWIDE (24 bits).
SNDMUL8 PSHA
        LDAB 1,X
        MUL
        JMP SNDMULLOW
; @island multiplylow
; Small tails occupy seven-byte ROM fragments; no waveform runs here.
SNDMULLOW STD SNDWIDE
        PULA
        JMP SNDMULHIGH
; @island multiplyhigh
SNDMULHIGH LDAB ,X
        MUL
        ADDB SNDWIDE
        ADCA #0
        STAB SNDWIDE
        STAA SNDHIGH
        RTS
