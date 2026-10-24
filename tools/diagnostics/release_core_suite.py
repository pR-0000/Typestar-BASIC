"""Public-language regression tests against the selected, unmodified BASIC ROM.

Commands pass through the real line editor/parser. Program-control fixtures
use the same packed records as Studio. No arithmetic/parser routines are
replaced with Python; the ordinary functional keyboard/timer bus is retained.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys,time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'studio/internal'),str(ROOT/'tools')]
from emulator_worker import backend
from native_text import encode_source


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',default='paper-grid');args=ap.parse_args()
    folder=ROOT/'build'/args.build;image=folder/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin'
    C=backend(mask_path=ROOT.parent.parent/'ROMReader/dumps/dump_hd6301_v3_fast_1.bin',firmware_path=image)
    c=C();c.allow_errors=True;s=c.symbols;cases=[];failures=[];started=time.monotonic()
    def drain(machine,limit=2500000,console=False):
        for steps in range(limit):
            if (machine.pc==s['GETC'] and not machine.input and
                (not console or machine.word(machine.sp+1)==s['READNEXT']+3)):return steps
            machine.step()
        raise AssertionError(('timeout',hex(machine.pc),machine.screen()))
    def command(text):
        if c.pc==s['GETC'] and c.word(c.sp+1)!=s['READNEXT']+3:
            c.input.append(13);drain(c,console=True)
        c.input.extend(encode_source(text)+b'\r');steps=drain(c)
        return c.screen(),steps
    def check(label,action):
        try:
            evidence=action();cases.append(dict(case=label,evidence=evidence))
        except Exception as error:
            failures.append(dict(case=label,error=str(error)));print('FAIL',label,str(error),flush=True)
            # Restore the actual console stack and let later independent cases run.
            c.input.clear();c.pc=s['READY'];drain(c,console=True)
    def exact(text,want):
        before=bytes(c.m[s['PROGRAM']:c.word(s['PEND'])+1])
        result,steps=command(text)
        assert result==want,(text,result,want)
        assert bytes(c.m[s['PROGRAM']:c.word(s['PEND'])+1])==before,('program modified',text)
        assert c.word(s['DFLOOR'])<=c.word(s['DHEAP'])<=0x3800
        return dict(screen=result,steps=steps)
    values=[('0.1+0.2','0.3'),('1/8','0.125'),('12.5*2','25'),
        ('-2^2','-4'),('(-2)^2','4'),('2^3^2','512'),('2+3*4','14'),
        ('(2+3)*4','20'),('2^-3','0.125'),('ABS(-12.5)','12.5'),
        ('SGN(-0.25)','-1'),('SGN(0)','0'),('SGN(0.25)','1'),
        ('INT(-1.2)','-2'),('FIX(-1.2)','-1'),('INT(1.9)','1'),('FIX(1.9)','1'),
        ('SQR(0)','0'),('SQR(144)','12'),('PI','3.1415927'),
        ('17 MOD 5','2'),('-17 MOD 5','-2'),('17 MOD -5','2'),('-17 MOD -5','-2'),
        ('-32768 MOD -1','0'),('65535 MOD 256','255'),
        ('NOT 0','-1'),('NOT -1','0'),('65535 AND 255','255'),
        ('32768 OR 1','-32767'),('5 AND 3','1'),('5 OR 3','7'),
        ('1<2','-1'),('1>2','0'),('1<=1','-1'),('2>=3','0'),('2<>3','-1'),
        ('NOT 1=1','0'),('1=1 AND 2=2','-1'),('1=2 OR 2=2','-1'),
        ('%101010','42'),('&HFFFF','65535'),('(&H8000 OR 1)','-32767'),
        ('LEN("")','0'),('LEN("ABC")','3'),('ASC("A")','65'),
        ('LEN(CHR$(0))','1'),('ASC(CHR$(255))','255'),('VAL("-12.5")','-12.5'),
        ('LEN(STR$(12.5))','4'),('INKEY(0)','0')]
    for expr,want in values:check(expr,lambda e=expr,w=want:exact('CLS:PRINT '+e+';',w))
    for expr,want in [('LEFT$("ABCDE",2)','AB'),('RIGHT$("ABCDE",2)','DE'),
        ('MID$("ABCDE",2,3)','BCD'),('MID$("ABCDE",3)','CDE'),
        ('"["+LEFT$("ABCDE",0)+"]"','[]'),('RIGHT$("ABCDE",8)','ABCDE'),
        ('"ABC"+"DEF"','ABCDEF'),('STR$(-0.125)','-0.125')]:
        check(expr,lambda e=expr,w=want:exact('CLS:PRINT '+e+';',w))
    for expr,expected,tolerance in [('SIN(PI/6)',.5,.00001),('COS(PI)',-1,.00001),
        ('SIN(-PI/2)',-1,.00001),('TAN(PI/4)',1,.0001),('ATN(1)',math.pi/4,.0001),
        ('LOG(1)',0,.00001),('LOG(2)',math.log(2),.0001),('EXP(0)',1,.00001),
        ('EXP(1)',math.e,.0001),('LOG(EXP(.5))',.5,.0001),('2^0.5',math.sqrt(2),.0001),
        ('SIN(PI/6)^2+COS(PI/6)^2',1,.0001)]:
        def approximate(e=expr,want=expected,tol=tolerance):
            result,steps=command('CLS:PRINT '+e+';');assert abs(float(result)-want)<=tol,(result,want,tol)
            return dict(screen=result,expected=want,tolerance=tol,steps=steps)
        check(expr,approximate)
    for expr,prefix in [('1/0','?DECIMAL MATH'),('SQR(-1)','?'),('LOG(0)','?'),
        ('LOG(-1)','?'),('1 MOD 0','?'),('1.5 MOD 1','?RANGE'),('NOT .5','?RANGE'),
        ('1 AND .1','?RANGE'),('RND(0)','?RANGE'),('CHR$(256)','?RANGE'),
        ('ASC("")','?RANGE'),('MID$("ABC",0,1)','?RANGE'),('ABS()','?'),
        ('(1+2','?'),('1+','?'),('FOO(1)','?'),('PEEK(1.5)','?RANGE')]:
        def rejected(e=expr,p=prefix):
            old=bytes(c.m[s['PROGRAM']:c.word(s['PEND'])+1]);_,steps=command('CLS:PRINT '+e+';')
            assert c.screen().startswith(p),(e,c.screen(),p)
            assert bytes(c.m[s['PROGRAM']:c.word(s['PEND'])+1])==old
            error=c.screen();exact('CLS:PRINT 7+5;','12')
            return dict(error=error,recovered=True,steps=steps)
        check('error/recovery '+expr,rejected)
    programs=[
      ('colon/GOSUB','10 A=1:GOSUB 100:A=A+10:PRINT A;:END\n100 A=A+2:RETURN','13'),
      ('FOR fractional','10 A=0:FOR I=.5 TO 2 STEP .5:A=A+I:NEXT I\n20 PRINT A;:END','5'),
      ('FOR negative','10 A=0:FOR I=3 TO 1 STEP -1:A=A+I:NEXT\n20 PRINT A;:END','6'),
      ('FOR empty','10 A=0:FOR I=3 TO 1:A=A+1:NEXT I\n20 PRINT A;:END','0'),
      ('nested FOR','10 A=0:FOR I=1 TO 3:FOR J=1 TO 2:A=A+I*J\n20 NEXT J:NEXT I\n30 PRINT A;:END','18'),
      ('IF true ELSE','10 IF 1 THEN A=2:A=A+3 ELSE A=9\n20 PRINT A;:END','5'),
      ('IF false ELSE','10 IF 0 THEN A=2:A=A+3 ELSE A=9:A=A+1\n20 PRINT A;:END','10'),
      ('IF quoted colon','10 IF "A:B"="A:B" THEN PRINT "YES"; ELSE PRINT "NO";\n20 END','YES'),
      ('REM tokens','10 A=1:REM ELSE PRINT BAD\n20 PRINT A;:END','1'),
      ('DATA/RESTORE','10 DATA -2.5,"A:B",%1010\n20 READ A,B$,C:RESTORE:READ D\n30 PRINT A;B$;C;D;:END','-2.5A:B10-2.5'),
      ('array 1D/2D','10 DIM A(3):DIM B(2,2):A(3)=12.5:B(2,2)=-.5\n20 PRINT A(3)+B(2,2);:END','12'),
      ('array DATA','10 DIM A(1):DATA 4,5\n20 READ A(0),A(1):PRINT A(0)+A(1);:END','9'),
      ('string assignments and numeric array stay bounded',
       '10 DIM A(3):FOR I=1 TO 100:A$=STR$(I):B$=A$+":"+A$\n20 A(I MOD 4)=I:NEXT I\n30 PRINT B$;A(0);:END','100:100100'),
      ('random seed is repeatable and values lie in [0,1)',
       '10 RANDOMIZE 123:A=RND(1):B=RND(1):RANDOMIZE 123\n20 PRINT A=RND(1);B=RND(1);A>=0 AND A<1;:END','-1-1-1'),
      ('eight nested FOR levels',
       '10 FOR A=1 TO 1:FOR B=1 TO 1:FOR C=1 TO 1\n20 FOR D=1 TO 1:FOR E=1 TO 1:FOR F=1 TO 1\n30 FOR G=1 TO 1:FOR H=1 TO 1:PRINT "EIGHT";\n40 NEXT H:NEXT G:NEXT F:NEXT E\n50 NEXT D:NEXT C:NEXT B:NEXT A:END','EIGHT'),
      ('FOR depth guard',
       '10 FOR A=1 TO 1:FOR B=1 TO 1:FOR C=1 TO 1\n20 FOR D=1 TO 1:FOR E=1 TO 1:FOR F=1 TO 1\n30 FOR G=1 TO 1:FOR H=1 TO 1:FOR I=1 TO 1','?FOR DEPTH'),
      ('GOSUB depth guard','10 GOSUB 10','?GOSUB DEPTH'),
      ('high line numbers','1000 GOSUB 60000:END\n60000 PRINT "HIGH";:RETURN','HIGH'),
      ('missing line','10 GOTO 12345','?'),
      ('RETURN underflow','10 RETURN','?'),
      ('NEXT underflow','10 NEXT I','?FOR/NEXT @10'),
      ('READ exhaustion','10 DATA 1\n20 READ A,B','?'),
      ('array bounds','10 DIM A(1)\n20 A(2)=9','?RANGE'),
      ('array fraction','10 DIM A(2)\n20 A(.5)=9','?RANGE'),
      ('zero FOR step','10 FOR I=1 TO 3 STEP 0\n20 NEXT I','?'),
    ]
    for label,source,want in programs:
        def program(src=source,expected=want):
            machine=C(src);machine.allow_errors=True;steps=drain(machine,4000000);result=machine.screen()
            assert (result.startswith(expected) if expected.startswith('?') else result==expected),(result,expected)
            if expected.startswith('?'):assert '@' in result,('missing error line',result)
            assert bytes(machine.m[s['PROGRAM']:machine.word(s['PEND'])+1])==bytes(C(src).m[s['PROGRAM']:machine.word(s['PEND'])+1])
            return dict(screen=result,steps=steps)
        check('program '+label,program)
    def long_string():
        command('A$="'+('A'*32)+'"');result,_=command('A$=A$+A$')
        assert result.startswith('?RANGE'),result
        exact('CLS:PRINT LEN(A$);','32');return dict(overflow_error=result,preserved=True)
    check('string overflow preserves previous value',long_string)
    result=dict(result='PASS' if not failures else 'FAIL',sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                cases=cases,failures=failures,seconds=round(time.monotonic()-started,2))
    dest=ROOT/'build'/('release-audit-'+json.loads((folder/'manifest.json').read_text())['version'].removesuffix('-dev'));dest.mkdir(exist_ok=True)
    (dest/'core.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Core suite:',len(cases),'passed,',len(failures),'failed;',result['seconds'],'seconds',flush=True)
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
