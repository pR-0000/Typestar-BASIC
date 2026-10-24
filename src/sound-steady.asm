; .96: timer accounting outside the ms loop preserves waveform continuity.
; Only reads Timer 1. Periods, GPIO states and generated kernels are unchanged.
; Ordinary playback spends much less time muted between batches.
SNDPLAYPREP LDAB #1
        LDAA SNDMODE
        CMPA #3
        BEQ SNDBATCHREADY
        LDD SNDHZ
        LSRD
        LSRD
        LSRD
        LSRD
        LSRD
        LSRD
        LSRD
SNDBATCHFITS INCB
SNDBATCHREADY STAB SNDBATCH
        LDD $09
        STD SNDSTAMP
SNDRUN LDAB SNDBATCH
SNDCALL LDX SNDBASE
        JSR ,X
        LDD $09
        STD SNDON ; waveform compilation has finished: this word is now free.
        SUBD SNDSTAMP
        LDX SNDLEFT
SNDTICKS SUBD #1000
        BCS SNDFRACTION
        DEX
        BNE SNDTICKS
        JMP SNDSTOP
SNDFRACTION STX SNDLEFT
        ; D=remaining fraction-1000. ~D + now - 999 = now-fraction.
        COMA
        COMB
        ADDD SNDON
        SUBD #999
        STD SNDSTAMP
        JSR RFASTBREAK
        BNE SNDRUN
        JMP SNDBREAK
SNDPLAYPREPEND EQU *
