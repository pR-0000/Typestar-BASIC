"""Correspondant du terminal BASIC : 1200/7E1, un octet puis un ACK."""
import argparse
from collections import deque
from queue import Empty, Queue
from threading import Thread
from time import monotonic
import unicodedata


def ascii_text(text):
    """Les accents deviennent des lettres simples ; les autres signes, ?."""
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
    """Recoit aussi les lignes Canon pendant l'attente d'une saisie PC."""
    pending = deque()
    waiting, closing, cr = True, False, False
    deadline = monotonic() + timeout
    while True:
        data = port.read(1)
        if data:
            b = data[0]
            if b == 6:
                if not waiting:
                    raise RuntimeError("ACK inattendu : relancer la session.")
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
                raise OSError("Octet non transmis ; session interrompue.")
            waiting = True
            deadline = monotonic() + timeout
        if waiting and monotonic() > deadline:
            raise TimeoutError("ACK absent : verifier RUN, cable et reglages.")


def main():
    import sys
    try:
        import serial
    except ImportError:
        raise SystemExit("Installer : python -m pip install pyserial")
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
        print(f"Terminal {args.baud}/7E1 : taper RUN sur la Canon.",
              flush=True)
        print("PC : texte puis Entree. /quit : fermer les deux cotes.")
        Thread(target=keyboard, daemon=True).start()
        converse(port, lines, lambda s: print(s, end="", flush=True))
    print("Session fermee. Canon revenue a 31250/7E1.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, TimeoutError) as exc:
        raise SystemExit(f"{exc}\nCanon : BREAK, puis BAUD 31250.")
    except KeyboardInterrupt:
        raise SystemExit("Interrompu. Canon : BREAK, puis BAUD 31250.")
