"""Actual-ROM checks for .101's CODE/margin keys and physical X tracking."""
from pathlib import Path
import argparse, hashlib, json, sys, time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'studio/internal'), str(ROOT/'tools')]
from hd6301 import HD6301CPU
from emulator_worker import backend
from rom_images import PROFILES


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',default='head-jog');args=parser.parse_args()
    folder=ROOT/'build'/args.build;image=(folder/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    s=json.loads((folder/'symbols.json').read_text());digest=hashlib.sha256(image).hexdigest()
    PROFILES[digest]='0.4.101'
    old=(ROOT/'build/release-candidate/EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    cases=[];started=time.monotonic()
    # Check registers, flags and ring pointers against the previous helper.
    for axis in (0,32):
        for direction in (0,16):
            for index in range(8):
                machines=[]
                for rom in (old,image):
                    c=HD6301CPU(rom);c.pc=0x7563;c.sp=0x1fff;c.x=0x1234;c.a=0xa5;c.b=0x67;c.c=1
                    c.m[0x41]=axis|direction|0xc0
                    c.putword(0x4e,0x6ee9+index);c.putword(0x50,0x6ef1+index)
                    c.putword(s['JGX'],100);c.push(0xff);c.push(0x3f)
                    for _ in range(100):
                        c.step()
                        if c.pc==0x3fff:break
                    else:raise AssertionError('phase helper did not return')
                    machines.append(c)
                a,b=machines
                assert (a.a,a.b,a.x,a.sp,a.c,a.z,a.n,a.v,a.word(0x4e),a.word(0x50))==(b.a,b.b,b.x,b.sp,b.c,b.z,b.n,b.v,b.word(0x4e),b.word(0x50)),(axis,direction,index)
                assert b.word(s['JGX'])==100+(0 if axis else -1 if direction else 1)
    cases.append(dict(case='64 native phase transitions, registers and flags',pass_count=64))
    print('PASS native phase equivalence',flush=True)
    class MatrixCPU(HD6301CPU):
        def read(self,address):
            if address==0x30:
                row=next((i for i in range(8) if self.m[0x31]==(255^(1<<i))),-1)
                return 255^(1<<(self.raw%8)) if self.raw!=255 and row==self.raw//8 else 255
            if address==0x32:return self.shift
            return super().read(address)
    key_cases=0
    for locale in range(10):
        for mode in (0,1):
            for shift in (0,128):
                for raw in list(range(64))+[255]:
                    outputs=[]
                    for rom in (old,image):
                        k=MatrixCPU(rom);k.raw=raw;k.shift=shift;k.sp=0x1fff;k.pc=s['KBDFAST'];k.a=0x55;k.b=0xa5;k.x=0x3456
                        for name,value in [('KPREV',raw),('KHELD',255),('KLOCALE',locale),('KMODE',mode),('EDWIDTH',31)]:k.m[s[name]]=value
                        k.m[0x19fb]=1;k.push(255);k.push(0x3f)
                        for _ in range(3000):
                            k.step()
                            if k.pc==0x3fff:break
                        else:raise AssertionError(('keyboard return',locale,mode,shift,raw,hex(k.pc)))
                        outputs.append((k.a,k.b,k.x,k.sp,k.m[s['KMODE']],k.m[s['KRAW']],k.m[s['KHELD']],k.m[0x31]))
                    assert outputs[0]==outputs[1],(locale,mode,shift,raw,outputs)
                    key_cases+=1
    cases.append(dict(case='all physical keys, 10 layouts, I/II and Shift unchanged',pass_count=key_cases))
    print('PASS',key_cases,'keyboard mapping comparisons',flush=True)
    C=backend(mask_path=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin',firmware_path=folder/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin')

    def run(c,predicate,limit=5000000):
        for n in range(limit):
            if predicate(c):return n
            c.step()
        raise AssertionError(('timeout',hex(c.pc),c.screen(),c.word(s['JGX']),c.xy))

    def console(c):
        return c.pc==s['GETC'] and not c.input and c.word(c.sp+1)==s['READNEXT']+3

    def command(c,text):
        if c.pc==s['GETC'] and not console(c):
            c.input.append(13);run(c,console)
        c.input.extend(text.encode('ascii')+b'\r');run(c,lambda c:c.pc==s['GETC'] and not c.input)
        return c.screen()

    def release(c):
        c.host_matrix([])
        run(c,lambda c:c.m[s['KHELD']]==255 and not c.matrix_events and c.pc==s['KBDRETURN'])

    def jog(c, direction, target):
        c.host_matrix([0x3b,0x38 if direction<0 else 0x39])
        run(c,lambda c:c.word(s['JGX'])==target and c.pc==s['KBDRETURN'])
        release(c)

    for instant in (False,True):
        c=C();c.allow_errors=True;c.instant_paper=instant
        command(c,'10 PRINT "KEEP"');run(c,console)
        c.input.extend(b'20 PRINT 123');run(c,console)
        pending=bytes(c.m[s['BUF']:s['BUF']+64]);editor=bytes(c.m[s['EDLEN']:s['EDWIN']+1])
        program=bytes(c.m[s['PROGRAM']:c.word(s['PEND'])+1]);crc=c.word(s['RETCRC'])
        start_y=c.xy[1];heat=len(c.paper_events)
        c.host_matrix([0x3b,0x39])
        run(c,lambda c:c.word(s['JGX'])>=96 and c.pc==s['KBDRETURN'])
        c.host_matrix([]);run(c,lambda c:c.m[s['KHELD']]==255 and not c.matrix_events and c.pc==s['KBDRETURN'])
        position=c.word(s['JGX']);assert position>=96 and position%32==0,position
        for _ in range(50000):c.step()
        assert c.word(s['JGX'])==position,'motion continued after release'
        assert c.xy[1]==start_y and len(c.paper_events)==heat
        assert bytes(c.m[s['BUF']:s['BUF']+64])==pending and bytes(c.m[s['EDLEN']:s['EDWIN']+1])==editor
        assert bytes(c.m[s['PROGRAM']:c.word(s['PEND'])+1])==program and c.word(s['RETCRC'])==crc
        c.host_matrix([0x3b,0x38]);run(c,lambda c:c.word(s['JGX'])==0 and c.pc==s['KBDRETURN'])
        for _ in range(50000):c.step()
        assert c.word(s['JGX'])==0
        c.host_matrix([]);run(c,lambda c:c.m[s['KHELD']]==255 and not c.matrix_events and c.pc==s['KBDRETURN'])
        cases.append(dict(case='repeat/release/left bound, editor and program intact',instant=instant,right_phases=position))
        print('PASS keyboard motion, release and preserved editor',instant,flush=True)
        # Every producer must keep the manually chosen start, including its
        # own carriage return. Compare the actual native heating columns.
        for statement in ('LPRINT "AB"','POINT 1,1','LLIST','RUN'):
            printed=[]
            for offset in (0,32):
                m=C();m.allow_errors=True;m.instant_paper=instant
                command(m,'10 LPRINT "AB"' if statement=='RUN' else '10 REM TEST');run(m,console)
                if offset:jog(m,1,offset)
                command(m,statement)
                assert not m.screen().startswith('?'),(statement,m.screen())
                assert m.word(s['JGX'])==offset,(statement,m.word(s['JGX']),m.xy)
                printed.append(list(m.paper_events))
            assert printed[0] and printed[1]==[[x+32,y,w] for x,y,w in printed[0]],statement
            cases.append(dict(case='next print keeps selected origin',producer=statement,instant=instant,columns=len(printed[0])))
        print('PASS text, graphics and listing after manual positioning',instant,flush=True)
        m=C();m.allow_errors=True;m.instant_paper=instant
        for _ in range(9):command(m,'ORIGIN:HEAD 128')
        assert m.word(s['JGX'])==2304
        run(m,console);m.host_matrix([0x3b,0x39])
        for _ in range(50000):m.step()
        assert m.word(s['JGX'])==2304 and not m.paper_events
        release(m)
        assert command(m,'LPRINT "A"').startswith('?PAPER') and not m.paper_events
        command(m,'');run(m,console);jog(m,-1,2272)
        result=command(m,'LPRINT "A"')
        assert not result.startswith('?'),(result,m.word(s['JGX']),m.xy,m.m[s['GPERROR']],m.m[s['GPRAN']],hex(m.word(0x4e)))
        assert m.word(s['JGX'])==2272 and m.paper_events
        cases.append(dict(case='absolute right limit after HEAD; printing bound and recovery',instant=instant))
        print('PASS right limit, print guard and recovery',instant,flush=True)
        n=C();n.allow_errors=True;n.instant_paper=instant
        for _ in range(7):command(n,'ORIGIN:HEAD 128')
        command(n,'ORIGIN:HEAD 112')
        assert n.word(s['JGX'])==2016
        assert command(n,'LPRINT "0123456789";').startswith('?PAPER')
        assert not n.paper_events and n.word(s['JGX'])==2016
        command(n,'');command(n,'DIM G(7):G(0)=255')
        assert command(n,'GLYPH G(0),8,8,4,10').startswith('?PAPER')
        assert not n.paper_events and n.word(s['JGX'])==2016
        command(n,'')
        command(n,'ORIGIN:HEAD 80')
        assert command(n,'DRAW DEFERRED:LINE 0,0,200,16,1:DRAW PRINT').startswith('?PAPER')
        assert not n.paper_events and n.word(s['JGX'])==2176
        command(n,'')
        assert not command(n,'LPRINT "X"').startswith('?'),'failed drawing retained ownership'
        command(n,'ORIGIN 80:HEAD -80')
        assert not command(n,'LPRINT "123456789";').startswith('?')
        assert n.word(s['JGX'])==2304
        command(n,'');run(n,console);jog(n,-1,2272)
        assert not command(n,'LPRINT "A"').startswith('?') and n.word(s['JGX'])==2272
        cases.append(dict(case='whole text/repeat/scene width checked before heat; recovery, exact fit and open-line jog',instant=instant))
        print('PASS whole-band bounds, repeats and open-line positioning',instant,flush=True)
    # Plain margin keys still browse history; CODE+arrows still type < and >.
    c=C();c.allow_errors=True;run(c,console)
    for keys in ([0x38],[0x39],[0x3b]):
        c.host_matrix(keys)
        for _ in range(40000):c.step()
        release(c)
    assert c.word(s['JGX'])==0 and not c.paper_events
    for keys in ([0x3b,0x31],[0x3b,0x32]):
        before=c.m[s['EDLEN']];c.host_matrix(keys)
        run(c,lambda c:c.m[s['EDLEN']]==before+1)
        release(c)
    assert bytes(c.m[s['BUF']:s['BUF']+2])==b'<>'
    cases.append(dict(case='plain margin history, CODE alone and CODE+arrows retained'))
    # Both immediate INPUT and program INKEY must leave motors alone.
    for label,source,text in [('direct INPUT','', 'INPUT A$'),('running INKEY','10 K=INKEY(0):GOTO 10',None)]:
        c=C(source);c.allow_errors=True
        if text:command(c,text)
        else:run(c,lambda c:c.pc==0x8ee6)
        c.host_matrix([0x3b,0x39])
        for _ in range(100000):c.step()
        assert c.word(s['JGX'])==0 and not c.paper_events,label
        cases.append(dict(case='jog excluded from '+label))
    print('PASS other shortcuts and INPUT/RUN exclusion',flush=True)
    c=C('10 DIM A(1145):END');c.allow_errors=True
    run(c,lambda c:c.pc==s['GETC'] and not c.input);command(c,'');run(c,console)
    free=c.word(s['DHEAP'])-c.word(s['DFLOOR']);assert 0<free<220,free
    program=bytes(c.m[s['PROGRAM']:c.word(s['PEND'])+1]);variables=bytes(c.m[c.word(s['DHEAP']):0x3800])
    c.host_matrix([0x3b,0x39])
    for _ in range(100000):c.step()
    assert c.word(s['JGX'])==0 and not c.paper_events
    assert bytes(c.m[s['PROGRAM']:c.word(s['PEND'])+1])==program and bytes(c.m[c.word(s['DHEAP']):0x3800])==variables
    cases.append(dict(case='insufficient motor workspace leaves program and variables intact',free_bytes=free))
    print('PASS low-memory rejection',flush=True)
    report=dict(result='PASS',sha256=digest,cases=cases,seconds=round(time.monotonic()-started,2))
    (folder/'head-jog-validation.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
