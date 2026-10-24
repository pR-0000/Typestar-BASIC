"""Validate Markdown examples; optionally execute them on selected ROMs.

No serial port or firmware mutation. Reports go to build/user-manual.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from native_text import encode_source
from native_program import read_source, pack, unpack


def examples(path):
    return re.findall(r'```basic\n(.*?)\n```', path.read_text(encoding='utf-8'), re.S)


def static_checks(config):
    report = []
    known = set()
    content_root=HERE/config.get('content_directory','.')
    for name in config['chapters']:
        text = (content_root/name).read_text(encoding='utf-8')
        known.update(name+'#'+a for a in re.findall(r'<a id="([^"]+)"', text))
        known.add(name+'#')
        for index, source in enumerate(examples(content_root/name), 1):
            lines = source.splitlines()
            for line in lines:
                if len(encode_source(line)) > 63:
                    raise AssertionError((name, index, 'Line exceeds 63 native bytes', line))
            program = bool(lines) and all(re.match(r'^\d+\s+\S', line) for line in lines if line.strip())
            if program:
                records = read_source(source)
                packed = pack(records)
                assert unpack(packed) == sorted(records), (name,index,'Codec round trip')
            report.append(dict(chapter=name, example=index, program=program, lines=len(lines),
                               source=source, bytes=len(packed)-1 if program else None))
    missing = set(config['symbols'].values())-known
    assert not missing, sorted(missing)
    for name in config['chapters']:
        for file, anchor in re.findall(r'\]\(([^)\s]+\.md)(?:#([^)]*))?\)', (content_root/name).read_text(encoding='utf-8')):
            if urlsplit(file).scheme:
                continue
            assert (content_root/file).exists(),(name,file)
            if anchor:
                assert Path(file).name+'#'+anchor in known,(name,file,anchor)
    return report


def runtime_checks(report, mask, firmware):
    sys.path.insert(0, str(ROOT/'studio/internal'))
    from emulator_worker import backend
    CPU = backend(mask_path=mask, firmware_path=firmware)
    results = []
    def advance(cpu, predicate, budget=20000000):
        for count in range(budget):
            if predicate():
                return count
            cpu.step()
        raise AssertionError(f'Execution timeout PC={cpu.pc:04X}, LCD={cpu.screen()!r}')
    def idle(cpu):
        return not cpu.input and cpu.pc == cpu.symbols['GETC']
    def awaiting_input(cpu):
        # RLINE also retains the last executed line after END. The return
        # address distinguishes INPUT's editor from output acknowledgement.
        return (idle(cpu) and cpu.word(cpu.symbols['RLINE']) != 0
                and cpu.word(cpu.sp+1) == cpu.symbols['READNEXT']+3)
    def error(cpu):
        return cpu.lcd[0] == ord('?')
    for position, item in enumerate(report):
        if not item['program']:
            continue
        if item['chapter'] == '11-programmes-complets.md':
            results.append(dict(chapter=item['chapter'], example=item['example'], result='syntax/codec only', reason='interactive selected program; validate by playing in Studio or on the Canon'))
            continue
        source = item['source']
        based_on = None
        # A replacement line is taught after the complete GLYPH example.
        # Execute it in that program's context, including its DIM and DATA.
        if len(source.splitlines()) == 1 and int(source.split()[0]) > 10:
            previous = next((old for old in reversed(report[:position])
                             if old['chapter'] == item['chapter'] and old['program']), None)
            assert previous is not None, (item['chapter'],item['example'],'Missing context')
            lines = {int(line.split()[0]):line for line in previous['source'].splitlines()}
            lines[int(source.split()[0])] = source
            source = '\n'.join(lines[number] for number in sorted(lines))
            based_on = previous['example']
        if 'SEROPEN' in source:
            results.append(dict(chapter=item['chapter'], example=item['example'], result='syntax/codec only', reason='requires external serial peer'))
            continue
        cpu = CPU(source+'\n')
        cpu.instant_paper = True
        if 'INKEY' in source:
            cpu.held_key = 32
        replies = 0
        for _ in range(8):
            advance(cpu, lambda: idle(cpu) or error(cpu))
            assert not error(cpu),(item['chapter'], item['example'],cpu.screen())
            if 'INPUT' not in source or not awaiting_input(cpu):
                break
            prompt = cpu.screen()
            answers = [('TON NOM','ALICE'),('TON AGE','12'),('DEVINE','42'),
                       ('PRIX','2.5'),('DE 1 A 6','4'),('NOMBRE','7'),
                       ('YOUR NAME','ALICE'),('YOUR AGE','12'),('WHAT IS 6*7','42'),
                       ('PRICE','2.5'),('QUANTITY','7'),('FROM 1 TO 6','4'),('NUMBER','7')]
            answer = next((value for key,value in answers if key in prompt),None)
            assert answer is not None,(item['chapter'],item['example'],'Unanswered INPUT',prompt)
            cpu.input.extend(encode_source(answer)+b'\r')
            cpu.step()
            replies += 1
        else:
            raise AssertionError((item['chapter'],item['example'],'repeated INPUT'))
        advance(cpu,lambda:idle(cpu) or error(cpu))
        assert not error(cpu),(item['chapter'], item['example'],cpu.screen())
        if 'INPUT' in source:
            assert not awaiting_input(cpu),(item['chapter'],item['example'],'Unanswered INPUT')
        results.append(dict(chapter=item['chapter'],example=item['example'],result='PASS',
                            screen=cpu.screen(), replies=replies, paper_points=len(cpu.paper_events),
                            based_on_example=based_on))
        print(item['chapter'],item['example'],'PASS',flush=True)
    checks = [
        ('ABS(-8)', '8'), ('SGN(-5)', '-1'), ('INT(-3.8)', '-4'),
        ('FIX(-3.8)', '-3'), ('SQR(25)', '5'), ('2^3^2', '512'),
        ('-2^2', '-4'), ('(-2)^2', '4'), ('2^-3', '0.125'),
        ('10 MOD 3*2', '4'), ('(10 MOD 3)*2', '2'), ('-17 MOD 5', '-2'),
        ('%101 AND %011', '1'), ('%101 OR %011', '7'), ('NOT 0', '-1'),
        ('("A"="A")', '-1'), ('%10101', '21'), ('&H1F', '31'),
        ('LEN("Déjà")', '4'), ('ASC("A")', '65'), ('VAL("&H1F")', '31'),
        ('LEFT$("TYPESTAR",4)', 'TYPE'), ('RIGHT$("TYPESTAR",4)', 'STAR'),
        ('MID$("TYPESTAR",3,3)', 'PES'), ('MID$("TYPESTAR",5)', 'STAR'),
        ('LOG(1)', '0'), ('EXP(0)', '1'), ('STR$(12.5)', '12.5'),
    ]
    for expression, expected in checks:
        cpu = CPU('10 PRINT '+expression+'\n20 END\n')
        advance(cpu, lambda: idle(cpu) or error(cpu))
        assert cpu.screen() == expected, (expression, cpu.screen(), expected)
    return dict(firmware_sha256=hashlib.sha256(firmware.read_bytes()).hexdigest(),
                mask_sha256=hashlib.sha256(mask.read_bytes()).hexdigest(), programs=results,
                expressions=len(checks), scope='actual ROM execution in Studio; no electrical or physical validation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mask-rom', type=Path)
    parser.add_argument('--firmware-rom', type=Path)
    parser.add_argument('--config',type=Path,default=HERE/'manuel-fr.json')
    args = parser.parse_args()
    if bool(args.mask_rom) != bool(args.firmware_rom):
        parser.error('Provide both ROM paths or neither')
    config = json.loads(args.config.read_text(encoding='utf-8'))
    items = static_checks(config)
    report = dict(result='PASS',version=config['version'],indexed_symbols=len(config['symbols']),
                  examples=len(items),numbered_programs=sum(i['program'] for i in items))
    if args.mask_rom:
        report['runtime'] = runtime_checks(items,args.mask_rom.resolve(),args.firmware_rom.resolve())
    output = ROOT/'build/user-manual'
    output.mkdir(parents=True,exist_ok=True)
    (output/('validation-en.json' if config.get('language')=='en' else 'validation.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='runtime'},ensure_ascii=True))
    if 'runtime' in report:
        print('ROM examples:',len(report['runtime']['programs']),'expressions:',report['runtime']['expressions'])


if __name__ == '__main__':
    main()
