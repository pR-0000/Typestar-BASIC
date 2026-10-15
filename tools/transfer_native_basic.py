"""Typestar BASIC .83+: UTF-8 source, native LCD strings, escaped 7-bit LOAD/SAVE.
Earlier firmware accepts ASCII only; accented sources require .83 or later.
"""
from transfer_messages import tr
import transfer_basic as transport
from native_program import read_source,pack
from native_text import encode_source,decode_source,escape_wire

def validate(data):
    records=read_source(data.decode('utf-8-sig'));pack(records)
    lines=[]
    for number,source in records:
        line=encode_source(f'{number} {source}')
        if len(line)>63:raise ValueError(tr('Line exceeds 63 native bytes including its number'))
        lines.append(line)
    return lines

def transfer(port,mode,lines=(),report=None):
    t=transport
    t.expect_ack(port,tr('Waiting for Canon ready'),timeout=60)
    t.send_frame(port,t.ACK,tr('PC initial ACK'))
    if mode=='load':
        t.expect_ack(port,tr('Waiting for Canon LOAD-ready'))
        for index,line in enumerate(lines,1):
            t.send_frame(port,escape_wire(line)+b'\r',tr('LOAD record {index}').format(index=index))
            t.expect_ack(port,tr('LOAD record {index}').format(index=index))
        t.send_frame(port,t.EOT,tr('LOAD end'));t.expect_ack(port,tr('LOAD end ACK'))
        t.send_frame(port,t.ACK,tr('PC final ACK'));return b''
    records=[];line=bytearray()
    while True:
        char=t.read_byte(port)
        if not char:raise RuntimeError(tr('SAVE timeout'))
        escaped=char==b'\x1b'
        if escaped:
            low=t.read_byte(port)
            if not low or low[0]>127:raise RuntimeError(tr('Truncated/invalid native escape'))
            char=bytes((low[0]|128,))
        if not escaped and char==t.EOT:
            if line:raise RuntimeError(tr('Incomplete final line'))
            data=('\n'.join(records)+('\n' if records else '')).encode('utf-8')
            validate(data);t.send_frame(port,t.ACK,tr('SAVE final ACK'));return data
        if not escaped and char==b'\r':
            records.append(decode_source(line));line.clear()
            validate('\n'.join(records).encode('utf-8'))
            t.send_frame(port,t.ACK,tr('SAVE line ACK'))
        else:
            if (not escaped and not 32<=char[0]<=126) or len(line)>=63:raise RuntimeError(tr('Invalid/oversized SAVE line'))
            line.extend(char)

def main():
    transport.validate=validate;transport.transfer=transfer;transport.__doc__=__doc__
    transport.main()
if __name__=='__main__':
    try:main()
    except (RuntimeError,OSError,ValueError) as exc:raise SystemExit(tr('Transfer failed: ')+str(exc))
