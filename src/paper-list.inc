; LIST and LLIST share unsigned range parsing and complete-line expansion.
; The retired HELP token $8A now spells LLIST. All other ids stay stable.
; LLAST is command-local; zero selects the LCD, $80 selects paper.
RLIST CLRB
        BRA LLBIGIN
LLIST LDAB #$80
LLBIGIN STAB LLAST
        JSR DIRECTONLY
        LDD #1
        STD RLOW
        LDD #$FFFF
        STD RHIGH
        JSR SPACE
        TSTA
        BEQ RLREADY
        JSR REXPRLINE
        STD RLOW
        STD RHIGH
        JSR SPACE
        CMPA #44
        BNE RLEOS
        INX
        STX CUR
        JSR REXPRLINE
        STD RHIGH
RLEOS JSR EOS
RLREADY LDD RHIGH
        SUBD RLOW
        BCC RLRANGE
        JMP RANGEERROR
RLRANGE LDD RLOW
        STD TEND+2
        LDX PEND
        STX TEND
        LDX #PROGRAM
        JSR $A800
        BCC RLFOUND
        TSTA
        BNE RLBAD
        BRA RLEND
RLBAD JMP RRAMERROR
RLFOUND STX RECORD
RLLOOP CPX PEND
        BCC RLEND
        LDD RHIGH
        SUBD 1,X
        BCS RLEND
        JSR LLFULL
        TST LLAST
        BMI LLPAPERGO
        CLR LWIN
        JSR LISTSHOW
RLWAIT JMP LISTWAIT
LLPAPERGO JSR LLPAPER
LLNEXT LDX RNEXT
        STX RECORD
        BRA RLLOOP
RLACK JSR HISTSAVE
        BRA LLNEXT
RLEND INC UIPENDING
        RTS
LLCOREEND EQU *
; @island format
; The complete expanded line is staged before a native motor call. Text
; goes directly to LVBUFFER for paper, outside LIST/motor shared scratch.
LLFULL JSR REXPAND
        LDD RLINE
        STD RFMT
        LDX #LBUFFER
        TST LLAST
        BPL LLFORMAT
        LDX #LVBUFFER
LLFORMAT JSR RFORMAT+6
        LDAA #32
        STAA ,X
        INX
        STX DOUT
        LDX #$1C00
LLCOPY LDAA ,X
        TST LLAST
        BPL LLKEEP
        TSTA
        BPL LLKEEP
        LDAA #63 ; Native LCD-only glyphs have no Courier 10 ASCII bitmap.
LLKEEP PSHX
        LDX DOUT
        STAA ,X
        INX
        STX DOUT
        PULX
        INX
        TSTA
        BNE LLCOPY
        LDAA DOUT+1
        ANDA #$7F ; Both buffers start on a 128-byte boundary; length <= 69.
LLLENGTH DECA
        STAA LLEN
        RTS
LLFORMATEND EQU *
; @island paper
; Finish an open LPRINT line first, then one cached job per source line.
; LVBUFFER survives those jobs; program, heap and traversal pointers remain.
LLPAPER JSR MCFREE
        JSR LLINIT
        CLR LPSUPPRESS
        TST LPCOLUMN
        BEQ LLPRINT
        CLR LPREMAIN
        JSR LPBUILD
LLPRINT LDX #LVBUFFER
        STX LPREAD
        LDAA LLEN
        STAA LPREMAIN
        JMP LPBUILD
LLPAPEREND EQU *
; @island save
; Reuse complete-line formatting without changing the serial handshake.
RSAVE JSR DIRECTONLY
        JSR EOS
        CLR LLAST
        JSR SERIALINIT
        JSR SACK
        JSR SWAITACK
        LDX #PROGRAM
        STX RECORD
RSVNEXT LDX RECORD
        CPX PEND
        BCC RSVEND
        JSR LLFULL
        LDX #LBUFFER
        JSR RSVTEXT
        LDAA #13
        JSR STXBYTE
        JSR SWAITACK
        LDX RNEXT
        STX RECORD
        BRA RSVNEXT
RSVEND LDAA #4
        JSR STXBYTE
        JSR SWAITACK
        JSR SERIALCLOSE
        LDX #SAVEDMSG
        JMP PUTS
LLSAVEEND EQU *
