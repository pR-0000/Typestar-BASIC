; S70 BASIC 0.2.2 - HD6301, a09 OPT H01. Original implementation.
; Experimental exclusive RAM ownership; no Canon calls after mask-ROM startup.
; Polling keyboard/LCD/SCI. No motor or printer services invoked.
        OPT H01
PROGRAM EQU $1000
BUF     EQU $1900
VARS    EQU $1940
CUR     EQU $1980
SAVE    EQU $1982
KEY     EQU $1984
DEST    EQU $1986
VALUE   EQU $1988
TEMP    EQU $198A
TOTAL   EQU $198C
OP      EQU $198E
SIGN    EQU $198F
RUNNING EQU $1990
LINE    EQU $1991
COUNT   EQU $1992
DIGIT   EQU $1993
STARTED EQU $1994
OVER    EQU $1995
        ORG $6800
BOOT    SEI
        LDS #$1FFF
        CLR $11
        CLR $1E
        CLR $1B
        LDAA #$19
        STAA $1C
        LDAA #$10
        STAA $1B
        LDAA #$24
        STAA $10
        LDAA #$06
        STAA $1E
        LDX #$1000
SETTLE  DEX
        BNE SETTLE
        LDAA #$0A
        STAA $11
        LDAA $1E
        LDAA $12
        LDAA $03
        ANDA #$7D
        STAA $03
        JSR CONSOLEINIT
        JSR CLEARALL
        LDX #BANNER
        JSR PUTS
READY   LDS #$1FFF
        CLR RUNNING
        LDX #PROMPT
        JSR PUTS
        JSR READLINE
        LDX #BUF
        STX CUR
        JSR SPACE
        TSTA
        BEQ READY
        CMPA #$30
        BCS DIRECT
        CMPA #$39
        BHI DIRECT
        JSR NUMBER
        JSR CHECKLINE
        STAB LINE
        JSR SPACE
        JSR SLOT
        STX DEST
COPY    LDX CUR
        LDAA ,X
        INX
        STX CUR
        LDX DEST
        STAA ,X
        INX
        STX DEST
        TSTA
        BNE COPY
        BRA READY
DIRECT  JSR EXECUTE
        BRA READY

; Console: A character, B/X preserved. TX timeout cannot block local console.
PUTC    PSHA
        PSHB
        PSHX
        JSR LCDPUT
        LDX #$2000
TXWAIT  LDAA $11
        BITA #$20
        BNE TXSEND
        DEX
        BNE TXWAIT
        BRA TXDONE
TXSEND  PULX
        PULB
        PULA
        STAA $13
        RTS
TXDONE  PULX
        PULB
        PULA
        RTS
GETC    JSR POLLIN
        TSTA
        BEQ GETC
        RTS
; Nonblocking result A=0 means no byte. ASCII NUL is ignored.
POLLIN  LDAA $11
        BITA #$C0
        BEQ POLLKEY
        BITA #$40
        BNE RXERROR
        LDAA $1E
        LDAA $12
        RTS
RXERROR LDAA $1E
        LDAA $12
        JMP IOERROR
POLLKEY JMP KBDPOLL
PUTS    LDAA ,X
        BEQ PUTSEND
        JSR PUTC
        INX
        BRA PUTS
PUTSEND RTS
CRLF    LDAA #13
        JSR PUTC
        LDAA #10
        JMP PUTC
READLINE LDX #BUF
        CLR OVER
READNEXT JSR GETC
        CMPA #3
        BNE READCR
        JMP BREAK
READCR  CMPA #13
        BEQ READDONE
        CMPA #10
        BEQ READNEXT
        CMPA #8
        BEQ BACKSPACE
        CMPA #127
        BEQ BACKSPACE
        CMPA #32
        BCS READNEXT
        CMPA #126
        BHI READNEXT
        TST OVER
        BNE READNEXT
        CPX #BUF+63
        BNE READSTORE
        INC OVER
        BRA READNEXT
READSTORE STAA ,X
        INX
        JSR PUTC
        BRA READNEXT
BACKSPACE TST OVER
        BNE READNEXT
        CPX #BUF
        BEQ READNEXT
        DEX
        LDAA #8
        JSR PUTC
        LDAA #32
        JSR PUTC
        LDAA #8
        JSR PUTC
        BRA READNEXT
READDONE CLR ,X
        JSR CRLF
        TST OVER
        BEQ READOK
        JMP LONGERROR
READOK  RTS

; Whitespace and keyword matching. CUR points to next unconsumed byte.
SPACE   LDX CUR
SPACE1  LDAA ,X
        CMPA #32
        BEQ SPACE2
        CMPA #9
        BNE SPACE3
SPACE2  INX
        BRA SPACE1
SPACE3  STX CUR
        RTS
UPPER   CMPA #$61
        BCS UPPEROK
        CMPA #$7A
        BHI UPPEROK
        SUBA #32
UPPEROK RTS
MATCH   STX KEY
        LDX CUR
        STX SAVE
MATCH1  LDX KEY
        LDAB ,X
        BEQ MATCHEND
        INX
        STX KEY
        LDX CUR
        LDAA ,X
        JSR UPPER
        STAB TEMP
        CMPA TEMP
        BNE MATCHNO
        INX
        STX CUR
        BRA MATCH1
MATCHEND LDX CUR
        LDAA ,X
        JSR UPPER
        CMPA #$41
        BCS MATCHYES
        CMPA #$5A
        BLS MATCHNO
MATCHYES CLC
        RTS
MATCHNO LDX SAVE
        STX CUR
        SEC
        RTS
EOS     JSR SPACE
        TSTA
        BEQ EOSOK
        JMP SYNTAX
EOSOK   RTS

EXECUTE JSR SPACE
        TSTA
        BEQ EXECRET
        LDX #KPRINT
        JSR MATCH
        BCS TRYLOCATE
        JMP PRINT
TRYLOCATE LDX #KLOCATE
        JSR MATCH
        BCS TRYCLS
        JMP LOCATE
TRYCLS  LDX #KCLS
        JSR MATCH
        BCS TRYLET
        JMP CLS
TRYLET  LDX #KLET
        JSR MATCH
        BCS TRYREM
        JMP LET
TRYREM  LDX #KREM
        JSR MATCH
        BCC EXECRET
        LDX #KRUN
        JSR MATCH
        BCS TRYLIST
        JMP RUN
TRYLIST LDX #KLIST
        JSR MATCH
        BCS TRYNEW
        JMP LIST
TRYNEW  LDX #KNEW
        JSR MATCH
        BCS TRYGOTO
        JMP NEW
TRYGOTO LDX #KGOTO
        JSR MATCH
        BCS TRYIF
        JMP GOTO
TRYIF   LDX #KIF
        JSR MATCH
        BCS TRYEND
        JMP IF
TRYEND  LDX #KEND
        JSR MATCH
        BCS TRYHELP
        JSR EOS
        CLR RUNNING
EXECRET RTS
TRYHELP LDX #KHELP
        JSR MATCH
        BCS TRYKEYS
        JSR EOS
        LDX #HELPMSG
        JMP PUTS
TRYKEYS LDX #KKEYS
        JSR MATCH
        BCS BARELET
        JMP KEYDIAG
BARELET JMP LET

; Signed 16-bit values; + and - wrap modulo 65536. No recursion.
LET     JSR VARADDR
        STX DEST
        JSR SPACE
        CMPA #$3D
        BEQ LETEQ
        JMP SYNTAX
LETEQ   INX
        STX CUR
        JSR EXPR
        STD VALUE
        JSR EOS
        LDD VALUE
        LDX DEST
        STD ,X
        RTS
VARADDR JSR SPACE
        JSR UPPER
        CMPA #$41
        BCS BADVAR
        CMPA #$5A
        BHI BADVAR
        INX
        STX CUR
        SUBA #$41
        TAB
        ASLB
        LDX #VARS
        ABX
        RTS
BADVAR  JMP SYNTAX
EXPR    JSR ATOM
        STD TOTAL
EXPRNEXT JSR SPACE
        CMPA #$2B
        BEQ EXPROP
        CMPA #$2D
        BNE EXPRDONE
EXPROP  STAA OP
        INX
        STX CUR
        JSR ATOM
        STD TEMP
        LDAA OP
        CMPA #$2D
        BEQ EXPRSUB
        LDD TOTAL
        ADDD TEMP
        BRA EXPRSET
EXPRSUB LDD TOTAL
        SUBD TEMP
EXPRSET STD TOTAL
        BRA EXPRNEXT
EXPRDONE LDD TOTAL
        RTS
ATOM    CLR SIGN
        JSR SPACE
        CMPA #$2D
        BNE ATOMPLUS
        INC SIGN
        BRA ATOMSKIP
ATOMPLUS CMPA #$2B
        BNE ATOMBODY
ATOMSKIP INX
        STX CUR
        JSR SPACE
ATOMBODY CMPA #$30
        BCS ATOMVAR
        CMPA #$39
        BHI ATOMVAR
        JSR NUMBER
        BRA ATOMSIGN
ATOMVAR JSR VARADDR
        LDD ,X
ATOMSIGN TST SIGN
        BEQ ATOMRET
        STD TEMP
        LDD #0
        SUBD TEMP
ATOMRET RTS
NUMBER  LDD #0
        STD VALUE
NUMLOOP LDX CUR
        LDAA ,X
        CMPA #$30
        BCS NUMDONE
        CMPA #$39
        BHI NUMDONE
        SUBA #$30
        STAA DIGIT
        LDD VALUE
        SUBD #6553
        BCS NUMSAFE
        BNE NUMBAD
        LDAA DIGIT
        CMPA #5
        BHI NUMBAD
NUMSAFE LDD VALUE
        ASLD
        STD TEMP
        ASLD
        ASLD
        ADDD TEMP
        STD VALUE
        CLRA
        LDAB DIGIT
        ADDD VALUE
        STD VALUE
        INX
        STX CUR
        BRA NUMLOOP
NUMDONE LDD VALUE
        RTS
NUMBAD  JMP RANGEERROR

PRINT   JSR SPACE
        TSTA
        BNE PRINTITEM
        JMP CRLF
PRINTITEM CMPA #$22
        BNE PRINTNUM
        INX
PRINTSTR LDAA ,X
        BNE STRNONUL
        JMP SYNTAX
STRNONUL CMPA #$22
        BEQ STREND
        JSR PUTC
        INX
        BRA PRINTSTR
STREND  INX
        STX CUR
        BRA PRINTSEP
PRINTNUM JSR EXPR
        JSR OUTNUM
PRINTSEP JSR SPACE
        TSTA
        BNE PRINTMORE
        JMP CRLF
PRINTMORE CMPA #$3B
        BEQ PRINTSEMI
        CMPA #$2C
        BEQ PRINTCOMMA
        JMP SYNTAX
PRINTCOMMA LDAA #32
        JSR PUTC
PRINTSEMI INX
        STX CUR
        JSR SPACE
        TSTA
        BNE PRINTITEM
        RTS
OUTNUM  STD VALUE
        TSTA
        BPL OUTPOS
        LDAA #$2D
        JSR PUTC
        LDD #0
        SUBD VALUE
        STD VALUE
OUTPOS  CLR STARTED
        LDX #DIVISORS
OUTDIG  LDAA #$30
        STAA DIGIT
OUTSUB  LDD VALUE
        SUBD ,X
        BCS OUTEMIT
        STD VALUE
        INC DIGIT
        BRA OUTSUB
OUTEMIT LDAA DIGIT
        CMPA #$30
        BNE OUTYES
        TST STARTED
        BNE OUTYES
        CPX #DIVISORS+8
        BNE OUTSKIP
OUTYES  JSR PUTC
        INC STARTED
OUTSKIP INX
        INX
        CPX #DIVISORS+10
        BNE OUTDIG
        RTS

; 32 fixed slots of 64 bytes; source line number 1..32 maps to slot.
CHECKLINE TSTA
        BNE BADLINE
        TSTB
        BEQ BADLINE
        CMPB #32
        BHI BADLINE
        RTS
BADLINE JMP RANGEERROR
SLOT    LDAB LINE
        DECB
        CLRA
        ASLD
        ASLD
        ASLD
        ASLD
        ASLD
        ASLD
        ADDD #PROGRAM
        STD TEMP
        LDX TEMP
        RTS
CLEARALL LDX #PROGRAM
CLEARP  CLR ,X
        INX
        CPX #$1800
        BNE CLEARP
CLEARVARS LDX #VARS
CLEARV  CLR ,X
        INX
        CPX #VARS+52
        BNE CLEARV
        RTS
DIRECTONLY TST RUNNING
        BEQ DIRECTOK
        JMP MODEERROR
DIRECTOK RTS
NEW     JSR DIRECTONLY
        JSR EOS
        JMP CLEARALL
LIST    JSR DIRECTONLY
        JSR EOS
        LDAA #1
        STAA LINE
LISTNEXT JSR SLOT
        LDAA ,X
        BEQ LISTSKIP
        CLRA
        LDAB LINE
        JSR OUTNUM
        LDAA #32
        JSR PUTC
        JSR SLOT
        JSR PUTS
        JSR CRLF
LISTSKIP INC LINE
        LDAA LINE
        CMPA #33
        BNE LISTNEXT
        RTS
RUN     JSR DIRECTONLY
        JSR EOS
        JSR CLEARVARS
        LDAA #1
        STAA RUNNING
        STAA LINE
RUNNEXT JSR POLLIN
        CMPA #3
        BNE RUNSLOT
        JMP BREAK
RUNSLOT JSR SLOT
        STX CUR
        JSR EXECUTE
        TST RUNNING
        BEQ RUNRET
        INC LINE
        LDAA LINE
        CMPA #33
        BNE RUNNEXT
        CLR RUNNING
RUNRET  RTS
GOTO    JSR EXPR
        STD VALUE
        JSR EOS
        LDD VALUE
        JSR CHECKLINE
        TST RUNNING
        BNE GOTOINRUN
        JMP MODEERROR
GOTOINRUN STAB LINE
        JSR SLOT
        TST ,X
        BNE GOTOVALID
        JMP UNDEFINED
GOTOVALID DEC LINE
        RTS
; IF uses nonzero truth, THEN requires a line target, even for false IF.
IF      JSR EXPR
        STD DEST
        LDX #KTHEN
        JSR MATCH
        BCC IFTHEN
        JMP SYNTAX
IFTHEN  JSR EXPR
        STD VALUE
        JSR EOS
        LDD VALUE
        JSR CHECKLINE
        TST RUNNING
        BNE IFMODEOK
        JMP MODEERROR
IFMODEOK LDX DEST
        BEQ IFRET
        BRA GOTOINRUN
IFRET   RTS

SYNTAX  LDX #MSYNTAX
        BRA ERROR
RANGEERROR LDX #MRANGE
        BRA ERROR
MODEERROR LDX #MMODE
        BRA ERROR
UNDEFINED LDX #MUNDEF
        BRA ERROR
LONGERROR LDX #MLONG
        BRA ERROR
IOERROR LDX #MIO
        BRA ERROR
BREAK   LDX #MBREAK
ERROR   LDS #$1FFF
        JSR PUTS
        JMP READY
; ABI slots deliberately trap; this is NOT a Canon-compatible service ABI.
TRAP    SEI
        BRA TRAP

DIVISORS FDB 10000,1000,100,10,1
BANNER  FCC "S70 BASIC 0.2.2 / LCD KBD SERIAL"
        FCB 13,10,0
PROMPT  FCC "READY> "
        FCB 0
HELPMSG FCC "PRINT LET RUN LIST NEW GOTO IF expr THEN line END REM HELP"
        FCB 13,10
        FCC "A-Z: signed 16 bit, + -; lines 1..32, 63 chars; CTRL-C breaks"
        FCB 13,10,0
MSYNTAX FCC "?SYNTAX"
        FCB 13,10,0
MRANGE  FCC "?RANGE"
        FCB 13,10,0
MMODE   FCC "?MODE"
        FCB 13,10,0
MUNDEF  FCC "?UNDEFINED LINE"
        FCB 13,10,0
MLONG   FCC "?LINE TOO LONG"
        FCB 13,10,0
MIO     FCC "?SERIAL ERROR"
        FCB 13,10,0
MBREAK  FCC "?BREAK"
        FCB 13,10,0
KLOCATE FCC "LOCATE"
        FCB 0
KCLS    FCC "CLS"
        FCB 0
KPRINT  FCC "PRINT"
        FCB 0
KLET    FCC "LET"
        FCB 0
KREM    FCC "REM"
        FCB 0
KRUN    FCC "RUN"
        FCB 0
KLIST   FCC "LIST"
        FCB 0
KNEW    FCC "NEW"
        FCB 0
KGOTO   FCC "GOTO"
        FCB 0
KIF     FCC "IF"
        FCB 0
KTHEN   FCC "THEN"
        FCB 0
KEND    FCC "END"
        FCB 0
KHELP   FCC "HELP"
        FCB 0
        INCLUDE "src/lcd-position.inc"
        INCLUDE "src/console.inc"
        INCLUDE "src/keymaps.inc"
CODEEND EQU *
        END
