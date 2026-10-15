; Foreground bridge to a native stage that terminates with RTI.
; Experimental, not linked into a released image; does not start a timer/job.
; Preconditions: I=1, X is a trusted native stage, complete exclusive ownership
; of native mechanical state. NEVER use for a stage that returns with RTS.
;
; JSR already supplies the return PC. Push X,A,B,CCR to complete the canonical
; seven-byte HD6301 interrupt frame: CCR,B,A,XH,XL,PCH,PCL above the final SP.
; Native RTI restores the caller registers and returns past the original JSR.
; Force I=1 in that frame: no accidental native keyboard/SCI interrupts when
; an intermediate timer stage yields. The caller must schedule the next stage
; only after the real peripheral deadline; a successful return is NOT job done.
PRINT_CALL_STAGE PSHX
        PSHA
        PSHB
        TPA
        ORAA #$10
        PSHA
        JMP 0,X
PRINT_CALL_STAGE_END EQU *
