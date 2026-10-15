; THEN preserves numeric target expressions (THEN A, THEN 60000, THEN &H100).
; A keyword or single-letter assignment selects an inline statement instead.
; Inspect X without consuming CUR: the target parser/EXECUTE owns the body.
; Tail jumps avoid accumulating stack frames for nested IF ... THEN IF.
; Parenthesized names are classified against the current ABS/SGN/INT/PEEK
; vocabulary. Extend this selector when adding numeric functions such as RND.
        ORG $58A1 ; Retired IF body, after its three-byte dispatch hook.
THENSKIPSTART
; Zero-trip FOR scanning must recognize IF ... THEN FOR/NEXT without
; evaluating the skipped condition (which could read an I/O register).
THENUNWRAP JSR SPACE
        LDX #KIF
        JSR MATCH
        BCS THENUNRET
THENFIND JSR SPACE
        TSTA
        BEQ THENUNRET
        LDX #KTHEN
        JSR MATCH
        BCC THENUNWRAP
        LDX CUR
        INX
        STX CUR
        BRA THENFIND
THENUNRET RTS
THENSKIPEND EQU *
        ORG $674C ; Retired integer PEEKATOM/keyword strings; limit $67C2.
THENSTART
THENBODY JSR SPACE
        TSTA
        BEQ THENBAD
        JSR UPPER
        CMPA #65
        BCS THENTARGET
        CMPA #90
        BHI THENTARGET
        CLRB
THENWORD INCB
        INX
        LDAA ,X
        JSR UPPER
        CMPA #65
        BCS THENASSIGN
        CMPA #90
        BLS THENWORD
THENASSIGN LDAA ,X
        CMPA #32
        BEQ THENSKIP
        CMPA #9
        BNE THENEQUAL
THENSKIP INX
        BRA THENASSIGN
THENEQUAL CMPA #40 ; ABS(...), INT(...), PEEK(...) remain target expressions.
        BNE THENNOTFUNC
        LDX CUR
        LDAA ,X
        JSR UPPER
        CMPB #3
        BNE THENFOUR
        CMPA #65 ; ABS, INT, SGN: only current three-letter numeric functions.
        BEQ THENTARGET
        CMPA #73
        BEQ THENTARGET
        CMPA #83
        BEQ THENTARGET
        BRA THENEXEC ; In particular REM(...) remains a comment.
THENFOUR CMPB #4
        BNE THENEXEC ; PRINT(...), SOUND(...), LOCATE(...) are statements.
        CMPA #80
        BNE THENEXEC ; BEEP(...) and ICON(...) are not numeric functions.
        LDAA 1,X
        JSR UPPER
        CMPA #69 ; PEEK versus POKE (and other four-letter commands).
        BEQ THENTARGET
        BRA THENEXEC
THENNOTFUNC
        CMPA #61
        BEQ THENEXEC
        CMPB #1
        BNE THENEXEC
THENTARGET JMP CIFTARGET
THENEXEC JMP EXECUTE
THENBAD JMP SYNTAX
THENEND EQU *
