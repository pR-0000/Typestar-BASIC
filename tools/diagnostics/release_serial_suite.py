"""SCI sessions and full LOAD/SAVE protocol, driven at the peripheral boundary."""
from pathlib import Path
import argparse,hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools')]
from emulator_worker import backend
from core import codec
from native_text import encode_source,escape_wire


def main():
    p=argparse.ArgumentParser();p.add_argument('--build',default='release-candidate');args=p.parse_args()
    folder=ROOT/'build'/args.build;image=folder/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin'
    C=backend(mask_path=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin',firmware_path=image)
    s=C.symbols;cases=[];started=time.monotonic()
    raw=image.read_bytes()
    # Name matching can bypass the historical SBENTRY prefix. Inject at
    # SERIN's actual status read, after its argument has been evaluated.
    receive_pc=raw.index(b'\x96\x11\x85\x40',s['SBENTRY']-0x4000,s['SBEMPTY']-0x4000)+0x4000
    def drain(c,hook=None,console=False,limit=5000000):
        for step in range(limit):
            if c.pc==s['GETC'] and not c.input and (not console or c.word(c.sp+1)==s['READNEXT']+3):return step
            if hook:hook(c)
            c.step()
        raise AssertionError(('serial timeout',hex(c.pc),c.screen(),len(c.rx),bytes(c.tx)))
    def command(c,text,hook=None):
        if c.pc==s['GETC'] and c.word(c.sp+1)!=s['READNEXT']+3:c.input.append(13);drain(c,console=True)
        c.input.extend(encode_source(text)+b'\r');return drain(c,hook)
    def offline(c):
        assert c.m[s['SACTIVE']]==0 and c.m[0x11]&31==0
        assert c.m[0x69]&0x92==0x92 and c.i
    for rate,divider in ((1200,25),(2400,12),(7812,3),(15625,1),(31250,0)):
        for format_,control in (('7N1',0),('7N2',1),('7E1',4),('7E2',5),('7O1',6),('7O2',7)):
            c=C();c.allow_errors=True
            command(c,'SERCFG '+format_);command(c,'SEROPEN '+str(rate))
            assert c.m[s['SACTIVE']]==1 and c.m[0x1c]==divider and c.m[0x1e]&7==control,(rate,format_,c.screen())
            c.tx.clear();command(c,'SEROUT 127');assert bytes(c.tx)==b'\x7f'
            command(c,'CLS:PRINT SERIN(0);');assert c.screen()=='-1',c.screen()
            for value in (0,65,127):
                injected=[]
                def receive(m,v=value):
                    if m.pc==receive_pc and not injected:m.rx.append(v);injected.append(True)
                command(c,'CLS:PRINT SERIN(0);',receive)
                assert injected and c.screen()==str(value),(rate,format_,value,c.screen())
            command(c,'SERCLOSE');offline(c)
            cases.append(dict(case='session',baud=rate,format=format_,divider=divider))
        print('PASS SCI session formats',rate,flush=True)
    records=[(1,'REM SERIAL'),(256,'PRINT "Été"'),(300,'REM '+('A'*55)),(65535,'END')]
    packed=codec.pack(records)
    lines=[escape_wire(encode_source(f'{n} {body}'))+b'\r' for n,body in records]
    for mode in ('LOAD','SAVE'):
        c=C();c.allow_errors=True
        if mode=='SAVE':
            c.m[s['PROGRAM']:s['PROGRAM']+len(packed)]=packed;c.putword(s['PEND'],s['PROGRAM']+len(packed)-1)
        c.tx.clear();received=[]
        incoming=b'\x06'+b''.join(lines)+b'\x04\x06' if mode=='LOAD' else b'\x06'*(len(records)+2)
        def feed(m):
            if m.pc==s['SRXBYTE'] and not received:m.rx.extend(incoming);received.append(True)
        steps=command(c,mode,feed);offline(c)
        assert received and not c.screen().startswith('?'),(mode,c.screen())
        if mode=='LOAD':
            assert bytes(c.m[s['PROGRAM']:c.word(s['PEND'])+1])==packed
            assert bytes(c.tx)==b'\x06'*(len(records)+3),bytes(c.tx)
        else:assert bytes(c.tx)==b'\x06'+b''.join(lines)+b'\x04',bytes(c.tx)
        cases.append(dict(case=mode,steps=steps,records=len(records),native_accents=True,maximum_line_bytes=63))
        print('PASS full protocol',mode,flush=True)
    for label,data,prefix in [('bad initial ACK',b'X','?BAD ACK'),
            ('incomplete final line',b'\x0610 PRINT 1\x04','?RX TEXT'),
            ('oversized line',b'\x06'+b'1 REM '+b'A'*59+b'\r','?RX TEXT'),
            ('unquoted native byte',b'\x0610 PRINT \x1bA\r','?')]:
        c=C();c.allow_errors=True;c.tx.clear();injected=[]
        def feed(m):
            if m.pc==s['SRXBYTE'] and not injected:m.rx.extend(data);injected.append(True)
        command(c,'LOAD',feed);assert c.screen().startswith(prefix),(label,c.screen());offline(c)
        cases.append(dict(case=label,error=c.screen(),closed=True))
    for label in ('RX timeout','TX timeout','BREAK during RX','parity error'):
        c=C();c.allow_errors=True;injected=[]
        if label=='TX timeout':c.tx_ready=False
        def failure(m):
            if m.pc==s['SRXBYTE'] and not injected:
                if label=='BREAK during RX':m.matrix_keys={0x36}
                if label=='parity error':m.m[0x1e]|=16
                injected.append(True)
        steps=command(c,'LOAD',failure);offline(c)
        assert c.screen().startswith('?'),(label,c.screen())
        cases.append(dict(case=label,error=c.screen(),closed=True,steps=steps))
        print('PASS serial failure cleanup',label,c.screen(),flush=True)
    result=dict(result='PASS',sha256=hashlib.sha256(image.read_bytes()).hexdigest(),cases=cases,seconds=round(time.monotonic()-started,2))
    dest=ROOT/'build'/('release-audit-'+json.loads((folder/'manifest.json').read_text())['version'].removesuffix('-dev'));dest.mkdir(exist_ok=True)
    (dest/'serial.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
