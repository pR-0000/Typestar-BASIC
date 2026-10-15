; X points to the existing error string. RLINE is the current physical BASIC
; line (16 bits), retained across colons, INPUT and native printer calls.
; Direct errors must not display the stale line left by LIST or a previous RUN.
ERLINE JSR PUTS
        TST RUNNING
        BEQ ERLINERET
        LDAA #32
        JSR PUTC
        LDAA #64
        JSR PUTC
        LDD RLINE
        JMP OUTNUM
ERLINERET RTS
; @island number
; OUTNUM now has only nonnegative callers: boot/MEM sizes and line numbers.
; Reuse LIST's unsigned formatter; support all line numbers through 65535.
ERUNSIGNED JSR RFORMAT
        CLR ,X
        LDX #LBUFFER
        JMP PUTS
