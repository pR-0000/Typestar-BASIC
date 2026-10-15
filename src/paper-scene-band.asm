; Scene callback for the existing synchronous RBJOB driver (offline linker).
; A=band index, B=tile count, X=destination band at DFLOOR.
; SBLIST must already point to the scene count byte in a validated private
; array. NEVER call SCLIST here: SCJOB aliases the active RBSTATE workspace.
; No heap allocations/changes may occur between resolving SBLIST and RBJOB.
; PCBASE points directly into the band, avoiding a second 64-byte tile.
; Caller validates all records and computes the total extent before motion.
SBBAND STX PCBASE
        STAB SBLEFT
        LDAB #16
        MUL
        STAB PCOY
        CLR PCOX
SBNEXT LDX SBLIST
        LDAB ,X
        INX
        JSR PCRENDER
        BCS SBRETURN
        LDD PCBASE
        ADDD #64
        STD PCBASE
        LDAA PCOX
        ADDA #31
        STAA PCOX
        DEC SBLEFT
        BNE SBNEXT
        CLC
SBRETURN RTS
SBEND EQU *
