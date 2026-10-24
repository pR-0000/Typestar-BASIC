"""Actual editor, capacity, CRC and reset-retention tests for a release ROM."""
from pathlib import Path
import argparse,binascii,hashlib,json,random,sys,time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools')]
from emulator_worker import backend
from core import codec
from native_text import encode_source
from machine import GenericMachine


def main():
    p=argparse.ArgumentParser();p.add_argument('--build',default='paper-grid');args=p.parse_args()
    folder=ROOT/'build'/args.build;image=(folder/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    mask=(ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin').read_bytes()
    C=backend(mask_path=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin',firmware_path=folder/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin')
    c=C();c.allow_errors=True;s=c.symbols;records={};rng=random.Random(221026);cases=[];started=time.monotonic()
    def wait(console=False,limit=3000000):
        for _ in range(limit):
            if c.pc==s['GETC'] and not c.input and (not console or c.word(c.sp+1)==s['READNEXT']+3):return
            c.step()
        raise AssertionError(('editor timeout',hex(c.pc),c.screen()))
    def command(text):
        if c.pc==s['GETC'] and c.word(c.sp+1)!=s['READNEXT']+3:c.input.append(13);wait(True)
        c.input.extend(encode_source(text)+b'\r');wait();return c.screen()
    def verify():
        packed=codec.pack(sorted(records.items()));end=s['PROGRAM']+len(packed)-1
        assert c.word(s['PEND'])==end,(c.word(s['PEND']),end)
        assert bytes(c.m[s['PROGRAM']:end+1])==packed
        assert c.word(s['RETMAGIC'])==0x5424
        assert c.word(s['RETCRC'])==binascii.crc_hqx(packed,0xffff)
        assert c.word(s['DFLOOR'])<=c.word(s['DHEAP'])<=0x3800
        return packed
    for n in (65535,1,32768,255,256,32767):
        body='REM LINE '+str(n);command(f'{n} {body}');records[n]=body;verify()
    for i in range(90):
        n=rng.choice(list(records)) if records and i%3==0 else rng.randrange(1,65536)
        if i%5==0:
            command(str(n));records.pop(n,None)
        else:
            body='REM '+''.join(rng.choice('ABCDE :"') for _ in range(rng.randrange(1,32)))
            command(f'{n} {body}');records[n]=body
        verify()
    cases.append(dict(case='random insert/replace/delete',edits=96,bytes=len(verify())))
    print('PASS random editor edits, sorted 16-bit records and CRC',flush=True)
    for text in ('0 REM ZERO','65536 REM OVERFLOW'):
        before=verify();result=command(text)
        assert result.startswith('?'),(text,result)
        assert verify()==before
    cases.append(dict(case='invalid line numbers are atomic',count=2))
    command('NEW');records.clear();verify()
    n=10000
    while True:
        body='REM '+('Z'*53)
        proposed=records|{n:body}
        if len(codec.pack(sorted(proposed.items()),capacity=65536))>s['PROGRAMEND']-s['PROGRAM']+1:break
        result=command(f'{n} {body}');assert not result.startswith('?'),result
        records[n]=body;n+=1
    full=verify();result=command(f'{n} {body}')
    assert result.startswith('?PROGRAM FULL'),result
    assert verify()==full
    # A longer replacement must fail before deleting the old record.
    first=min(records);records[first]='REM X';command(f'{first} REM X');verify()
    small=20000
    while len(codec.pack(sorted((records|{small:'REM X'}).items()),capacity=65536))<=s['PROGRAMEND']-s['PROGRAM']+1:
        command(f'{small} REM X');records[small]='REM X';small+=1
    verify();full=verify();first=min(records)
    result=command(f'{first} '+body)
    assert result.startswith('?PROGRAM FULL'),result
    assert verify()==full
    command('CLEAR');assert verify()==full
    cases.append(dict(case='full arena and failed growth are atomic',bytes=len(full),free=c.word(s['DHEAP'])-c.word(s['DFLOOR'])))
    print('PASS near-full RAM, failed insertion/growth, CLEAR and CRC',flush=True)
    # Run the real reset path with an ideal mechanical bus, no PC-based motor
    # shortcut. Stop at the first BASIC welcome wait, after retention validation.
    bootcases=[]
    for label,damage,fill,serial in [('valid',None,0,False),('valid-ff',None,255,True),
            ('bad-crc',5,165,False),('bad-record',0,165,True),('missing-signature',None,90,False)]:
        b=GenericMachine(image,mask,mechanics=True)
        b.m[0x1803:0x3800]=bytes([fill])*(0x3800-0x1803)
        b.m[s['PROGRAM']:s['PROGRAM']+len(full)]=full
        b.m[s['RETMAGIC']:s['RETMAGIC']+4]=bytes(c.m[s['RETMAGIC']:s['RETMAGIC']+4])
        b.m[0x36]=2
        if damage is not None:b.m[s['PROGRAM']+damage]^=1
        if label=='missing-signature':b.m[s['RETMAGIC']]=0
        if serial:b.rx.extend(b'noise');b.tx_ready=False;b.m[0x11]=0xff
        for step in range(4000000):
            if b.pc==s['GETC']:break
            b.step()
        else:raise AssertionError(('reset timeout',label,hex(b.pc)))
        kept=bytes(b.m[s['PROGRAM']:b.word(s['PEND'])+1])
        expected=full if label.startswith('valid') else b'\0'
        assert kept==expected,(label,len(kept),len(expected))
        assert b.m[0x36]==0 and b.m[0x11]&0x1f==0
        assert b.word(s['RETMAGIC'])==0x5424
        assert b.word(s['RETCRC'])==binascii.crc_hqx(expected,0xffff)
        bootcases.append(dict(case=label,steps=step,kept_bytes=len(kept),mechanical_irqs=b.irq_counts))
        print('PASS reset',bootcases[-1],flush=True)
    result=dict(result='PASS',sha256=hashlib.sha256(image).hexdigest(),cases=cases,boots=bootcases,seconds=round(time.monotonic()-started,2))
    dest=ROOT/'build'/('release-audit-'+json.loads((folder/'manifest.json').read_text())['version'].removesuffix('-dev'));dest.mkdir(exist_ok=True)
    (dest/'memory.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
