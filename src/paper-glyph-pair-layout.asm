; Normalize the private rank once: 1 -> 0 (row words), 2 -> 1 (pixels).
SGLAYOUT LSR SGRANK
        BCS SGWORDS
        CLRA
        LDAB SGWIDTH
        SUBD SGSTRIDE
        BNE SGLBAD
        BRA SGSTAGING
SGWORDS LDAB SGWIDTH
        ANDB #$DF
        CMPB #16
        BHI SGLBAD
SGSTAGING JMP SGSTAGE
SGLBAD JMP RANGEERROR
SGLAYOUTEND EQU *
