"""Small byte-oriented LZ format for a future HD6301 font decoder.

Literal: tag 0..127, followed by tag+1 bytes.
Match: tag 128..255, length (tag&127)+3, distance next_byte+1 (1..256).
Overlapping matches allowed. Expected output size is supplied by the caller.
No embedded ROM data; generated assets remain private build artifacts.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import json,hashlib,zlib
from pathlib import Path

def pack(data):
    out=bytearray();literal=bytearray();p=0
    def flush():
        if literal:out.append(len(literal)-1);out.extend(literal);literal.clear()
    while p<len(data):
        best=0;distance=0
        for d in range(1,min(p,256)+1):
            n=0
            while n<130 and p+n<len(data) and data[p+n]==data[p+n-d]:n+=1
            if n>best:best,distance=n,d
        if best>=3:
            flush();out.extend((128+best-3,distance-1));p+=best
        else:
            literal.append(data[p]);p+=1
            if len(literal)==128:flush()
    flush();return bytes(out)

def unpack(data,size):
    out=bytearray();p=0
    while len(out)<size:
        if p>=len(data):raise ValueError('truncated tag')
        tag=data[p];p+=1
        if tag<128:
            n=tag+1
            if p+n>len(data) or len(out)+n>size:raise ValueError('literal overrun')
            out.extend(data[p:p+n]);p+=n
        else:
            n=(tag&127)+3
            if p>=len(data):raise ValueError('truncated distance')
            d=data[p]+1;p+=1
            if d>len(out) or len(out)+n>size:raise ValueError('match overrun')
            for _ in range(n):out.append(out[-d])
    if p!=len(data):raise ValueError('trailing bytes')
    return bytes(out)

def main():
    root=Path(__file__).resolve().parents[2];out=root/'build/paper-font'
    trace=json.loads((out/'native-trace.json').read_text())
    glyphs=[bytes(v for u in g['units'] for v in u['lanes']) for g in trace['glyphs']]
    assert len(glyphs)==95 and all(len(g)==93 for g in glyphs)
    results=[]
    for count in (95,64):
        raw=b''.join(glyphs[:count])
        for block in (1,8,16,95):
            chunks=[b''.join(glyphs[i:min(i+block,count)]) for i in range(0,count,block)]
            encoded=[pack(x) for x in chunks]
            assert all(unpack(p,len(x))==x for p,x in zip(encoded,chunks))
            offsets=[0]
            for chunk in encoded:offsets.append(offsets[-1]+len(chunk))
            index=b''.join(n.to_bytes(2,'big') for n in offsets)
            payload=index+b''.join(encoded)
            name=f'ascii-{count}-block-{block}.lz'
            (out/name).write_bytes(payload)
            results.append(dict(file=name,characters=count,block_glyphs=block,
                bytes=len(payload),index_bytes=len(index),raw_bytes=len(raw),
                sha256=hashlib.sha256(payload).hexdigest()))
    # Malformed streams must not silently overrun a destination/window.
    for data,size in [(b'',1),(b'\x80\x00',3),(b'\x01A',2),(b'\x00A',0)]:
        try:unpack(data,size)
        except ValueError:pass
        else:raise AssertionError('bad stream accepted')
    report=dict(result='PASS',source_sha256=trace['sha256'],results=results,
                zlib_reference_bytes=len(zlib.compress(b''.join(glyphs),9)),
                limitations='PC codec only; no HD6301 decoder or LPRINT integration. 24-lane physical order unverified.')
    (out/'compression.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
