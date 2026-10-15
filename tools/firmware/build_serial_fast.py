""".47 bounded receive polling + Timer2 rate table on pinned .46. Never flash."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
OUT=ROOT/'build/serial-fast';VERSION='0.4.47-dev'

def main():
    OUT.mkdir(exist_ok=True)
    raw=release_input('s70-basic-0.4.46-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='2d097a560c12f6241c8e54496c9d3b8d759d926fedf1578ceba60689df95256f'
    cpu=bytearray(raw[16384:]+raw[:16384]);before=bytes(cpu)
    s=json.loads((ROOT/'build/serial-framing/symbols.json').read_text())
    source='        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())
    code,l=assemble('serial-fast',source+(ROOT/'src/serial-fast.inc').read_text())
    assert l['RPEND']<=0x9000 and l['RAEND']==s['SBAPPLYOK']
    assert l['RTEND']<=s['SBRANGE'] and l['RFLOOKEND']<=0x9277
    fresh=[(0x8FF2,l['RPEND']),(0x925E,l['RFLOOKEND'])]
    spans=fresh+[(s['SBAPPLY'],l['RAEND']),(s['SBPARSE'],l['RTEND'])]
    m=json.loads((ROOT/'build/serial-framing/manifest.json').read_text())
    for module in m['runtime_segments']+m['loop_modules']+m['statement_modules']:
        for a,b in fresh:assert module['origin']+module['bytes']<=a or module['origin']>=b,module
    changes=[]
    def patch(address,expected,replacement):
        at=address-0x4000;assert cpu[at:at+len(expected)]==expected,(hex(address),cpu[at:at+len(expected)].hex())
        assert len(expected)==len(replacement)
        cpu[at:at+len(expected)]=replacement
        changes.append(dict(address=address,before=expected.hex(),after=replacement.hex()))
    for a,b in spans:patch(a,before[a-0x4000:b-0x4000],code[a-0x8FF2:b-0x8FF2])
    for a,b in ((s['SRXPRIMARY'],s['SRXCONTINUE']),(s['GXRXWAIT'],s['GXIOBAD'])):
        part=bytes(cpu[a-0x4000:b-0x4000]);needle=b'\xBD'+s['KBDSCAN'].to_bytes(2,'big')
        assert part.count(needle)==1 and part.count(b'\x81\x36')==1
        patch(a+part.index(needle),needle,b'\xBD'+l['RFASTBREAK'].to_bytes(2,'big'))
        # PULX does not change flags: use the helper's Z instead of raw code A.
        patch(a+part.index(b'\x81\x36'),b'\x81\x36',b'\x01\x01')
    old=b'Typestar BASIC 0.4.46-dev';new=b'Typestar BASIC 0.4.47-dev'
    patch(cpu.index(old)+0x4000,old,new)
    allowed=set()
    for p in changes:allowed.update(range(p['address']-0x4000,p['address']-0x4000+len(bytes.fromhex(p['before']))))
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(before,cpu)))
    m.update(version=VERSION,sha256=hashlib.sha256(cpu).hexdigest(),fast_added_bytes=sum(b-a for a,b in fresh),
        fast_spans=spans,fast_patches=changes,status='15625/31250 hardware validation pending')
    m['statement_modules'] += [dict(name=f'serial-fast-{i}',origin=a,bytes=b-a) for i,(a,b) in enumerate(fresh)]
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s|l,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print(VERSION,m['fast_added_bytes'],m['sha256'])

if __name__=='__main__':main()
