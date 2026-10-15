; ORIGIN [x]: declare the CURRENT head position as x (default zero).
; No movement, no homing; Y remains zero. Allows an explicit bounded return
; after mixing text and graphics, without reversing the paper or POKE tricks.
; Validate syntax/range/ownership before modifying any persistent state.
OCENTRY JSR SPACE
        TSTA
        BEQ OCZERO
        CMPA #58
        BEQ OCZERO
        JSR MCUNSIGNED
        SUBD #128
        BHI OCBAD
        ADDD #128
        BRA OCSAVE
OCZERO CLRA
        CLRB
OCSAVE STD MCX
        JMP OCVALIDATE
OCBAD JMP RANGEERROR
; Separate islands use ROM fragments too short to store a glyph.
; @island validate
OCVALIDATE JSR EOS
        JMP OCCHECK
; @island check
OCCHECK JSR MCFREE
        JMP OCCOMMIT
; @island commit
OCCOMMIT JSR PMORIGIN
        JMP OCLOAD
; @island load
OCLOAD LDD MCX
        JMP OCSTORE
; @island store
OCSTORE STD PMX
        RTS
