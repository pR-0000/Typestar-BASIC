"""Transfer Typestar BASIC programs, USB cable (31250/7E1 by default (.48+; older firmware: --baud 1200)).
Start this tool FIRST, then type LOAD or SAVE on the Canon.
LOAD replaces the current program after handshake; failed loads can be partial.
Limits: firmware 0.4.28+, lines 1..255, 5951 record bytes.
SAVE of older firmware still works; larger LOAD requires updated firmware.
"""
from transfer_messages import tr
import argparse
import time
from pathlib import Path

ACK=b'\x06'
EOT=b'\x04'

def read_byte(port, timeout=8, clock=time.monotonic):
    """Protocol deadline, with the port's short read timeout fixed at open.

    Do not assign port.timeout mid-transfer: pyserial on Windows calls
    SetCommState again, including baud/format/flow control, even for that
    property. A drained OS TX queue is not proof of an idle FTDI shifter.
    """
    deadline=clock()+timeout
    while True:
        received=port.read(1)
        if received:return received
        if clock()>=deadline:return b''

def validate(data):
    text=data.decode('ascii')
    lines=[];seen=set();used=0
    for raw in text.splitlines():
        if not raw.strip():continue
        number,sep,source=raw.strip().partition(' ')
        if not number.isdigit() or not sep or not source or not 1<=int(number)<=255:
            raise ValueError('Each line must be numbered 1..255 followed by BASIC source')
        if int(number) in seen:raise ValueError('Duplicate line number')
        seen.add(int(number))
        line=f'{int(number)} {source}'.encode('ascii')
        if len(line)>63 or any(c<32 or c>126 for c in line):
            raise ValueError('Each input line must contain at most 63 printable ASCII characters')
        used+=len(source)+2
        if used>5951:raise ValueError('Program exceeds the 5951-byte record arena')
        lines.append(line)
    return lines

def link_status(port):
    return tr('CTS={state}, pending TX={count} byte(s)').format(state=tr('READY') if port.cts else tr('BLOCKED'), count=port.out_waiting)

def send_frame(port, data, stage, timeout=10):
    deadline=time.monotonic()+timeout
    while not port.cts:
        if time.monotonic()>=deadline:
            raise RuntimeError(tr('{stage}: Canon RTS#/FTDI CTS remains BLOCKED; no bytes submitted. Check the LCD and CN7 pin 4 signal.').format(stage=stage))
        time.sleep(0.01)
    try:
        written=port.write(data)
        if written!=len(data):raise RuntimeError(tr('Short write: {written}/{size}').format(written=written, size=len(data)))
        while port.out_waiting:
            if time.monotonic()>=deadline:
                raise RuntimeError(tr('Transmit queue did not drain'))
            time.sleep(0.01)
    except (OSError, RuntimeError) as exc:
        raise RuntimeError(f"{stage}: {exc}; {link_status(port)}") from exc

def expect_ack(port, stage=tr("handshake"), timeout=8):
    received=read_byte(port, timeout)
    if received!=ACK:
        detail=tr("timeout (no byte received)") if not received else tr("unexpected byte 0x")+received.hex().upper()
        raise RuntimeError(tr('{stage}: {detail}. {status}. Note the exact Canon LCD message. LOAD may be partial; no automatic retry.').format(stage=stage, detail=detail, status=link_status(port)))

def transfer(port, mode, lines=(), report=None):
    expect_ack(port, tr("Waiting for Canon ready"), timeout=60)
    if report: report("Canon initial ACK received; "+link_status(port))
    send_frame(port, ACK, tr("PC initial ACK"))
    if report: report("PC initial ACK transmit queue drained; "+link_status(port))
    if mode=='load':
        expect_ack(port, tr('Waiting for Canon LOAD-ready (before sending program)'))
        for index,line in enumerate(lines,1):
            send_frame(port, line+b'\r', f'PC program record {index}')
            expect_ack(port, f"LOAD record {index}, BASIC line {line.split()[0].decode()}")
        send_frame(port, EOT, "PC end of program")
        expect_ack(port, "LOAD end acknowledgement")
        send_frame(port, ACK, tr("PC final ACK"))
        return b''
    records=[];line=bytearray()
    while True:
        char=read_byte(port)
        if not char:raise RuntimeError('SAVE timed out; check the Canon screen')
        if char==EOT:
            if line:raise RuntimeError(tr('Incomplete final line'))
            data=b'\n'.join(records)+(b'\n' if records else b'')
            validate(data)
            send_frame(port, ACK, "PC SAVE final ACK")
            return data
        if char==b'\r':
            records.append(bytes(line));line.clear()
            validate(b'\n'.join(records))
            send_frame(port, ACK, "PC SAVE line ACK")
        else:
            if not 32<=char[0]<=126 or len(line)>=66:
                raise RuntimeError('Invalid or oversized SAVE line')
            line.extend(char)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('port',help='COM28, /dev/ttyUSB0 or /dev/cu.usbserial-...')
    p.add_argument('mode',choices=('load','save'))
    p.add_argument('file',type=Path)
    from serial_rates import add_baud_argument
    add_baud_argument(p)
    args=p.parse_args()
    lines=validate(args.file.read_bytes()) if args.mode=='load' else []
    if args.mode=='save' and args.file.exists():p.error(tr('Destination already exists; choose a new filename'))
    import serial
    print(tr('Type {mode} then Return on the Canon now.').format(mode=args.mode.upper()),flush=True)
    if args.mode=='load':print(tr('LOAD replaces the current program.'),flush=True)
    print(tr('Serial: {baud}/7{parity}{stopbits}. Set matching BAUD and SERCFG on Canon.').format(baud=args.baud, parity=args.parity, stopbits=args.stopbits),flush=True)
    with serial.Serial(args.port,args.baud,bytesize=serial.SEVENBITS,
                       parity=args.parity,stopbits=args.stopbits,
                       timeout=0.1,write_timeout=10,rtscts=True,xonxoff=False,dsrdtr=False) as port:
        data=transfer(port,args.mode,lines,report=lambda text: print(text,flush=True))
    if args.mode=='save':
        with args.file.open('xb') as f:f.write(data)
    print(tr('Program transfer acknowledged by the Canon.') if args.mode=='load' else tr('Program saved to ')+str(args.file))

if __name__=='__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError) as exc:
        raise SystemExit(tr("Transfer failed: ")+str(exc))
