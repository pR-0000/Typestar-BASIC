# Workshop - A paper terminal for conversation

The Canon receives a computer message and keeps it on paper. Prepare a reply on its keyboard, review it on the LCD, then Return sends it back. With the serial cable, the machine becomes a little **paper terminal**.

This example uses **line mode**, allowing corrections before sending. Other terminals transmit every key immediately; the application determines that choice. Here, we favour a simple conversation in sentences. [T1]

## Preparing both ends

Both files are in **examples/terminal**: [terminal-en.bas](../../../examples/terminal/terminal-en.bas) for the Canon and [terminal_pc_en.py](../../../examples/terminal/terminal_pc_en.py) for the computer. The BASIC program uses the firmware described in this manual.

1. Open **terminal-en.bas** in **Typestar BASIC Studio**, then **Send → LOAD** with the usual **31250 / 7E1** settings. Wait for completion.
2. Prepare a sheet, preferably thermal paper. Leave the Canon at `>`.
3. Open a computer terminal in the project folder and run the command below, replacing COM28 with Studio's port.
4. Type **RUN**, then Return on the Canon. The display shows `> `: conversation is open.

```text
python examples/terminal/terminal_pc_en.py COM28
```

On Linux or macOS, use **python3** if needed and your port name, such as `/dev/ttyUSB0` or `/dev/cu.usbserial-...`. The script uses **pySerial**, also used by Studio. If your selected Python needs it, install with:

```text
python -m pip install pyserial
```

Conversation begins at **1200 baud, 7E1**: seven data bits, even parity and one stop bit. BASIC sets this format at startup; the computer script applies matching values. [T2]

## Your first conversation

On the computer, type **HELLO FROM THE COMPUTER** and Enter. The message prints on the sheet. On the Canon, type **HELLO FROM TYPESTAR**: letters appear on the LCD. **Backspace** removes the last letter. **Return** sends the reply to the computer window.

The LCD shows prefix `> ` and **30 reply characters**, filling its 32 positions. A held key counts as one press; release it before repeating the same letter. Ordinary ASCII signs are accepted. A short beep signals a full reply or an unsupported key.

Canon letters wait for Return, allowing review. Replies end with **CR then LF**, two common line-ending codes. Received computer text prints; the local reply stays on the LCD until sent.

| Received by the Canon | Paper result |
|---|---|
| ASCII text | Courier 10 letters, digits and punctuation. |
| CR or LF | Ends the line and advances paper. |
| CR followed by LF | One line ending. |
| Tab | Spaces to the next eight-column stop. |
| More than 72 characters | Continues on the next paper line. |

The Python peer simplifies computer-message accents: **café** becomes **cafe**, **Noël** becomes **Noel**, **œuf** becomes **oeuf**. A sign without an equivalent becomes `?`. This is the terminal program's rule; LLIST has its own replacement rule in the paper chapter.

To finish, type **/quit** and Enter on the computer. Pending text prints, both ends close the connection and Canon displays **TERMINAL CLOSED**. It restores **31250 / 7E1** for Studio transfers.

**MARGIN RELEASE / BREAK** also stops the program. After this, type `BAUD 31250` before the next Studio transfer.

## Why does the computer wait for confirmation?

BASIC checks received characters between instructions. Printing takes time. To match these rhythms, the computer sends **one byte**, then waits for **ACK**, code 6, before the next. Canon also confirms initial readiness.

Received text is prepared in **36-character groups**, a chosen buffer size. While printing a group, the program temporarily closes the serial session, then reopens it before ACK. The computer waits. LPRINT's semicolon keeps groups on the same paper line; advance occurs at a line ending or 72 columns.

The keyboard is checked **between print batches**. Prepare your reply while the head is stationary so keystrokes are read. The computer peer continues receiving replies while you prepare another sentence.

Rate and character format are standard; **this example's dialogue requires acknowledgements**. Another peer must follow the same rule. Continuous streams, ANSI cursor controls or a direct remote-system connection would need fuller firmware reception management.

## Reading the BASIC program

Lines **100-230** alternate reception and keyboard reading. B$ stores the local reply. Subroutines **500** and **600** handle Return and Backspace; **900** prepares the LCD.

From **1000**, received characters and line endings are recognised. R$ stores the next print group; C counts columns. **2000** and **2100** print, then restore communication. Special code **4**, sent by /quit, goes to **3000** for a clean finish.

<!-- terminal-basic:start -->
```basic
10 REM PAPER TERMINAL - 1200 BAUD 7E1
20 B=1200:SERCFG 7E1:LSPACING 1.5
30 B$="":R$="":C=0:D=0:H=0
40 GOSUB 900:SEROPEN B:SEROUT 6
100 A=SERIN(0)
110 IF A>=0 THEN GOSUB 1000
120 K=INKEY(0)
130 IF K=0 THEN H=0:GOTO 100
140 IF K=H THEN 100
150 H=K
160 IF K=13 THEN GOSUB 500:GOTO 100
170 IF K=8 THEN GOSUB 600:GOTO 100
180 IF K<32 THEN 100
190 IF K>126 THEN BEEP 20:GOTO 100
200 IF LEN(B$)=30 THEN BEEP 20:GOTO 100
210 B$=B$+CHR$(K)
220 LOCATE 1,LEN(B$)+2:PRINT CHR$(K);
230 GOTO 100
500 N=LEN(B$):IF N=0 THEN 540
510 FOR I=1 TO N
520 SEROUT ASC(MID$(B$,I,1))
530 NEXT I
540 SEROUT 13:SEROUT 10
550 B$="":GOSUB 900:RETURN
600 IF LEN(B$)=0 THEN RETURN
610 LOCATE 1,LEN(B$)+2:PRINT " ";
620 B$=LEFT$(B$,LEN(B$)-1):RETURN
900 CLS:CURSOR 0:PRINT "> ";:RETURN
1000 IF A=4 THEN 3000
1010 IF A=10 AND D=13 THEN D=0:GOTO 1150
1020 IF A=13 THEN GOSUB 2000:D=13:GOTO 1150
1030 IF A=10 THEN GOSUB 2000:D=0:GOTO 1150
1040 D=0
1050 IF A=9 THEN GOSUB 1300:GOTO 1150
1060 IF A<32 OR A>126 THEN 1150
1070 GOSUB 1400
1150 SEROUT 6:RETURN
1300 T=8-(C MOD 8):A=32
1310 FOR J=1 TO T:GOSUB 1400:NEXT J
1320 RETURN
1400 IF C=72 THEN GOSUB 2000
1410 R$=R$+CHR$(A):C=C+1
1420 IF LEN(R$)=36 THEN GOSUB 2100
1430 RETURN
2000 SERCLOSE
2010 IF LEN(R$)>0 THEN LPRINT R$;
2020 R$="":LPRINT:C=0
2030 SEROPEN B:RETURN
2100 SERCLOSE:LPRINT R$;
2110 R$="":SEROPEN B:RETURN
3000 IF C>0 THEN GOSUB 2000
3010 SEROUT 6:SERCLOSE:BAUD 31250
3020 CLS:CURSOR 0:PRINT "TERMINAL CLOSED":END
```
<!-- terminal-basic:end -->

## The little Python peer

The script reads the port and waits for acknowledgements. A second thread waits for computer keyboard lines, allowing a Canon reply to appear while you prepare the next one. pySerial handles the port and format. [T2]

<!-- terminal-python:start -->
```python
"""BASIC terminal peer: 1200/7E1, one byte then one ACK."""
import argparse
from collections import deque
from queue import Empty, Queue
from threading import Thread
from time import monotonic
import unicodedata


def ascii_text(text):
    """Simplify accents to plain letters; replace other signs with ?."""
    text = text.translate(str.maketrans({
        "\u0153": "oe", "\u0152": "OE", "\u00e6": "ae", "\u00c6": "AE",
        "\u00df": "ss", "\u2019": "'", "\u2018": "'", "\u201c": '"',
        "\u201d": '"', "\u2013": "-", "\u2014": "-",
    }))
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    data = text.encode("ascii", "replace")
    return bytes(b if b == 9 or 32 <= b <= 126 else 63 for b in data)


def converse(port, lines, emit, timeout=60):
    """Receive Canon lines while waiting for computer input."""
    pending = deque()
    waiting, closing, cr = True, False, False
    deadline = monotonic() + timeout
    while True:
        data = port.read(1)
        if data:
            b = data[0]
            if b == 6:
                if not waiting:
                    raise RuntimeError("Unexpected ACK: restart the session.")
                waiting = False
            elif b == 13:
                emit("\n")
                cr = True
            elif b == 10:
                if not cr:
                    emit("\n")
                cr = False
            elif 32 <= b <= 126 or b == 9:
                emit(chr(b))
                cr = False
        if closing and not pending and not waiting:
            return
        if not pending and not closing:
            try:
                text = lines.get_nowait()
                closing = text is None or text == "/quit"
                pending.extend(b"\x04" if closing else
                               ascii_text(text) + b"\r\n")
            except Empty:
                pass
        if pending and not waiting:
            if port.write(bytes([pending.popleft()])) != 1:
                raise OSError("Byte not sent; session interrupted.")
            waiting = True
            deadline = monotonic() + timeout
        if waiting and monotonic() > deadline:
            raise TimeoutError("Missing ACK: check RUN, cable and settings.")


def main():
    import sys
    try:
        import serial
    except ImportError:
        raise SystemExit("Install: python -m pip install pyserial")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port",
                        help="COM28, /dev/ttyUSB0, /dev/cu.usbserial...")
    parser.add_argument("--baud", type=int, default=1200,
                        choices=[1200, 2400, 7812, 15625, 31250])
    args = parser.parse_args()
    lines = Queue()
    def keyboard():
        for text in sys.stdin:
            lines.put(text.rstrip("\r\n"))
        lines.put(None)
    with serial.Serial(args.port, args.baud, bytesize=serial.SEVENBITS,
                       parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE,
                       timeout=0.05, write_timeout=60, rtscts=True) as port:
        port.reset_input_buffer()
        print(f"Terminal {args.baud}/7E1: type RUN on the Canon.",
              flush=True)
        print("Computer: text then Enter. /quit: close both ends.")
        Thread(target=keyboard, daemon=True).start()
        converse(port, lines, lambda s: print(s, end="", flush=True))
    print("Session closed. Canon restored to 31250/7E1.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, TimeoutError) as exc:
        raise SystemExit(f"{exc}\nCanon: BREAK, then BAUD 31250.")
    except KeyboardInterrupt:
        raise SystemExit("Interrupted. Canon: BREAK, then BAUD 31250.")
```
<!-- terminal-python:end -->

## Your turn to modify it

Change the LCD prefix at line **900**, or spacing at **20**. For another rate, change **B=1200** at line 20 and run the peer with the same value, for example `--baud 2400`. Retain 7E1 and ACKs at both ends.

Emulator tests check the program, Python peer and dialogue with only one occupied reception slot at a time. A first test on your Canon checks the cable, actual keyboard pace and printing.

[T1]: https://ftp.gnu.org/old-gnu/Manuals/glibc/html_node/Canonical-or-Not.html
[T2]: https://pyserial.readthedocs.io/en/latest/pyserial_api.html
