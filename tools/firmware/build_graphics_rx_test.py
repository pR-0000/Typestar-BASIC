"""Build an isolated CODE+P reception-only diagnostic, never flash hardware."""

from build_inputs import release_input

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json
from validate_array_tokens import assemble,ROOT

OUT=ROOT/'build/graphics-rx-test'

def main():
    OUT.mkdir(exist_ok=True)
    raw=release_input('s70-basic-0.4.38-dev-canon-start-nh7.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='5d36480bff5eb522d74fbd260d06b633bc7c61800c494a8cf75a3a3542727a0e'
    cpu=bytearray(raw[16384:]+raw[:16384])
    before=bytes(cpu)
    symbols=json.loads((ROOT/'build/keyboard-current/symbols.json').read_text())
    # Reuse dead arithmetic temporaries only while sitting in the direct editor.
    # 150-byte line ends at 1E61 exclusive, below the live RND seed at 1EC6.
    bindings=dict(GXBUFFER=0x1DCB,GXPATTERN=0x1BC0,GXINDEX=0x1B90,GXCOUNT=0x1B91,
        GXPTR=0x1B92,GXLEFT=0x1B94,GFCRC=0x1B95,GFLEFT=0x1B97,GFBITS=0x1B98,
        GFVALUE=0x1B99,GFHIGH=0x1B9A)
    equ=''.join(f'{k} EQU ${v:04X}\n' for k,v in (symbols|bindings).items())
    origin=0x8800
    source='        OPT H01\n'+equ+f'        ORG ${origin:04X}\n'
    for name in ('graphics-key.inc','graphics-frame.inc','graphics-rx-test.inc'):
        source+=(ROOT/'src'/name).read_text()+'\n'
    code,linked=assemble('graphics-rx-test',source)
    assert origin+len(code)<=0x9000
    manifest=json.loads((ROOT/'build/keyboard-current/manifest.json').read_text())
    for m in manifest['runtime_segments']+manifest['loop_modules']+manifest['statement_modules']:
        assert m['origin']+m['bytes']<=origin or m['origin']>=origin+len(code),m
    cpu[origin-0x4000:origin-0x4000+len(code)]=code
    def patch(label,old,new):
        at=symbols[label]-0x4000
        assert bytes(cpu[at:at+len(old)])==old,(label,cpu[at:at+len(old)].hex())
        cpu[at:at+len(old)]=new
    def jump(op,name):
        n=linked[name];return bytes((op,n>>8,n&255))
    n=symbols['KBDSCAN']
    patch('KBDREAD',bytes((0xBD,n>>8,n&255)),jump(0xBD,'GRAPHICS_SCAN'))
    for label,target in (('KBDCHAR','GRAPHICS_KEYCHAR'),('EDPRINTABLE','GXEDIT')):
        at=symbols[label]-0x4000
        assert cpu[at] == 0x81 and cpu[at+2] in (0x24,0x25)
        patch(label,bytes(cpu[at:at+4]),jump(0x7E,target)+b'\x01')
    old_banner=b'Typestar BASIC 0.4.38-dev'
    assert cpu.count(old_banner)==1
    banner=cpu.index(old_banner)
    cpu=cpu.replace(old_banner,b'Typestar BASIC 0.4.39-rx ')
    allowed=set(range(origin-0x4000,origin-0x4000+len(code)))|set(range(banner,banner+len(old_banner)))
    for label,size in (('KBDREAD',3),('KBDCHAR',4),('EDPRINTABLE',4)):
        allowed.update(range(symbols[label]-0x4000,symbols[label]-0x4000+size))
    assert len(cpu)==32768 and all(i in allowed or a==b for i,(a,b) in enumerate(zip(before,cpu)))
    manifest.update(version='0.4.39-rx',sha256=hashlib.sha256(cpu).hexdigest(),
        status='Reception-only diagnostic; no graphic printing',graphics_bytes=len(code),
        graphics_scratch=bindings,base_nh7_sha256=hashlib.sha256(raw).hexdigest())
    manifest['statement_modules'].append(dict(name='graphics-rx-test',origin=origin,bytes=len(code)))
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'symbols.json').write_text(json.dumps(symbols|linked|bindings,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(manifest['version'],len(code),manifest['sha256'])

if __name__=='__main__':main()
