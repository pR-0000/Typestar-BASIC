"""Cross-command regressions: INPUT, LCD errors, paper producers and LLIST."""
from pathlib import Path
import argparse,hashlib,json,sys,time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools')]
from emulator_worker import backend
from native_text import encode_source


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',default='release-candidate');args=parser.parse_args()
    folder=ROOT/'build'/args.build;image=folder/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin'
    C=backend(mask_path=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin',firmware_path=image)
    s=C.symbols;cases=[];started=time.monotonic()
    def run(c,limit=8000000,console=False,observe=None):
        for step in range(limit):
            if observe:observe(c)
            if c.pc==s['GETC'] and not c.input and (not console or c.word(c.sp+1)==s['READNEXT']+3):return step
            c.step()
        raise AssertionError(('timeout',hex(c.pc),c.screen()))
    def command(c,text,observe=None):
        if c.pc==s['GETC'] and c.word(c.sp+1)!=s['READNEXT']+3:
            c.input.append(13);run(c,console=True)
        c.input.extend(encode_source(text)+b'\r');run(c,observe=observe)
        return c.screen()
    fixtures=[
        ('numeric INPUT retries empty/text/division/colon',
         '10 A=7:INPUT "N?";A\n20 PRINT A;:END',
         '\rNO\r1/0\r2:3\r12.5\r','12.5'),
        ('empty string INPUT is accepted',
         '10 INPUT A$\n20 PRINT "["+A$+"]";:END','\r','[]'),
        ('string INPUT preserves spaces, quotes and colons',
         '10 INPUT "TEXT?";A$\n20 PRINT "["+A$+"]";:END',
         ' A:B"C \r','[ A:B"C ]'),
    ]
    for label,source,replies,expected in fixtures:
        c=C(source);c.allow_errors=True;c.input.extend(replies.encode('ascii'));run(c)
        assert c.screen()==expected,(label,c.screen(),expected)
        cases.append(dict(case=label,screen=c.screen()))
        print('PASS',label,flush=True)
    c=C();c.allow_errors=True
    command(c,'CURSOR 4:LOCATE 5:PRINT "OLD TEXT";:LCDLINE 5,31')
    result=command(c,'PRINT 1/0')
    assert result.startswith('?DECIMAL MATH') and 'OLD TEXT' not in result,result
    assert c.m[s['CURSORMODE']]==16
    assert command(c,'CLS:PRINT 12;')=='12'
    cases.append(dict(case='LCD clear/default cursor and parser recovery after error',screen=result))
    print('PASS LCD/error recovery',flush=True)
    source='''10 DIM G(65):G(0)=65535:G(1)=32769:G(64)=0:G(65)=0
20 A$="KEEP":B=12.5:DATA 42,"OK"
30 LPRINT "TEST"
40 GLYPH G(0),2,8,5
50 GLYPH G(0),16,2,1
60 DRAW DEFERRED:LINE 0,0,12,12,1:BOX 0,0,12,12,1,0
70 CIRCLE 6,6,3,1,0:DRAW PRINT
80 LPRINT "END"
90 ORIGIN:HEAD 4:HEAD -4:FEED 4:FEED -4:LLOCATE 1,1
100 SOUND 5000,1:READ C,D$
110 PRINT A$;B;C;D$;G(0);:END'''
    c=C(source);c.allow_errors=True;c.instant_paper=True;run(c,20000000)
    assert c.screen()=='KEEP12.542OK65535',c.screen()
    assert c.m[s['SGACTIVE']]==c.m[s['LPMODE']]==c.m[s['GPRAN']]==0
    assert c.word(s['DFLOOR'])<=c.word(s['DHEAP'])
    cases.append(dict(case='font/tile/glyph/scene/motors/sound/DATA preserve variables',
                      jobs=c.jobs,tiles=c.tiles,screen=c.screen()))
    print('PASS mixed graphics, motor, sound and DATA state',flush=True)
    # Exercise shared LIST/SAVE expansion and the independent paper cache.
    # LLIST intentionally substitutes '?' for LCD-only native characters.
    # Native accents enter through LOAD/Studio, rather than the ASCII console
    # key stream. Injection here uses the same native packed record format;
    # release_serial_suite separately verifies the escaped LOAD byte stream.
    c=C('10 PRINT "Été"\n65535 END');c.allow_errors=True;c.instant_paper=True;run(c)
    packed=bytes(c.m[s['PROGRAM']:c.word(s['PEND'])+1]);crc=c.word(s['RETCRC']);lines=[]
    def capture(machine):
        if machine.pc==s['LLPRINT']:
            a=s['LVBUFFER'];lines.append(bytes(machine.m[a:a+machine.m[s['LLEN']]]).decode('ascii'))
    command(c,'LLIST',capture)
    assert lines==['10 PRINT "?t?"','65535 END'],lines
    assert bytes(c.m[s['PROGRAM']:c.word(s['PEND'])+1])==packed and c.word(s['RETCRC'])==crc
    lines.clear();command(c,'LLIST 65535',capture);assert lines==['65535 END'],lines
    jobs=c.jobs;lines.clear();command(c,'LLIST 11,20',capture)
    assert not lines and c.jobs==jobs
    assert command(c,'LLIST 20,10').startswith('?RANGE')
    cases.append(dict(case='LLIST full/single/empty/reversed range and accent fallback',program_unchanged=True))
    print('PASS LLIST ranges, accent fallback and program integrity',flush=True)
    result=dict(result='PASS',sha256=hashlib.sha256(image.read_bytes()).hexdigest(),cases=cases,
                seconds=round(time.monotonic()-started,2))
    dest=ROOT/'build'/('release-audit-'+json.loads((folder/'manifest.json').read_text())['version'].removesuffix('-dev'));dest.mkdir(exist_ok=True)
    (dest/'state.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
