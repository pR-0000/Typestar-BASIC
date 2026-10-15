"""Typestar BASIC 0.4.35-dev and 0.4.36-dev token format; NOT for 0.4.34.

Same text protocol, default 31250/7E1 (.48+; older firmware: --baud 1200), line numbers 1..65535, token-aware RAM accounting.
No token bytes are sent over the serial wire. No automatic firmware detection.
"""
import transfer_basic as transport
from tokenized_program import pack, read_source


def validate(data):
    text=data.decode('ascii')
    records=read_source(text)
    pack(records) # Includes record overhead, tokenization and final sentinel.
    lines=[]
    for number,source in records:
        line=f'{number} {source}'.encode('ascii')
        if len(line)>63:
            raise ValueError('Each transferred line must fit 63 ASCII bytes including its number')
        lines.append(line)
    return lines


def main():
    # Reuse the proven transport unchanged, within this explicitly named tool.
    # The standard transfer_basic.py retains its original 1..255 validator.
    transport.validate=validate
    transport.__doc__=__doc__
    transport.main()


if __name__=='__main__':
    try:
        main()
    except (RuntimeError,OSError,ValueError) as exc:
        raise SystemExit('Transfer failed: '+str(exc))
