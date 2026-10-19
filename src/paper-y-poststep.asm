; Compensate AFTER a completed positioning move, matching the BASIC trial.
; Entry replaces PMCOMMIT's LDD PMTX; success rejoins after that instruction.
; PMY still holds the old nominal position here. All accepted paper targets
; are nonnegative and below 32767, so delta+1 is negative exactly for delta<=-2.
YPACC EQU $1B8D
YPPOST LDD PMTY
        SUBD PMY
        ADDD #1
        BPL YPDONE
        LDAA YPACC
        ; YPGAIN is the fraction in 1/256 units: .91=96 (3/8), .92=64 (1/4).
        ADDA #YPGAIN
        STAA YPACC
        BCC YPDONE
        ; Mark the original travel completed before issuing a forward unit.
        ; The re-entry then sees delta=0 and cannot apply a second correction.
        ; PMVALID stays pending until the common successful commit/cleanup.
        LDD PMTY
        STD PMY
        LDD #1
        JMP PMFEED+8
YPDONE LDD PMTX
        JMP PMCOMMIT+3
YPEND EQU *
; @island boot
YPBOOT LDD #$5400
        STD LSPITCH
        JMP MOTORBOOT
YPBOOTEND EQU *
