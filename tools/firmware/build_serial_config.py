""".45: full printable LCD composition and selectable SCI rate; never flash."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
OUT=ROOT/'build/serial-config';VERSION='0.4.45-dev'

def main():
    OUT.mkdir(exist_ok=True)
    raw=release_input('s70-basic-0.4.44-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='ce28b4c4f8dc75dbc8202038203109a4a051604abb3ee0d33fa3a0980369a7ea'
    cpu=bytearray(raw[16384:]+raw[:16384]);before=bytes(cpu)
    s=json.loads((ROOT/'build/inkey-current/symbols.json').read_text())
    at=s['EXECUTE']-0x4000;assert cpu[at]==0x7E
    s['PREVEXEC']=int.from_bytes(cpu[at+1:at+3],'big')
    source='        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())
    source+=(ROOT/'src/serial-config.inc').read_text()+'\n'+(ROOT/'tmp/historical-lcd-font/lcd-ascii-extra.inc').read_text()
    code,linked=assemble('serial-config',source)
    assert linked['SBEND']<=0x9000 and linked['LCDEXTRAEND']<=0x9277
    assert linked['LCDEXTRAEND']-linked['LCDEXTRA']==43*7
    spans=[(0x8F13,linked['SBEND']),(0x9000,linked['LCDEXTRAEND'])]
    m=json.loads((ROOT/'build/inkey-current/manifest.json').read_text())
    for module in m['runtime_segments']+m['loop_modules']+m['statement_modules']:
        for a,b in spans:
            assert module['origin']+module['bytes']<=a or module['origin']>=b,module
    changes=[]
    def patch(address,expected,replacement):
        at=address-0x4000
        assert cpu[at:at+len(expected)]==expected,(hex(address),cpu[at:at+len(expected)].hex(),expected.hex())
        assert len(expected)==len(replacement)
        cpu[at:at+len(expected)]=replacement
        changes.append(dict(address=address,before=expected.hex(),after=replacement.hex()))
    def jump(op,target):return bytes([op])+target.to_bytes(2,'big')
    patch(s['FNENTRY'],jump(0x7E,s['IKENTRY']),jump(0x7E,linked['SBENTRY']))
    patch(s['UIINIT'],jump(0xBD,s['IKBOOT']),jump(0xBD,linked['SBBOOT']))
    patch(s['EXECUTE'],jump(0x7E,s['PREVEXEC']),jump(0x7E,linked['SBDISPATCH']))
    patch(s['SERIALINIT'],bytes([0x7F])+s['SCHAR'].to_bytes(2,'big'),jump(0x7E,linked['SBINIT']))
    lo=s['SERIALINIT']-0x4000;hi=s['SERIALCLOSE']-0x4000
    needle=bytes.fromhex('8619971C');part=bytes(cpu[lo:hi]);assert part.count(needle)==1
    patch(lo+0x4000+part.index(needle),needle,jump(0xBD,linked['SBAPPLY'])+b'\x01')
    at=s['TRIFINDGLYPH']-0x4000;assert cpu[at:at+2]==bytes.fromhex('8120')
    patch(at+0x4000,bytes(cpu[at:at+3]),jump(0x7E,linked['LXFONT']))
    for a,b in spans:cpu[a-0x4000:b-0x4000]=code[a-0x8F13:b-0x8F13]
    old=b'Typestar BASIC 0.4.44-dev';new=b'Typestar BASIC 0.4.45-dev'
    patch(cpu.index(old)+0x4000,old,new)
    allowed={p-0x4000 for a,b in spans for p in range(a,b)}
    for p in changes:allowed.update(range(p['address']-0x4000,p['address']-0x4000+len(bytes.fromhex(p['before']))))
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(before,cpu)))
    used=sum(b-a for a,b in spans)
    m.update(version=VERSION,sha256=hashlib.sha256(cpu).hexdigest(),serial_config_bytes=used,serial_config_spans=spans,
             serial_config_patches=changes,status='LCD ASCII + selectable serial rate; hardware validation pending')
    m['statement_modules'] += [dict(name=f'serial-config-lcd-{i}',origin=a,bytes=b-a) for i,(a,b) in enumerate(spans)]
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s|linked,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print(VERSION,used,m['sha256'])

if __name__=='__main__':main()
