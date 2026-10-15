; CLEAR releases scalars/strings, arrays and a closed DRAW scene.
; Keep program, GOSUB continuations, DATA cursor, serial settings and seed.
; FOR frames are invalidated. Reject pending printing before changing RAM.
; Split across small audited ROM holes; source order is not physical order.
; @island clear-entry
CLENTRY JSR EOS
        JMP CLCHECK
; @island clear-check
CLCHECK JSR MCFREE
        JMP CLRESET
; @island clear-reset
CLRESET LDX PEND
        INX
        JMP CLAPPLY
; @island clear-apply
CLAPPLY JSR DECIMAL_INIT
        CLR DFDEPTH
        RTS
