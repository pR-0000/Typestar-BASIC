; Blocking BASIC sound, known ASIC gate only. Global IRQ remains masked.
; Rate labels refer to envelope modulation, not the ~5.89 kHz carrier.
; Delays reuse hardware-tried recipes; polling/IRQ changes need recalibration.
SNDLEFT EQU $19EB ; input duration, then remaining full cycles, word
SNDDELAY EQU $19ED ; half-period delay loop count, word
SNDSTEP EQU $19EF ; period-interpolation bias (7 or 17)
SNDMODE EQU $19F0 ; 0 continuous, 1 modulated, 2 silence
SNDHZ EQU $19F1 ; nominal modulation rate, 100 for plain beep/pause
SNDWIDE EQU $19F3 ; low word of 24-bit arithmetic accumulator
SNDHIGH EQU $19F5 ; upper byte
SNDDIVISOR EQU $19F6 ; positive 16-bit divisor
KBEEP FCC "BEEP"
        FCB 0
KSOUND FCC "SOUND"
        FCB 0
SOUNDDISPATCH LDX #KBEEP
        JSR MATCH
        BCS TRYSOUND
        JMP BASICBEEP
TRYSOUND LDX #KSOUND
        JSR MATCH
        BCS NOTSOUND
        JMP BASICSOUND
NOTSOUND JMP $440C
BASICBEEP CLR SNDMODE
        LDD #100
        STD SNDHZ
        JSR SPACE
        TSTA
        BNE SNDDURATION
        LDD #100
        BRA SNDVALIDATE
BASICSOUND JSR EXPR
        STD SNDHZ
        SUBD #0
        BEQ SNDSILENCE
        SUBD #60
        BCS SNDBADNEAR
        SUBD #690
        BHI SNDBADNEAR
        LDAA #1
        BRA SNDSET
SNDSILENCE LDD #100
        STD SNDHZ
        LDAA #2
SNDSET STAA SNDMODE
        JSR SPACE
        CMPA #44
        BEQ SNDCOMMA
        JMP SYNTAX
SNDCOMMA INX
        STX CUR
SNDDURATION JSR EXPR
SNDVALIDATE STD SNDLEFT
        SUBD #2000
        BHI SNDBADNEAR
        JSR EOS
        LDD SNDLEFT
        BNE SNDPREP
        JMP SNDSTOP
SNDBADNEAR JMP RANGEERROR
; Integer interpolation in period (1/f), matching the validated delay counts
; exactly at 100/200/400. Acoustic timing still requires recalibration.
SNDPREP LDD SNDHZ
        STD SNDDIVISOR
        SUBD #200
        BHI SNDHIGHBAND
        LDD #48864       ; 114400 = 65536 + 48864
        STD SNDWIDE
        LDAA #7
        BRA SNDBIAS
SNDHIGHBAND LDD #50864   ; 116400 = 65536 + 50864
        STD SNDWIDE
        LDAA #17
SNDBIAS STAA SNDSTEP
        LDAA #1
        STAA SNDHIGH
        JSR SNDDIV
        STX SNDDELAY
        CLRA
        LDAB SNDSTEP
        STD VALUE
        LDD SNDDELAY
        SUBD VALUE
        STD SNDDELAY
; Full cycles = ceil(rate * duration_ms / 1000). Use bounded 24-bit
; arithmetic: the product can exceed 65535 (750 * 2000 = 1500000).
        CLR SNDHIGH
        LDD #0
        STD SNDWIDE
        LDX SNDLEFT
SNDPRODUCT LDD SNDWIDE
        ADDD SNDHZ
        STD SNDWIDE
        BCC SNDNOCARRY
        INC SNDHIGH
SNDNOCARRY DEX
        BNE SNDPRODUCT
        LDD SNDWIDE
        ADDD #999
        STD SNDWIDE
        BCC SNDROUNDOK
        INC SNDHIGH
SNDROUNDOK LDD #1000
        STD SNDDIVISOR
        JSR SNDDIV
        STX SNDLEFT
SNDLOOP LDAA SNDMODE
        CMPA #2
        BEQ SNDQUIET
        LDAA #$40
        BRA SNDSTART
SNDQUIET CLRA
SNDSTART JSR SNDGATE
        JSR SNDWAIT
        LDAA SNDMODE
        CMPA #1
        BNE SNDSECOND
        CLRA
        JSR SNDGATE
SNDSECOND JSR SNDWAIT
        ; Sound waits already space samples: avoid the editor debounce delay.
        ; No serial or motor service is enabled during this command.
        JSR KBDFAST
        CMPA #3
        BEQ SNDBREAK
        LDD SNDLEFT
        SUBD #1
        STD SNDLEFT
        BEQ SNDSTOP
        BRA SNDLOOP
SNDSTOP CLRA
        JMP SNDGATE
SNDBREAK CLRA
        JSR SNDGATE
        JMP BREAK
SNDWAIT LDX SNDDELAY
SNDWAITLOOP DEX
        BNE SNDWAITLOOP
        RTS
; A=0 or $40. Use shadow, never read the mixed ASIC hardware register.
; Keep hardware and shadow coherent, preserving all non-buzzer bits.
SNDGATE TAB
        LDAA $1801
        ANDA #$BF
        TSTB
        BEQ SNDGATEWRITE
        ORAA #$40
SNDGATEWRITE STAA $1801
        STAA $34
        RTS

; Bounded 24/16 division by repeated subtraction, quotient X.
; Largest quotient < 2000 in the validated input range. No signed math.
SNDDIV LDX #0
SNDDIVLOOP LDD SNDWIDE
        SUBD SNDDIVISOR
        BCC SNDDIVSTORE
        TST SNDHIGH
        BEQ SNDDIVDONE
        DEC SNDHIGH
SNDDIVSTORE STD SNDWIDE
        INX
        BRA SNDDIVLOOP
SNDDIVDONE RTS
