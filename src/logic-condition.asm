; IF now obtains the same decimal boolean/bitwise expression as PRINT/LET.
LXCONDITION JSR CEVAL
        LDX #DW
        JSR CANY
        JMP CBOOL
; A string RHS can itself evaluate a numeric comparison (e.g. STR$(1<2)).
; Keep the outer relation mask on the stack until that expression returns.
LXSTRRIGHT PSHB
        JSR STCAPTURE
        PULA
        STAA CMASK
        RTS
