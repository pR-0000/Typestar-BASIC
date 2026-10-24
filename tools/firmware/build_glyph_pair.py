""".94: bounded two-word rows for GLYPH, without relocating fonts or motors.

Built from the released .93 image. Three fixed private code slots are replaced;
all other changes are a guarded width limit and the version banner.
"""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/glyph-pair'
ASSEMBLER=ROOT.parent.parent/'ROMReader/tmp/m680x-tools/a09.exe'
BASE_SHA='94fb4550241850965f52978619b1dd3e6be160392031a7698ddced062b264d87'

def assemble(name,source,origin,symbols):
    own=set(re.findall(r'^([A-Z][A-Z0-9_]*)\b',source,re.M))
    definitions=''.join(f'{k} EQU ${v:04X}\n' for k,v in symbols.items() if k not in own)
    path=OUT/(name+'.asm');path.write_text(' OPT H01\n'+definitions+f' ORG ${origin:04X}\n'+source,encoding='ascii')
    run=subprocess.run([str(ASSEMBLER),'-W','-B'+str(path.with_suffix('.bin')),'-L'+str(path.with_suffix('.lst')),str(path)],capture_output=True,text=True)
    assert not run.returncode,run.stdout+run.stderr
    table=path.with_suffix('.lst').read_text().split('SYMBOL TABLE')[1]
    labels={n:int(v,16) for n,v in re.findall(r'\b([A-Z][A-Z0-9_]*)\s+[0-9A-F]{2}\s+([0-9A-F]{4})\b',table)}
    return path.with_suffix('.bin').read_bytes(),{n:labels[n] for n in own}

def main():
    OUT.mkdir(exist_ok=True)
    raw=(ROOT/'firmware/0.4.93-dev/typestar-basic-32k.bin').read_bytes()
    old=raw[16384:]+raw[:16384];assert hashlib.sha256(old).hexdigest()==BASE_SHA
    s=json.loads((ROOT/'studio/internal/profiles/basic-0.4.93-symbols.json').read_text())
    m=json.loads((ROOT/'src/paper-glyph-pair-base.json').read_text())
    assert m['sha256']==BASE_SHA
    # Recover the dispatch catalogue from the verified public base image.
    p=s['CMDTABLE'];seen=set();commands=[]
    while p:
        assert p not in seen;seen.add(p)
        key=int.from_bytes(old[p-0x4000:p-0x4000+2],'big')
        handler=int.from_bytes(old[p-0x4000+2:p-0x4000+4],'big')
        if not key:p=handler;continue
        name=old[key-0x4000:].split(b'\0',1)[0].decode('ascii')
        commands.append(dict(name=name,key=key,handler=handler));p+=4
    m['command_dispatch']=commands
    cpu=bytearray(old);patches=[];free=m['explicit_free_regions'][:]
    assert all(old[a-0x4000:b-0x4000]==b'\xff'*(b-a) for a,b in free)
    s.pop('SGCOPY',None)
    def patch(a,expected,new):
        assert len(expected)==len(new) and cpu[a-0x4000:a-0x4000+len(new)]==expected,hex(a)
        cpu[a-0x4000:a-0x4000+len(new)]=new
        patches.append(dict(address=a,bytes=len(new),old=expected.hex(),new=new.hex()))
    # The shared decimal helper copies exactly five bytes and unpacks DW.
    assert old[s['DFUNPACK']-0x4000:s['DFUNPACK']-0x4000+5]==b'\xcc'+s['DW'].to_bytes(2,'big')+b'\xfd'+s['DFDST'].to_bytes(2,'big')[:1]
    for name,file,lo,hi in [('stage','paper-glyph-pair.asm',s['SGSTAGE'],s['SGSTAGEEND']),
                            ('layout','paper-glyph-pair-layout.asm',s['SGLAYOUT'],s['SGLBAD']+3),
                            ('pixels','paper-glyph-pair-pixels.asm',s['SGRCOLUMN'],s['SGRENDEREND'])]:
        code,labels=assemble(name,(ROOT/'src'/file).read_text(),lo,s)
        assert len(code)<=hi-lo,(name,len(code),hi-lo)
        patch(lo,old[lo-0x4000:hi-0x4000],code+b'\xff'*(hi-lo-len(code)))
        if lo+len(code)<hi:free.append([lo+len(code),hi])
        s.update(labels)
    start=s['SGSOURCEOK'];end=s['SGCOMMANDEND']
    needle=b'\xf7'+s['SGWIDTH'].to_bytes(2,'big')+bytes.fromhex('c11f22')
    at=old.index(needle,start-0x4000,end-0x4000)+0x4000+4
    patch(at,b'\x1f',b'\x20')
    banner=b'Typestar BASIC 0.4.93-dev';at=old.index(banner)+0x4000
    patch(at,banner,b'Typestar BASIC 0.4.94-dev')
    free=sorted(free)
    m.update(version='0.4.94-dev',base_cpu_sha256=BASE_SHA,sha256=hashlib.sha256(cpu).hexdigest(),
             explicit_free_regions=free,explicit_free_bytes=sum(b-a for a,b in free),
             known_free_fragmented_bytes=m['other_tracked_fragment_bytes']+sum(b-a for a,b in free),
             status='Two-word row candidate; physical test pending',
             glyph_pair=dict(width=32,row_words=2,maximum_height=16,band_buffer_mode4=476,
                             source_layout='left/right 16-bit words interleaved by row',patches=patches,
                             shared_unpacker=s['DFUNPACK']))
    m.pop('nh7_sha256',None)
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    (OUT/'symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    (ROOT/'studio/internal/profiles/basic-0.4.94-symbols.json').write_text(json.dumps(s,indent=2)+'\n')
    print(json.dumps(dict(sha256=m['sha256'],free_rom=m['explicit_free_bytes'],patches=len(patches))))
if __name__=='__main__':main()
