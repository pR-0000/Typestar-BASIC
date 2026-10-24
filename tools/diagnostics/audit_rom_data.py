"""Check immutable error texts, ROM island ownership and patch provenance.

Expected texts are independent fixtures: comparing only a new pack against
its immediate predecessor would preserve an already damaged shared string.
The native motor region is compared byte for byte with the verified input.
"""
from pathlib import Path
import argparse,hashlib,json

ROOT=Path(__file__).resolve().parents[2]
ERROR_TEXTS={
    'MBREAK':'?BREAK', 'MLONG':'?LINE TOO LONG', 'MMODE':'?MODE',
    'MRANGE':'?RANGE', 'MSYNTAX':'?SYNTAX', 'MUNDEF':'?UNDEFINED LINE',
    'PMEMMSG':'?PROGRAM FULL', 'PRAMMSG':'?PROGRAM RAM',
    'SACKMSG':'?BAD ACK', 'SFAILMSG':'?SERIAL', 'SRXMSG':'?RX',
    'SSTATUSMSG':'?RX STATUS ', 'STEXTMSG':'?RX TEXT', 'STXMSG':'?TX TIMEOUT',
    'FORDEPTHMSG':'?FOR DEPTH', 'FORPAIRMSG':'?FOR/NEXT',
    'FORVARMSG':'?FOR VARIABLE', 'GDEPTHMSG':'?GOSUB DEPTH',
    'TRICHARMSG':'?LCD CHAR', 'TRIFULLMSG':'?LCD SLOTS',
    'RBPAPERMSG':'?PAPER', 'MCMESSAGE':'?MOTOR',
    'SDMESSAGE':'?DRAW', 'SDPENDING':'?DRAW PENDING', 'TRCOEFFEND':'?OUT OF DATA',
}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',default='release-candidate');args=parser.parse_args()
    folder=ROOT/'build'/args.build
    image=(folder/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    s=json.loads((folder/'symbols.json').read_text());m=json.loads((folder/'manifest.json').read_text())
    base=(ROOT/'build/sound-steady/EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    digest=hashlib.sha256(image).hexdigest()
    assert len(image)==32768 and digest==m['sha256']
    assert hashlib.sha256(base).hexdigest()==m['base_cpu_sha256']
    owners={};reclaimed=set();patches=set()
    for lo,hi in m['reclaimed']:
        assert 0x4000<=lo<hi<=0xc000
        region=set(range(lo,hi));assert not reclaimed&region
        reclaimed|=region
    for group in m['allocations']:
        for a in range(group['origin'],group['origin']+group['bytes']):
            assert a in reclaimed and a not in owners,(group['name'],hex(a),owners.get(a))
            owners[a]=group['name']
    free=set()
    for lo,hi in m['explicit_free_regions']:
        for a in range(lo,hi):
            assert a not in owners and a not in free and a in reclaimed,hex(a)
            assert image[a-0x4000]==255,hex(a)
            free.add(a)
    assert set(owners)|free==reclaimed
    assert len(free)==m['explicit_free_bytes']
    for patch in m['patches']:
        a=patch['address'];before=bytes.fromhex(patch['old']);after=bytes.fromhex(patch['new'])
        assert len(before)==len(after) and 0x4000<=a<=0xc000-len(after)
        assert base[a-0x4000:a-0x4000+len(before)]==before
        assert image[a-0x4000:a-0x4000+len(after)]==after
        patches.update(range(a,a+len(after)))
    allowed=reclaimed|patches
    assert all(x==y or i+0x4000 in allowed for i,(x,y) in enumerate(zip(base,image)))
    # Includes the three indirect GPCALL targets and their motor helpers.
    assert image[0x2e00:0x3800]==base[0x2e00:0x3800]
    messages=[]
    for label,text in ERROR_TEXTS.items():
        a=s[label];expected=text.encode('ascii')+b'\0'
        assert image[a-0x4000:a-0x4000+len(expected)]==expected,(label,hex(a))
        assert not free&set(range(a,a+len(expected)))
        messages.append(dict(symbol=label,address=a,text=text))
    banner=('Typestar BASIC '+m['version']+'\r\n\0').encode('ascii');a=s['BANNER']
    assert image[a-0x4000:a-0x4000+len(banner)]==banner
    for label in ('FORPAIRERROR','GLOOPERROR'):
        a=s[label]
        assert image[a-0x4000:a-0x4000+3]==b'\xce'+s['FORPAIRMSG'].to_bytes(2,'big')
    result=dict(result='PASS',sha256=digest,allocations=len(m['allocations']),
                reclaimed_bytes=len(reclaimed),explicit_free_bytes=len(free),
                patch_sites=len(m['patches']),native_motor_bytes_unchanged=2560,
                error_messages=messages,banner=banner[:-1].decode())
    dest=ROOT/'build'/('release-audit-'+m['version'].removesuffix('-dev'));dest.mkdir(exist_ok=True)
    (dest/'rom-data.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS ROM ownership, patch provenance, native motors, banner and',len(messages),'error texts')


if __name__=='__main__':main()
