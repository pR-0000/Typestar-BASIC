"""Link token runtime and retention on decimal candidate. OFFLINE ONLY.

Uses gaps in 9C00..ABFF and retired BASIC regions; preserves AC00..BFFF.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib
import json
import re
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'build/token-current'


def main():
    OUT.mkdir(exist_ok=True)
    ram=json.loads((ROOT/'tools/firmware/candidate_ram_map.json').read_text())
    blocks=sorted((int(a,16),int(b,16),name) for name,a,b in ram['blocks'])
    for block in blocks:assert block[0]<block[1],block
    for left,right in zip(blocks,blocks[1:]):
        assert left[1]<=right[0],('candidate RAM overlap',left,right)
    for path,name,want in ram['bindings']:
        match=re.search(r'^'+name+r'\s+EQU\s+\$([0-9A-F]+)',(ROOT/path).read_text(),re.M)
        assert match and int(match[1],16)==int(want,16),(path,name,want)
    (OUT/'validation.json').unlink(missing_ok=True)
    base = ROOT/'build/decimal-current'
    cpu = bytearray((base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes())
    manifest = json.loads((base/'manifest.json').read_text())
    assert hashlib.sha256(cpu).hexdigest() == manifest['candidate_sha256']
    original = bytes(cpu)
    symbols = json.loads((base/'symbols.json').read_text())
    listing=(ROOT/'build/canon-basic/retention.lst').read_text().split('SYMBOL TABLE')[1]
    symbols.update({n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',listing)})
    symbols['LBUFFER']=0x1D80 # 70 bytes, separate from persistent LCD glyph metadata.
    assert [symbols['LBUFFER'],symbols['LBUFFER']+70]==[int(a,16) for name,*ends in ram['blocks'] if name=='LIST/SAVE text buffer' for a in ends]
    # Existing LISTSHOW has one immediate buffer address; all other code uses
    # the candidate symbol. Keep the display routine's instructions unchanged.
    begin,end=symbols['LISTSHOW']-0x4000,symbols['LISTPAINT']-0x4000
    old=bytes(cpu[begin:end]); assert old.count(bytes.fromhex('CE1B00'))==1
    cpu[begin:end]=old.replace(bytes.fromhex('CE1B00'),bytes.fromhex('CE1D80'))
    symbols['RFORMAT']=symbols['FORCOMMAND']+3
    source = '        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in symbols.items())
    source += (ROOT/'src/token-runtime.inc').read_text()
    (OUT/'runtime.asm').write_text(source)
    r = subprocess.run([str(ROOT.parent.parent/'ROMReader/tmp/m680x-tools/a09.exe'),
                        '-W', '-B'+str(OUT/'runtime.bin'), '-L'+str(OUT/'runtime.lst'),
                        str(OUT/'runtime.asm')], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stdout+r.stderr)
    payload = (OUT/'runtime.bin').read_bytes()
    runtime_table=(OUT/'runtime.lst').read_text().split('SYMBOL TABLE')[1]
    runtime_map={n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',runtime_table)}
    runtime_base=runtime_map['SEGONE']
    runtime_segments=[]
    for name,limit in [('SEGONE',symbols['FORFINISH']),('SEGTWO',0xA000),('SEGTHREE',0xA400),('SEGFOUR',0xA500),('SEGFIVE',0xA800)]:
        start,end=runtime_map[name],runtime_map[name+'END']
        assert start<end<=limit,(name,hex(end),hex(limit))
        cpu[start-0x4000:end-0x4000]=payload[start-runtime_base:end-runtime_base]
        runtime_segments.append(dict(name=name,origin=start,bytes=end-start))
    retention = '        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in symbols.items())
    retention += (ROOT/'src/token-retention.inc').read_text()
    (OUT/'retention.asm').write_text(retention)
    r = subprocess.run([str(ROOT.parent.parent/'ROMReader/tmp/m680x-tools/a09.exe'),
                        '-W', '-B'+str(OUT/'retention.bin'), '-L'+str(OUT/'retention.lst'),
                        str(OUT/'retention.asm')], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stdout+r.stderr)
    retained = (OUT/'retention.bin').read_bytes()
    retention_origin=symbols['STORELINE']+3
    assert retention_origin+len(retained) <= symbols['PRAMERROR']
    cpu[retention_origin-0x4000:retention_origin-0x4000+len(retained)] = retained
    runtime_symbols=(OUT/'runtime.lst').read_text().split('SYMBOL TABLE')[1]
    save_symbols=dict(symbols)
    save_symbols.update({n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',runtime_symbols)})
    format_source='        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in save_symbols.items() if k!='RFORMAT')
    format_source+=(ROOT/'src/token-format.inc').read_text()
    (OUT/'format.asm').write_text(format_source)
    r=subprocess.run([str(ROOT.parent.parent/'ROMReader/tmp/m680x-tools/a09.exe'),'-W',
        '-B'+str(OUT/'format.bin'),'-L'+str(OUT/'format.lst'),str(OUT/'format.asm')],capture_output=True,text=True)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    formatted=(OUT/'format.bin').read_bytes()
    assert symbols['RFORMAT']+len(formatted)<=symbols['NEXTCOMMAND']
    pos=symbols['RFORMAT']-0x4000
    cpu[pos:pos+len(formatted)]=formatted
    save_source='        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in save_symbols.items())
    save_source+=(ROOT/'src/token-save.inc').read_text()
    (OUT/'save.asm').write_text(save_source)
    r=subprocess.run([str(ROOT.parent.parent/'ROMReader/tmp/m680x-tools/a09.exe'),'-W',
        '-B'+str(OUT/'save.bin'),'-L'+str(OUT/'save.lst'),str(OUT/'save.asm')],capture_output=True,text=True)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    saved=(OUT/'save.bin').read_bytes()
    assert len(saved)<=symbols['SAVEDMSG']-symbols['SAVECMD']
    pos=symbols['SAVECMD']-0x4000
    cpu[pos:pos+len(saved)]=saved
    conditional_source='        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in save_symbols.items())
    conditional_source+=(ROOT/'src/decimal-if.inc').read_text()
    (OUT/'decimal-if.asm').write_text(conditional_source)
    r=subprocess.run([str(ROOT.parent.parent/'ROMReader/tmp/m680x-tools/a09.exe'),'-W',
        '-B'+str(OUT/'decimal-if.bin'),'-L'+str(OUT/'decimal-if.lst'),str(OUT/'decimal-if.asm')],capture_output=True,text=True)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    conditional=(OUT/'decimal-if.bin').read_bytes()
    assert 0x420C+len(conditional)<=0x4368 # Preserve IPREFIX and MFUNC.
    cpu[0x20C:0x20C+len(conditional)]=conditional
    loop_symbols=dict(save_symbols)
    condition_listing=(OUT/'decimal-if.lst').read_text().split('SYMBOL TABLE')[1]
    loop_symbols.update({n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',condition_listing)})
    loop_text=(ROOT/'src/decimal-for.inc').read_text()
    loop_symbols.update({n:int(v,16) for n,v in re.findall(r'^([A-Z][A-Z0-9]*) EQU \$([0-9A-F]+)',loop_text,re.M)})
    loop_modules=[]
    for name,origin,limit in [('decimal-for-helpers',0x9E80,0x9F60),('decimal-for',0x9D00,0x9E00),('decimal-next',0xA600,0xA700)]:
        body=(ROOT/'src'/(name+'.inc')).read_text()
        local=set(re.findall(r'^([A-Z][A-Z0-9]*)\b',body,re.M))
        code='        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in loop_symbols.items() if k not in local)+body
        (OUT/(name+'.asm')).write_text(code)
        r=subprocess.run([str(ROOT.parent.parent/'ROMReader/tmp/m680x-tools/a09.exe'),'-W',
            '-B'+str(OUT/(name+'.bin')),'-L'+str(OUT/(name+'.lst')),str(OUT/(name+'.asm'))],capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        blob=(OUT/(name+'.bin')).read_bytes()
        assert origin+len(blob)<=limit,(name,len(blob))
        cpu[origin-0x4000:origin-0x4000+len(blob)]=blob
        table=(OUT/(name+'.lst')).read_text().split('SYMBOL TABLE')[1]
        loop_symbols.update({n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',table)})
        loop_modules.append(dict(name=name,origin=origin,bytes=len(blob)))
    statement_modules=[]
    expression_table=(base/'decimal-expressions.lst').read_text().split('SYMBOL TABLE')[1]
    expression_symbols={n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',expression_table)}
    for name in ('DADVANCE','DNUMBER','DW','DPTR','DERR','DDOT','DDIG','DOUT','DCH','DEXPR','DSPACE','DVARIABLE'):
        loop_symbols[name]=expression_symbols[name]
    for name,parts in [('token-statements',[('STSEGONE','STSEGONEEND',0x57CC),('STSEGTWO','STSEGTWOEND',symbols['GOTO'])]),
                       ('direct-statements',[('DCHAIN','DCEND',symbols['NUMBER'])]),
                       ('decimal-radix',[('RADIXSTART','RADIXEND',symbols['NEXTCOMMAND'])]),
                       ('decimal-then',[('THENSKIPSTART','THENSKIPEND',symbols['SYNTAX']),
                                        ('THENSTART','THENEND',0x67C2)]),
                       ('decimal-functions',[('FNAPPLYSTART','FNAPPLYEND',0x4400),
                                             ('FNPARSESTART','FNPARSEEND',0x4800),
                                             ('FNINTSTART','FNINTEND',symbols['KGOSUB']),
                                             ('FNPEEKSTART','FNPEEKEND',0xAC00)])]:
        body=(ROOT/'src'/(name+'.inc')).read_text()
        local=set(re.findall(r'^([A-Z][A-Z0-9]*)\b',body,re.M))
        code='        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in loop_symbols.items() if k not in local)+body
        (OUT/(name+'.asm')).write_text(code)
        r=subprocess.run([str(ROOT.parent.parent/'ROMReader/tmp/m680x-tools/a09.exe'),'-W',
            '-B'+str(OUT/(name+'.bin')),'-L'+str(OUT/(name+'.lst')),str(OUT/(name+'.asm'))],capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        table=(OUT/(name+'.lst')).read_text().split('SYMBOL TABLE')[1]
        smap={n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',table)}
        blob=(OUT/(name+'.bin')).read_bytes(); start=smap[parts[0][0]]
        for first,last,limit in parts:
            a,b=smap[first],smap[last]
            assert a<b<=limit,(name,first,hex(b),hex(limit))
            cpu[a-0x4000:b-0x4000]=blob[a-start:b-start]
            statement_modules.append(dict(name=first,origin=a,bytes=b-a))
        loop_symbols.update(smap)
    pos=expression_symbols['DA_NUMBER']-0x4000
    assert cpu[pos:pos+3]==bytes([0x7E,expression_symbols['DNUMBER']>>8,expression_symbols['DNUMBER']&255])
    cpu[pos:pos+3]=bytes.fromhex('7E45D2')
    # DATOM's variable path now recognizes function names before scalar lookup.
    pos=expression_symbols['DA_NUMBER']-0x4000-3
    assert cpu[pos:pos+3]==bytes([0x7E,expression_symbols['DVARIABLE']>>8,expression_symbols['DVARIABLE']&255])
    cpu[pos:pos+3]=bytes.fromhex('7E4756')
    # Check all candidate modules together, not just their individual ceilings.
    intervals=[(m['origin'],m['origin']+m['bytes'],m.get('name','runtime'))
               for m in manifest['modules']+runtime_segments+loop_modules+statement_modules]
    intervals += [(symbols['RFORMAT'],symbols['RFORMAT']+len(formatted),'format'),
                  (symbols['SAVECMD'],symbols['SAVECMD']+len(saved),'save'),
                  (0x420C,0x420C+len(conditional),'IF'),
                  (retention_origin,retention_origin+len(retained),'retention')]
    intervals.sort()
    for left,right in zip(intervals,intervals[1:]):
        assert left[1]<=right[0],('candidate module overlap',left,right)
    # Only the console's direct call is wrapped; RUN executes split statements.
    pos=symbols['DIRECT']-0x4000
    assert cpu[pos:pos+3]==bytes([0xBD,symbols['EXECUTE']>>8,symbols['EXECUTE']&255])
    cpu[pos:pos+3]=bytes.fromhex('BD5470')
    hooks={label:runtime_map[target] for label,target in {
        'STORELINE':'RSTORE','CHECKLINE':'RCHECK','RUN':'RRUN','GOTO':'RGOTO',
        'GCALL':'RGCALL','GRETURN':'RGRETURN','LIST':'RLIST','LISTACK':'RLACK'}.items()}
    hooks.update({'RETCRC16':retention_origin,'IF':0x420C,'FORCOMMAND':0x9D00,'NEXTCOMMAND':0xA600})
    for label, address in hooks.items():
        pos = symbols[label]-0x4000
        cpu[pos:pos+3] = bytes([0x7E,address>>8,address&255])
    assert cpu[0x6C00:]==original[0x6C00:] # Preserve AEB2, its AD4B callee, and all higher IC8 services.
    assert cpu[0x2800:0x2859] == original[0x2800:0x2859]
    # Change format identity in PREP and COMMIT only; no additional work before
    # native boot. The structural/CRC hook is used after the 6829 handoff.
    for label, opcode in [('RETPREP',0x8C), ('RETCOMMIT',0xCE)]:
        begin=symbols[label]-0x4000
        end=symbols['FORDISPATCH']-0x4000 if label=='RETPREP' else symbols['RETPREP']-0x4000
        needle=bytes([opcode,0x54,0x23])
        region=bytes(cpu[begin:end])
        assert region.count(needle)==1
        address=begin+region.index(needle)+2
        cpu[address]=0x24
    before=symbols['RETPREP']-0x4000
    after=symbols['RETRESTORE']-0x4000
    assert bytes(cpu[before:after]).replace(bytes.fromhex('8C5424'),bytes.fromhex('8C5423')) == original[before:after]
    text = (OUT/'runtime.lst').read_text().split('SYMBOL TABLE')[1]
    symbols.update({n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',text)})
    (OUT/'symbols.json').write_text(json.dumps(symbols,indent=2)+'\n')
    old_banner=b'Typestar BASIC 0.4.34-dev'
    new_banner=b'Typestar BASIC 0.4.36-dev'
    assert cpu.count(old_banner)==1 and len(old_banner)==len(new_banner)
    cpu=cpu.replace(old_banner,new_banner)
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    report = dict(status='CPU candidate; package only after release checks', version='0.4.36-dev', base_sha256=manifest['candidate_sha256'],
                  sha256=hashlib.sha256(cpu).hexdigest(), runtime_bytes=sum(part['bytes'] for part in runtime_segments), runtime_segments=runtime_segments, save_bytes=len(saved), format_bytes=len(formatted), decimal_if_bytes=len(conditional),
                  loop_modules=loop_modules, statement_modules=statement_modules, ram_map=ram, retention_bytes=len(retained), retention_origin=retention_origin, retention_signature='5424', hooks=hooks,
                  limits=['Token persistence validated after native startup; previous format not migrated automatically.',
                          'Decimal loop frames use experimental RAM; printer service overlap not audited.',
                          'IC8 placement and native-service RAM overlap not audited.'])
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
