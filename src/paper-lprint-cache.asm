; Prepare distinct glyphs before printing; reuse their pixels thereafter.
; If RAM is short, keep a smaller cache and replace its last slot on a miss.
; ASCII keys share the inactive serial-graphics pattern buffer, not BASIC RAM.
; Up to 72 columns, explicit newline; trailing semicolon retains position.
; PMVALID=3 owns PMX+1 as the text column. Native motion invalidates it.
; Validate the complete statement before heating, then print one transaction.
; Source lives in the BASIC input/expanded-line buffer, outside native scratch.
; No full-string copy or permanent heap reservation is needed.
; No expression evaluation or heap mutation during decode/physical printing.
; Temporary LIST/SAVE/motor scratch is exclusive while a command is running.
LPCACHE EQU GXPATTERN
LPREAD EQU $1DAD
LPREMAIN EQU $1DAF
LPSUPPRESS EQU $1DB0
LPUCOUNT EQU $1DB1
LPCOLUMN EQU PMX+1
LPMODE EQU $1DBA
LPPTR EQU $1DBB
LPDEST EQU $1DBD
LPLEFT EQU $1DBF
LPCOUNT EQU $1DC0
LPINDEX EQU $1DC1
LPDISPATCH CLR LPMODE
        LDX #LPNAME
        JSR MATCH
        BCC LPPARSE
        JMP PTDISPATCH
LPNAME FCC "LPRINT"
        FCB 0
LPPARSE JSR SPACE
        CLR LPREMAIN
        CLR LPSUPPRESS
        TSTA
        BEQ LPENDTEXT
        CMPA #58
        BEQ LPENDTEXT
        CMPA #34
        BEQ LPOPEN
        JMP LPSYNTAX
LPOPEN EQU *
        INX
        STX LPREAD
        CLR LPREMAIN
LPSCAN LDAA ,X
        CMPA #34
        BEQ LPQUOTED
        CMPA #32
        BHS LPCHARLOWOK
        JMP LPSYNTAX
LPCHARLOWOK EQU *
        CMPA #126
        BLS LPCHARHIGHOK
        JMP LPBAD
LPCHARHIGHOK EQU *
        LDAB LPREMAIN
        CMPB #63
        BCS LPLENGTHOK
        JMP LPBAD
LPLENGTHOK EQU *
        INC LPREMAIN
        INX
        BRA LPSCAN
LPQUOTED INX
        STX CUR
LPENDTEXT JSR SPACE
        CMPA #59
        BNE LPVALIDATE
        INC LPSUPPRESS
        INX
        STX CUR
LPVALIDATE EQU *
        JSR EOS
        ; Reject an open drawing, serial session or engaged printer first.
        JSR MCFREE
        LDAA PMVALID
        CMPA #3
        BEQ LPCHECKWIDTH
        CLR LPCOLUMN
LPCHECKWIDTH LDAA LPCOLUMN
        ADDA LPREMAIN
        CMPA #72
        BLS LPBUILD
        JMP LPBAD
LPBUILD LDAA LPREMAIN
        STAA LPCOUNT
        STAA LPLEFT
        CLR LPUCOUNT
        CLR LPINDEX
        CLR LPREMAIN
        TSTA
        BNE LPSTARTCACHE
        TST LPSUPPRESS
        BNE LPRETURN
        BRA LPCOPIED
LPSTARTCACHE EQU *
        LDX LPREAD
        STX LPPTR
LPCOPY LDX LPPTR
        LDAA ,X
        INX
        STX LPPTR
        JSR LPLOOKUP
        CMPB LPUCOUNT
        BCS LPFOUND
        STAA ,X
        INC LPUCOUNT
LPFOUND DEC LPLEFT
        BNE LPCOPY
LPCOPIED EQU *
        LDAB LPCOUNT
        BNE LPHASCOUNT
        INCB ; Empty LPRINT borrows one record but never heats/prints it.
LPHASCOUNT EQU *
        LDAA #1
        STAA LPMODE
        JSR RBJOB
        CLR LPMODE
        TSTA
        BNE LPERROR
        CLR GPRAN
        LDAA #3
        STAA PMVALID
LPRETURN RTS
LPERROR JMP RBPAPERERROR
LPBAD JMP RANGEERROR
LPSYNTAX JMP SYNTAX

; Preserve the old 64-byte graphics path when not rendering text.
LPSIZE LDAA #64
        TST LPMODE
        BEQ LPMUL
        LDAB LPUCOUNT
        BNE LPCACHETRY
        INCB ; Empty newline retains the minimum checked reservation.
; Clip the cache to free RAM without touching the program or heap boundaries.
; At least one record is requested; RBJOB rejects even that if it cannot fit.
LPCACHETRY STAB LPUCOUNT
        LDAA #96
        MUL
        ADDD DFLOOR
        BCS LPCACHESMALL
        ADDD #220
        BCS LPCACHESMALL
        SUBD DHEAP
        BLS LPCACHEFITS
LPCACHESMALL LDAB LPUCOUNT
        CMPB #1
        BEQ LPCACHESIZE
        DECB
        BRA LPCACHETRY
LPCACHEFITS LDAB LPUCOUNT
LPCACHESIZE EQU *
        LDAA #96
LPMUL MUL
        RTS
LPNEXT TST LPMODE
        BEQ LPADD64
        ; LPPRINT selects each cached pointer independently of the last one.
        RTS
LPADD64 ADDD #64
        RTS
LPFORMAT LDAA LPMODE
        STAA GPDESC+1
        RTS

LPSELECT TST LPMODE
        BNE LPRENDER
        JMP LNSELECT
LPRENDER TST LPCOUNT
        BEQ LPEMPTY
        STX LPDEST
        LDAB LPUCOUNT
        STAB LPLEFT
        LDX #LPCACHE
        STX LPPTR
LPNEXTCHAR LDX LPPTR
        LDAA ,X
        INX
        STX LPPTR
        LDX LPDEST
        JSR LPDECODEONE
        BCS LPFAIL
        STX LPDEST
        DEC LPLEFT
        BNE LPNEXTCHAR
LPEMPTY CLC
        RTS
; Also usable for a cache miss after a completed glyph when RAM is scarce.
LPDECODEONE STX LPDEST
        JSR HFDECODE
        BCS LPFAIL
        ; Native format 1 expects C,B,A, whereas extraction stores A,B,C.
        ; Keep all channels, including those absent from format-0 graphics.
        LDX LPDEST
        LDAB #31
LPSWAP LDAA ,X
        PSHA
        LDAA 2,X
        STAA ,X
        PULA
        STAA 2,X
        INX
        INX
        INX
        DECB
        BNE LPSWAP
        CLR ,X
        CLR 1,X
        CLR 2,X
        INX
        INX
        INX
        CLC
        RTS
LPFAIL SEC
        RTS
; These two hooks change BASIC text transactions only. Serial graphics and
; BASIC drawings retain their original tile print / row-return behavior.
LPPRINT TST LPMODE
        BEQ LPNATIVEPRINT
        TST LPCOUNT
        BEQ LPNOPRINT
        ; Poll BREAK after each completed glyph, with native stages stopped.
        JSR RFASTBREAK
        BNE LPKEEPPRINTING
        LDAA #8
        STAA GPERROR
        JMP RBABORT
LPKEEPPRINTING LDX LPREAD
        LDAB LPINDEX
        ABX
        LDAA ,X
        JSR LPLOOKUP
        CMPB LPUCOUNT
        BCS LPCACHED
        ; Keep the first keys resident; replace the last slot only. One slot
        ; still works with 316 bytes free, as the old per-glyph path did.
        DECB
        LDX #LPCACHE
        ABX
        STAA ,X
        PSHA
        LDAA #96
        MUL
        ADDD DFLOOR
        STD GXPATPTR
        XGDX
        PULA
        JSR LPDECODEONE
        BCC LPREADYPRINT
        LDAA #7
        STAA GPERROR
        JMP RBABORT
LPCACHED EQU *
        LDAA #96
        MUL
        ADDD DFLOOR
        STD GXPATPTR
LPREADYPRINT INC LPINDEX
LPNATIVEPRINT JMP GPPRINT
LPNOPRINT RTS
LPROW TST LPMODE
        BEQ LPNATIVEROW
        LDAA LPCOLUMN
        ADDA LPCOUNT
        STAA LPCOLUMN
        TST LPREMAIN
        BNE LPNOPRINT
        TST LPSUPPRESS
        BNE LPNOPRINT
        STAA GXNX ; Return the TOTAL line length, not the last buffer width.
        TSTA
        BEQ LPBLANKROW
        JSR GPROW
        BRA LPCLEARED
; Canon's raw carriage move must NOT receive zero: it underflows its count.
; Skip only the carriage half; retain the normal enabled paper-feed sequence.
LPBLANKROW JSR GPROW+24
LPCLEARED EQU *
        CLR LPCOLUMN
        RTS
LPNATIVEROW JMP GPROW
; A=ASCII; returns B=slot and X=key address. B=count means not found.
; Keys survive the native printer workspace; no decompression during motion.
LPLOOKUP LDX #LPCACHE
        CLRB
LPFIND CMPB LPUCOUNT
        BEQ LPLOOKDONE
        CMPA ,X
        BEQ LPLOOKDONE
        INX
        INCB
        BRA LPFIND
LPLOOKDONE RTS
; Physical character count and number of distinct cached glyphs differ.
; Preserve the original limit of eight for the shared graphics driver.
LPLIMIT TST LPMODE
        BEQ LPGRAPHICLIMIT
        CMPB #54
        BRA LPCOUNTLIMIT
LPGRAPHICLIMIT CMPB #8
LPCOUNTLIMIT BLS LPLIMITOK
        JMP RBREJECT
LPLIMITOK JMP LPLIMITNEXT
LPEND EQU *
