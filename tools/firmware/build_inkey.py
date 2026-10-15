"""Link INKEY on the pinned, hardware-validated .43 image. Never flash."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re
from validate_array_tokens import ROOT,assemble
OUT=ROOT/'build/inkey-current'
VERSION='0.4.44-dev'

def main():
    OUT.mkdir(exist_ok=True)
    raw=release_input('s70-basic-0.4.43-gp-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='5b29e05f91105c0de542733a77b9ca8a10858c4b35bb9d3bc06113a49d5e5f38'
    cpu=bytearray(raw[16384:]+raw[:16384]);before=bytes(cpu)
    s=json.loads((ROOT/'build/graphics-packed/symbols.json').read_text())
    for path in ('decimal-current/decimal-expressions.lst','token-current/decimal-functions.lst',
                 'token-current/decimal-for-helpers.lst'):
        table=(ROOT/'build'/path).read_text().split('SYMBOL TABLE')[1]
        for k,v in re.findall(r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',table):
            s.setdefault(k,int(v,16))
    source='        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())
    code,linked=assemble('basic-inkey',source+(ROOT/'src/basic-inkey.inc').read_text())
    assert linked['IKEND']<=0x9000
    m=json.loads((ROOT/'build/graphics-packed/manifest.json').read_text())
    for module in m['runtime_segments']+m['loop_modules']+m['statement_modules']:
        assert module['origin']+module['bytes']<=0x8E7B or module['origin']>=linked['IKEND'],module
    changes=[]
    def patch(address,expected,replacement):
        at=address-0x4000
        assert cpu[at:at+len(expected)]==expected,(hex(address),cpu[at:at+len(expected)].hex(),expected.hex())
        assert len(expected)==len(replacement)
        cpu[at:at+len(expected)]=replacement
        changes.append(dict(address=address,before=expected.hex(),after=replacement.hex()))
    def jump(op,target):return bytes([op])+target.to_bytes(2,'big')
    patch(s['FNENTRY'],jump(0xCE,s['FNAMES']),jump(0x7E,linked['IKENTRY']))
    patch(s['UIINIT'],jump(0xBD,s['GPINIT']),jump(0xBD,linked['IKBOOT']))
    # Runtime polling must not consume keystrokes before INKEY evaluates them.
    for lo,hi in ((s['RRLOOP'],s['RRGO']),(s['DFSREAD'],s['DFSDECODE'])):
        needle=jump(0xBD,s['KBDFAST']);part=bytes(cpu[lo-0x4000:hi-0x4000])
        assert part.count(needle)==1
        patch(lo+part.index(needle),needle,jump(0xBD,linked['IKPOLL']))
    lo=s['RRUN'];part=bytes(cpu[lo-0x4000:s['RRLOOP']-0x4000])
    needle=jump(0xBD,s['CLEARVARS']);assert part.count(needle)==1
    patch(lo+part.index(needle),needle,jump(0xBD,linked['IKRUN']))
    cpu[0x4E7B:0x4E7B+len(code)]=code
    old=b'Typestar BASIC 0.4.43-gp ';new=b'Typestar BASIC 0.4.44-dev'
    banner=cpu.index(old);patch(banner+0x4000,old,new)
    allowed=set(range(0x4E7B,0x4E7B+len(code)))
    for p in changes:allowed.update(range(p['address']-0x4000,p['address']-0x4000+len(bytes.fromhex(p['before']))))
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(before,cpu)))
    m.update(version=VERSION,sha256=hashlib.sha256(cpu).hexdigest(),inkey_bytes=len(code),
             inkey_patches=changes,status='INKEY awaiting hardware validation',base_nh7_sha256=hashlib.sha256(raw).hexdigest())
    m['statement_modules'].append(dict(name='inkey',origin=0x8E7B,bytes=len(code)))
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s|linked,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print(VERSION,len(code),m['sha256'])

if __name__=='__main__':main()
