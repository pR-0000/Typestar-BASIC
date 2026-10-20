"""Typestar BASIC keyboard peer: framed native codes over 7E1.

Monitoring is the default. --type explicitly enables output to the focused
application. The serial loop is independent of the optional pynput backend.
"""
import argparse
from pathlib import Path
import sys
from time import monotonic, sleep

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from native_text import LCD_TO_UNICODE
from serial_rates import BAUD_RATES

HELLO = b'KB2\r'
PROTOCOLS = {b'KB1\r': 1, HELLO: 2}
ACK = b'\x06'
EOT = b'\x04'
SPECIAL = {8: 'backspace', 9: 'tab', 13: 'enter',
           18: 'left', 19: 'right', 20: 'up', 21: 'down', 127: 'delete'}
MESSAGES = {
    'fr': {
        'description': 'Clavier distant Typestar BASIC (moniteur par défaut).',
        'port': 'Port indiqué dans Studio : COM28, /dev/ttyUSB0…',
        'type': 'Écrire dans la fenêtre active après le délai de préparation.',
        'monitor': 'Afficher les codes sans écrire dans une autre application.',
        'baud': 'Débit de B à la ligne 20 du BASIC (défaut : 31250).',
        'delay': 'Secondes pour choisir la fenêtre cible (défaut : 5).',
        'serial_missing': 'Installer : python -m pip install pyserial',
        'keyboard_missing': 'Installer : python -m pip install pynput',
        'backend': 'Clavier système indisponible : {error}',
        'waiting': 'Liaison {baud}/7E1. Tapez RUN sur la Canon.',
        'select': 'Clavier prêt. Cliquez dans la fenêtre cible : activation dans {delay:g} s.',
        'active': 'Actif. Arrêt propre : revenez ici puis Ctrl+C. BREAK interrompt aussi la Canon.',
        'monitoring': 'Mode MONITEUR : codes affichés ici uniquement. Pour écrire dans Studio ou une autre application, relancez avec --type.',
        'legacy': 'Ancien programme KB1 : compatible, mais rechargez le nouveau BASIC KB2 pour accélérer la frappe.',
        'timeout': 'Délai dépassé : vérifiez RUN, le câble et le débit.',
        'hello': 'Programme inattendu : chargez remote-keyboard, puis tapez RUN.',
        'frame': 'Trame clavier invalide : session arrêtée.',
        'write': 'Octet non transmis : session arrêtée.',
        'ignored': 'ignoré',
        'backspace': 'Retour arrière', 'tab': 'Tabulation', 'enter': 'Entrée',
        'left': 'Gauche', 'right': 'Droite', 'up': 'Haut', 'down': 'Bas',
        'delete': 'Supprimer',
        'closed': 'Session fermée. Canon revenue à 31250/7E1.',
        'recover': 'Canon : BREAK, puis BAUD 31250 avant un transfert Studio.',
        'failed': 'Échec : {error}',
        'interrupted': 'Interrompu.',
        'bad_delay': 'Le délai doit être compris entre 0 et 60 secondes.',
    },
    'en': {
        'description': 'Typestar BASIC remote keyboard (monitor by default).',
        'port': 'Port shown in Studio: COM28, /dev/ttyUSB0…',
        'type': 'Type in the focused window after the preparation delay.',
        'monitor': 'Display codes without typing in another application.',
        'baud': 'B at BASIC line 20 (default: 31250).',
        'delay': 'Seconds to select the target window (default: 5).',
        'serial_missing': 'Install: python -m pip install pyserial',
        'keyboard_missing': 'Install: python -m pip install pynput',
        'backend': 'System keyboard unavailable: {error}',
        'waiting': 'Serial {baud}/7E1. Type RUN on the Canon.',
        'select': 'Keyboard ready. Click the target window: activation in {delay:g} s.',
        'active': 'Active. To close cleanly, return here and press Ctrl+C. BREAK also stops the Canon.',
        'monitoring': 'MONITOR mode: codes appear here only. To type in Studio or another application, restart with --type.',
        'legacy': 'Older KB1 program: supported, but load the new KB2 BASIC program for faster typing.',
        'timeout': 'Timed out: check RUN, the cable and baud rate.',
        'hello': 'Unexpected program: load remote-keyboard, then type RUN.',
        'frame': 'Invalid keyboard frame: session stopped.',
        'write': 'Byte not transmitted: session stopped.',
        'ignored': 'ignored',
        'backspace': 'Backspace', 'tab': 'Tab', 'enter': 'Enter',
        'left': 'Left', 'right': 'Right', 'up': 'Up', 'down': 'Down',
        'delete': 'Delete',
        'closed': 'Session closed. Canon restored to 31250/7E1.',
        'recover': 'Canon: BREAK, then BAUD 31250 before a Studio transfer.',
        'failed': 'Failed: {error}',
        'interrupted': 'Interrupted.',
        'bad_delay': 'The delay must be between 0 and 60 seconds.',
    },
}


class ProtocolError(RuntimeError):
    pass


def action_for(code):
    """Map translated INKEY values, never raw KEYS/matrix positions."""
    if code in SPECIAL:
        return 'key', SPECIAL[code]
    if 32 <= code <= 126:
        return 'text', chr(code)
    if code in LCD_TO_UNICODE:
        return 'text', LCD_TO_UNICODE[code]
    return None


def read_exact(port, count, timeout, message, clock=monotonic):
    deadline = None if timeout is None else clock() + timeout
    data = bytearray()
    while len(data) < count:
        part = port.read(count - len(data))
        if part:
            data.extend(part)
        if len(data) < count and deadline is not None and clock() >= deadline:
            raise TimeoutError(message)
    return bytes(data)


def send(port, data, message):
    if port.write(data) != len(data):
        raise OSError(message)


def read_key(port, messages, protocol=2, pending=None):
    # Idle is unlimited; a packet that has started must finish promptly.
    # The caller keeps partial input so Ctrl+C can close at a frame boundary.
    pending = bytearray() if pending is None else pending
    if not pending:
        pending.extend(read_exact(port, 1, None, messages['timeout']))
    deadline = monotonic() + 5
    while len(pending) < (2 if protocol == 2 else 4):
        pending.extend(read_exact(port, 1, max(0, deadline - monotonic()),
                                  messages['timeout']))
    first, tail = bytes(pending[:1]), bytes(pending[1:])
    pending.clear()
    if protocol == 2:
        if first not in (b'@', b'A'):
            raise ProtocolError(messages['frame'])
        if tail[0] > 127:
            raise ProtocolError(messages['frame'])
        return (first[0] - 64) * 128 + tail[0]
    if (first != b'\x02' or tail[2:] != b'\x03' or
            any(b not in b'0123456789ABCDEF' for b in tail[:2])):
        raise ProtocolError(messages['frame'])
    return int(tail[:2], 16)


def close_session(port, messages, protocol=2, pending=None):
    """EOT ends either protocol; drain whole pending packets before final ACK."""
    send(port, EOT, messages['write'])
    deadline = monotonic() + 3
    if pending:
        read_exact(port, (2 if protocol == 2 else 4) - len(pending),
                   max(0, deadline - monotonic()), messages['timeout'])
        pending.clear()
    # A key packet already in flight may precede the final ACK.
    while monotonic() < deadline:
        first = port.read(1)
        if first == ACK:
            return
        # A KB2 payload may itself be ACK. It is data, not the closing reply.
        count = (1 if protocol == 2 and first in (b'@', b'A') else
                 3 if protocol == 1 and first == b'\x02' else 0)
        if count:
            read_exact(port, count, max(0, deadline - monotonic()),
                       messages['timeout'])
    raise TimeoutError(messages['timeout'])


class SystemKeyboard:
    def __init__(self, module):
        self.controller = module.Controller()
        self.keys = module.Key

    def emit(self, action):
        if action is None:
            return
        kind, value = action
        key = getattr(self.keys, value) if kind == 'key' else value
        # Every received event is a complete tap; no remote key is held down.
        try:
            self.controller.press(key)
        finally:
            self.controller.release(key)


def main(language='en', argv=None):
    m = MESSAGES[language]
    parser = argparse.ArgumentParser(description=m['description'])
    parser.add_argument('port', help=m['port'])
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--type', action='store_true', help=m['type'])
    modes.add_argument('--monitor', action='store_true', help=m['monitor'])
    parser.add_argument('--baud', type=int, choices=BAUD_RATES, default=31250,
                        help=m['baud'])
    parser.add_argument('--start-delay', type=float, default=5, help=m['delay'])
    args = parser.parse_args(argv)
    if not 0 <= args.start_delay <= 60:
        parser.error(m['bad_delay'])
    try:
        import serial
    except ImportError:
        raise SystemExit(m['serial_missing'])
    keyboard = None
    if args.type:
        try:
            from pynput import keyboard as keyboard_module
        except ImportError as error:
            raise SystemExit(m['backend'].format(error=error) + '\n' +
                             m['keyboard_missing'])
        try:
            keyboard = SystemKeyboard(keyboard_module)
        except Exception as error:
            raise SystemExit(m['backend'].format(error=error))

    session = closed = False
    protocol = 2
    pending = bytearray()
    try:
        with serial.Serial(args.port, args.baud, bytesize=serial.SEVENBITS,
                           parity=serial.PARITY_EVEN,
                           stopbits=serial.STOPBITS_ONE, timeout=0.1,
                           write_timeout=2, rtscts=True) as port:
            port.reset_input_buffer()
            print(m['waiting'].format(baud=args.baud), flush=True)
            try:
                hello = read_exact(port, len(HELLO), 60, m['timeout'])
                if hello not in PROTOCOLS:
                    raise ProtocolError(m['hello'])
                protocol = PROTOCOLS[hello]
                session = True
                if protocol == 1:
                    print(m['legacy'], flush=True)
                if keyboard:
                    print(m['select'].format(delay=args.start_delay), flush=True)
                    sleep(args.start_delay)
                print(m['active'] if keyboard else m['monitoring'], flush=True)
                send(port, ACK, m['write'])
                while True:
                    code = read_key(port, m, protocol, pending)
                    action = action_for(code)
                    if keyboard:
                        try:
                            keyboard.emit(action)
                        except Exception as error:
                            raise RuntimeError(m['backend'].format(error=error)) from error
                    else:
                        label = (m[action[1]] if action and action[0] == 'key'
                                 else repr(action[1]) if action else m['ignored'])
                        print(f'{code:3d} / 0x{code:02X} : {label}', flush=True)
                    if protocol == 1:
                        send(port, ACK, m['write'])
            finally:
                if session:
                    original_error = sys.exc_info()[0] is not None
                    try:
                        close_session(port, m, protocol, pending)
                        closed = True
                    except (OSError, RuntimeError, TimeoutError):
                        if not original_error:
                            raise
    except KeyboardInterrupt:
        print(m['interrupted'], flush=True)
        if closed:
            print(m['closed'], flush=True)
        else:
            print(m['recover'], flush=True)
    except (OSError, RuntimeError, TimeoutError, ValueError) as error:
        raise SystemExit(m['failed'].format(error=error) + '\n' +
                         (m['closed'] if closed else m['recover']))


if __name__ == '__main__':
    main()
