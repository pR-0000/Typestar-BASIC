; Shared existing recursive function parser, nine fixed six-byte entries.
; PI remains a constant before this table. Function id stays on CPU stack
; while evaluating nested arguments; no global selector or new RAM.
        ORG $4B93
NFAPPLY CMPB #5
        BCS NFOLD
        BEQ NFSQR
        PSHB
        JSR $A400 ; FRE/SERIN/INKEY require an exact zero argument.
        BCS NFBAD
        SUBD #0
        BNE NFBAD
        PULB
        CMPB #6
        BEQ NFFRE
        CMPB #7
        BEQ NFSERIN
        JMP $8EE6 ; existing INKEY poll and pending-event handling
NFFRE JMP $9175 ; existing free-byte calculation
NFSERIN JMP $8F5E ; existing SCI checks and receive path
NFBAD PULB
        LDAA #4
        STAA DERR
        RTS
NFOLD JMP $47DF
NFSQR JMP SQROOT
NFAPPLYEND EQU *


        ORG $912A
NFENTRY LDX #NFTABLE
        JMP FNENTRY+3
NFTABLE FCB 3
        FCC "ABS  "
        FCB 3
        FCC "SGN  "
        FCB 3
        FCC "INT  "
        FCB 4
        FCC "PEEK "
        FCB 3
        FCC "RND  "
        FCB 3
        FCC "SQR  "
        FCB 3
        FCC "FRE  "
        FCB 5
        FCC "SERIN"
        FCB 5
        FCC "INKEY"
NFTABLEEND EQU *
