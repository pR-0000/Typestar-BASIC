; LCD is attached before retained-program validation, after native startup.
; No artificial delay: verification owns the message until it returns.
CXBOOT LDX #CXBOOTMSG
        JSR PUTS
        JSR $4403
        JMP UICLEAR
; @island load
CXLOAD LDX #CXLOADMSG
        JSR PUTS
        JMP SERIALINIT
; @island bootmsg
CXBOOTMSG FCC "BOOTING"
        FCB 0
; @island loadmsg
CXLOADMSG FCC "LOADING"
        FCB 13,0
