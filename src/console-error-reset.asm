; Common error/BREAK display reset. ERRORWAIT already saves message X.
; Skip only CLS's EOS parser check: an invalid instruction cannot pass EOS.
; SOFTSTORE selects default cursor mode 0 (internal value 16), resets blink
; state and rebuilds reserved CGRAM slot 7. CLS also removes LCDLINE owners.
ERRORRESET LDAB #16
        JSR SOFTSTORE
        JMP CLS+3
