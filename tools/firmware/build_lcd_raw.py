""".82: counted PRINT strings use raw LCD codes; native block frees slot 7."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'build/lcd-native';out=ROOT/'build/lcd-raw';out.mkdir(exist_ok=True)
old=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();cpu=bytearray(old)
assert hashlib.sha256(old).hexdigest()=='d5c06d6b3b3658bc6ed7f825f76e6d77472960496604256892bdf5c411e05a47'
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text());patches=[]
def patch(a,b,n):
 assert len(b)==len(n) and cpu[a-0x4000:a-0x4000+len(b)]==b,hex(a)
 cpu[a-0x4000:a-0x4000+len(n)]=n;patches.append(dict(address=a,old=b.hex(),new=n.hex()))
# Retire the only call to SOFTBLOCK; initialization no longer touches slot 7.
call=b'\xbd'+s['SOFTBLOCK'].to_bytes(2,'big')
assert old.count(call)==1
patch(old.index(call)+0x4000,call,b'\x01'*3)
# Native fixed CGROM block, confirmed in Pierre's atlas at code AB.
a=s['SOFTVISIBLE']-4
assert old[a-0x4000:a-0x4000+4]==bytes.fromhex('86072003')
patch(a,bytes.fromhex('8607'),bytes.fromhex('86ab'))
patch(s['TRINEXTSLOT']+6,bytes.fromhex('8107'),bytes.fromhex('8108'))
patch(s['LCTRI']+6,bytes.fromhex('8106'),bytes.fromhex('8107'))
# Reuse the retired 33-byte cursor initializer. Same register contract as
# PUTC, but jump past LCDPUT control/filter branches for counted strings.
# Canonicalize 08..0F to 00..07 so automatic slot ownership sees aliases.
a=s['SOFTBLOCK'];previous=old[a-0x4000:a-0x4000+33]
assert previous==bytes.fromhex('bd5ab79638847f8a80368678bd5acbc607861fbd5adb5a26fa4fbd5adb327e5acb')
raw=bytes.fromhex('36373c368601b7')+s['OUTFLAG'].to_bytes(2,'big')+bytes.fromhex('32811024028407bd')+(s['LCDPRINTABLE']+8).to_bytes(2,'big')+bytes.fromhex('38333239')
assert len(raw)==23
patch(a,previous,raw+b'\xff'*(33-len(raw)))
patch(s['STLCD'],b'\xbd'+s['PUTC'].to_bytes(2,'big'),b'\xbd'+a.to_bytes(2,'big'))
s['LCDRAWPUT']=a
at=old.index(b'Typestar BASIC 0.4.81-dev')+0x4000
patch(at,b'Typestar BASIC 0.4.81-dev',b'Typestar BASIC 0.4.82-dev')
free=m['explicit_free_regions']+[[a+len(raw),a+33]]
m.update(version='0.4.82-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='Awaiting tests',
 explicit_free_regions=sorted(free),explicit_free_bytes=m['explicit_free_bytes']+33-len(raw),
 known_free_fragmented_bytes=m['known_free_fragmented_bytes']+33-len(raw),lcd_raw_patches=patches,
 lcd_custom_slots=8,lcd_cursor_code=171,lcd_string_range=[0,255])
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s,indent=2));(out/'manifest.json').write_text(json.dumps(m,indent=2))
print(m['sha256'])
