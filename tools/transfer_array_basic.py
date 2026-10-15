"""Typestar BASIC 0.4.37+: LOAD/SAVE text, including DIM/RND.

Default 31250 baud (.48+); older firmware: --baud 1200. .45 adds --baud 2400 or 7812 (set BAUD on Canon too).
Firmware .47 also accepts --baud 15625 or 31250.
Default 7E1; .46 adds --parity and --stopbits (set matching SERCFG).
Use transfer_token_basic.py for 0.4.35/0.4.36. Wire format stays ASCII.
"""
import importlib.util
from pathlib import Path
import transfer_token_basic as transfer

spec=importlib.util.spec_from_file_location('_array_token_codec',Path(__file__).with_name('tokenized_program.py'))
codec=importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
assert len(codec.WORDS)==35
codec.WORDS=codec.WORDS+['DIM','RND']
codec.ENCODE['DIM']=0xA3
codec.DECODE[0xA3]='DIM'
codec.ENCODE['RND']=0xA4
codec.DECODE[0xA4]='RND'

def main():
    transfer.pack=codec.pack
    transfer.__doc__=__doc__
    transfer.main()

if __name__=='__main__':
    try:main()
    except (RuntimeError,OSError,ValueError) as exc:
        raise SystemExit('Transfer failed: '+str(exc))
