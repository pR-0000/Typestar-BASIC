; ESC (27), low-seven-bits encodes one native byte >=128.
; Wrappers only for program LOAD/SAVE, never SERIN/SEROUT or graphics.
NATIVERX JSR SRXBYTE
        CMPA #27
        BNE NRRET
        JSR SRXBYTE
        ORAA #128
NRRET RTS
NATIVETX TSTA
        BPL NTASCII
        PSHA
        LDAA #27
        JSR STXBYTE
        PULA
        ANDA #127
NTASCII JMP STXBYTE
