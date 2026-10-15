; S-70 status cells are the second DDRAM bank, $40..$5F.
; Canon EC48 renders them using EC9C's codes; $20 clears, $B2 is
; its ordinary active marker (packed nibble enable bit + payload zero).
; Direct access avoids Canon's editor shadow $18C4 and its IRQ updater.
; BASIC runs with IRQ masked. A/B/X are preserved by STATUSWRITE.
LCDSAVED EQU $19C0
KICON   FCC "ICON"
        FCB 0
; ICON index,code: index 0..31, raw LCD character code 0..255.
; Validate the entire command before any LCD write; valid in stored programs.
ICON    JSR EXPR
        TSTA
        BNE ICONRANGE
        CMPB #31
        BHI ICONRANGE
        PSHB
        JSR SPACE
        CMPA #44
        BNE ICONSYNTAX
        INX
        STX CUR
        JSR EXPR
        TSTA
        BNE ICONRANGE
        PSHB
        JSR EOS
        PULB
        PULA
        JMP STATUSWRITE
ICONRANGE JMP RANGEERROR
ICONSYNTAX JMP SYNTAX

; A=status index, B=raw code. Preserve the actual LCD address, not LCDPOS.
; Use existing bounded busy waits and sticky LCDOK failure handling.
STATUSWRITE JMP $4809 ; Module also tracks second-bank glyph ownership.

; Canon EF1C seeds packed byte $18D3=$21: I uses selector 2 ($D7),
; II selector 1 ($D3). EE58 changes only the enable bits of these nibbles.
; Thus a generic $B2 marker is NOT the native I/II symbol code.
; Clear the inactive marker, set the active marker. Do not insert text.
LCDMODE PSHA
        PSHB
        LDAA #30
        LDAB #$20
        TST KMODE
        BNE LCDMODEI
        LDAB #$D7
LCDMODEI JSR STATUSWRITE
        LDAA #31
        LDAB #$20
        TST KMODE
        BEQ LCDMODEII
        LDAB #$D3
LCDMODEII JSR STATUSWRITE
        PULB
        PULA
        RTS
