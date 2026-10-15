"""Link FRE into a released font gap; preserve the validated .49 image."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import ROOT,assemble
OUT=ROOT/'build/numeric-dispatch'
def main():
    raw=release_input('s70-basic-0.4.52-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='c724c7a570a2986888d8f9e008d32b6fc4ca89f32a9d073adc5878e9e74ac87f'
    cpu=bytearray(raw[16384:]+raw[:16384]);s=json.loads((ROOT/'build/pi/symbols.json').read_text())
    code,l=assemble('numeric-dispatch','        OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())+(ROOT/'src/numeric-dispatch.inc').read_text())
    retired=[(s['FRENTRY'],0x9175),(s['SBENTRY'],0x8F5E),(s['IKENTRY'],0x8EE6),(s['SQENTRY'],s['SQCOPY'])]
    for a,b in retired:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
    spans=[(0x912A,l['NFTABLEEND'],0x9175),(0x4B93,l['NFAPPLYEND'],s['SQCOPY'])]
    for a,b,end in spans:
        assert b<=end
        cpu[a-0x4000:b-0x4000]=code[a-0x4B93:b-0x4B93]
    def patch(at,old,new):
        at-=0x4000;assert cpu[at:at+len(old)]==old
        assert len(old)==len(new);cpu[at:at+len(old)]=new
    patch(s['PIMISS'],b'\x7e'+s['SQENTRY'].to_bytes(2,'big'),b'\x7e'+l['NFENTRY'].to_bytes(2,'big'))
    a=s['FNMISS'];b=s['FNFALLBACK'];part=bytes(cpu[a-0x4000:b-0x4000])
    for old,new in [(bytes.fromhex('C105'),bytes.fromhex('C109')),(bytes.fromhex('8605'),bytes.fromhex('8606')),(b'\xc3'+s['FNAMES'].to_bytes(2,'big'),b'\xc3'+l['NFTABLE'].to_bytes(2,'big'))]:
        assert part.count(old)==1;patch(a+part.index(old),old,new)
    a=s['FNENTRY'];b=s['FNBADARG'];part=bytes(cpu[a-0x4000:b-0x4000]);old=b'\x7e'+0x47DF.to_bytes(2,'big')
    assert part.count(old)==1;patch(a+part.index(old),old,b'\x7e'+l['NFAPPLY'].to_bytes(2,'big'))
    cpu=cpu.replace(b'Typestar BASIC 0.4.52-dev',b'Typestar BASIC 0.4.53-dev')
    assert len(cpu)==32768
    m=json.loads((ROOT/'build/pi/manifest.json').read_text())
    m.update(version='0.4.53-dev',sha256=hashlib.sha256(cpu).hexdigest(),dispatch_reclaimed=sum(b-a for a,b in retired)-sum(b-a for a,b,_ in spans))
    m['dispatch_free']=[(0x8E9B,0x8EE6),(0x8F13,0x8F5E),(l['NFAPPLYEND'],s['SQCOPY']),(l['NFTABLEEND'],0x9175)];m['dispatch_retired']=retired;m['dispatch_spans']=[(a,b) for a,b,_ in spans]
    OUT.mkdir(exist_ok=True)
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(s|l,indent=2))
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2))
    print(m['version'],m['dispatch_reclaimed'],'bytes')
if __name__=='__main__':main()
