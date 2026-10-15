; Immediate foreground handoff after original Canon startup.
; No display or artificial settling loop. Hardware startup remains upstream.
        OPT H01
        ORG $6829
HOOK    SEI
        CLRA
        STAA $37
        JMP $5000
        ; Preserve the historical patch footprint for exact diff checks.
        ORG $6858
        FCB $01
HOOKEND EQU *
