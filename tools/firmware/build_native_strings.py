""".83 native string bytes; relocate token words, repack unchanged paper glyphs."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import hashlib,json,re,random
from validate_array_tokens import ROOT,assemble
from tokenized_program import WORDS
base=ROOT/'build/lcd-raw';out=ROOT/'build/native-strings';out.mkdir(exist_ok=True)
original=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();cpu=bytearray(original)
assert hashlib.sha256(original).hexdigest()=='dfa8c68a0292de7c96e1f0719f5a4701fd416eb230632026af1504869d31c7f6'
s=json.loads((base/'symbols.json').read_text());m=json.loads((base/'manifest.json').read_text());words=WORDS+['DIM','RND']
# Verify the exact old token module before reclaiming its code/data.
table='\nTOKENCOUNT EQU 37\nTOKENPTRS\n'+''.join(f' FDB TW{i}\n' for i in range(37))+''.join(f'TW{i} FCC "{w}"\n FCB 0\n' for i,w in enumerate(words))
old,oldsyms=assemble('native-old-check',(ROOT/'src/token-records.asm').read_text()+table)
assert original[0x6800:0x6800+len(old)]==old
limit=0xA800+len(old)
# Externalized dictionary lets expanded token logic and wire wrappers fit in place.
newsrc=(ROOT/'src/token-native.asm').read_text()
placeholder='\nTOKENCOUNT EQU 37\nTOKENPTRS\n'+''.join(' FDB $4000\n' for _ in words)
blob,ts=assemble('native-size',newsrc+placeholder)
serial,ss=assemble('native-serial-size',' OPT H01\n'+''.join(f'{k} EQU ${v:04X}\n' for k,v in s.items())+f' ORG ${0xA800+len(blob):04X}\n'+(ROOT/'src/native-serial.inc').read_text())
end=0xA800+len(blob)+len(serial);assert end<=limit
items=[dict(r) for r in m['font_allocations'] if re.fullmatch(r'font-glyph-[0-9a-f]{2}',r['name'])]
saved={r['name']:original[r['origin']-0x4000:r['origin']-0x4000+r['bytes']] for r in items}
regions=m['explicit_free_regions']+[[r['origin'],r['origin']+r['bytes']] for r in items]+[[end,limit]]
free=[]
for a,b in sorted(regions):
 if free and a<=free[-1][1]:free[-1][1]=max(b,free[-1][1])
 else:free.append([a,b])
for a,b in free:cpu[a-0x4000:b-0x4000]=b'\xff'*(b-a)
shared={}
for i,w in enumerate(words):
 data=w.encode()+b'\0';offset=original.find(data)
 while offset>=0:
  a=offset+0x4000
  if not any(a<b and a+len(data)>lo for lo,b in regions+[[0xA800,limit]]):
   shared[f'native-word-{i}']=a;break
  offset=original.find(data,offset+1)
 if f'native-word-{i}' in shared:continue
 name=f'native-word-{i}';saved[name]=w.encode()+b'\0';items.append(dict(name=name,bytes=len(w)+1))
zero=[dict(r) for r in items if r["bytes"]==0]
items=[r for r in items if r["bytes"]]
initial=[r[:] for r in free]
for seed in range(500):
 pending=items[:];random.Random(seed).shuffle(pending);free=[r[:] for r in initial];placements=[]
 for i in sorted(range(len(free)),key=lambda i:free[i][1]-free[i][0]):
  a,b=free[i];choices={0:[]}
  for j,r in enumerate(pending):
   for n,selection in sorted(list(choices.items()),reverse=True):
    nn=n+r['bytes']
    if nn<=b-a and nn not in choices:choices[nn]=selection+[j]
  selected=choices[max(choices)]
  for j in selected:
   r=pending[j];placements.append(dict(r,origin=a));a+=r['bytes']
  pending=[r for j,r in enumerate(pending) if j not in selected];free[i]=[a,b]
 if not pending:break
assert not pending,[(r['name'],r['bytes']) for r in pending]
placements+=zero
addresses={r['name']:r['origin'] for r in placements}|shared;patches=[]
def patch(a,old,new):
 assert len(old)==len(new) and cpu[a-0x4000:a-0x4000+len(old)]==old,hex(a)
 cpu[a-0x4000:a-0x4000+len(new)]=new;patches.append(dict(address=a,old=old.hex(),new=new.hex()))
for r in placements:
 a=r['origin'];cpu[a-0x4000:a-0x4000+r['bytes']]=saved[r['name']]
 if r['name'].startswith('font-glyph'):
  ch=int(r['name'].rsplit('-',1)[1],16);p=s['HFGLYPHS']+(ch-32)*3
  patch(p,original[p-0x4000:p-0x4000+2],a.to_bytes(2,'big'))
table='\nTOKENCOUNT EQU 37\nTOKENPTRS\n'+''.join(f" FDB ${addresses['native-word-'+str(i)]:04X}\n" for i in range(37))
blob,ts=assemble('native-tokens',newsrc+table);cpu[0x6800:0x6800+len(blob)]=blob
cpu[0x6800+len(blob):end-0x4000]=serial
patch(s['LOADBYTE'],b'\xbd'+s['SRXBYTE'].to_bytes(2,'big'),b'\xbd'+ss['NATIVERX'].to_bytes(2,'big'))
a=s['LOADBYTE'];part=original[a-0x4000:a-0x4000+32];i=part.index(bytes.fromhex('817e22'))
patch(a+i,part[i:i+3],bytes.fromhex('817f27'))
needle=bytes.fromhex('a6002706bd')+s['STXBYTE'].to_bytes(2,'big')+bytes.fromhex('0820f639')
assert original.count(needle)==1
s['RSVTEXT']=original.index(needle)+0x4000
a=s['RSVTEXT']+4
patch(a,b'\xbd'+s['STXBYTE'].to_bytes(2,'big'),b'\xbd'+ss['NATIVETX'].to_bytes(2,'big'))
# The command dispatcher shares token spellings; follow its linked tables.
aliases={oldsyms[f'TW{i}']:addresses[f'native-word-{i}'] for i in range(37)}
p=s['CMDTABLE'];visited=set()
while p:
 assert p not in visited;visited.add(p)
 key=int.from_bytes(original[p-0x4000:p-0x4000+2],'big')
 if not key:p=int.from_bytes(original[p-0x4000+2:p-0x4000+4],'big');continue
 if key in aliases:patch(p,key.to_bytes(2,'big'),aliases[key].to_bytes(2,'big'))
 p+=4
for r in m['dispatch_patches']:
 data=bytes.fromhex(r['new']);a=r['address']
 if len(data)==3 and data[0]==0xce and int.from_bytes(data[1:],'big') in aliases and original[a-0x4000:a-0x4000+3]==data:
  patch(a,data,b'\xce'+aliases[int.from_bytes(data[1:],'big')].to_bytes(2,'big'))
for r in m['command_dispatch']:r['key']=aliases.get(r['key'],r['key'])
a=original.index(b'Typestar BASIC 0.4.82-dev')+0x4000
patch(a,b'Typestar BASIC 0.4.82-dev',b'Typestar BASIC 0.4.83-dev')
allowed=regions+[[0xA800,limit]]+[[r['address'],r['address']+len(bytes.fromhex(r['new']))] for r in patches]
assert all(x==y or any(a<=i+0x4000<b for a,b in allowed) for i,(x,y) in enumerate(zip(original,cpu)))
m['font_allocations']=[r for r in m['font_allocations'] if not r['name'].startswith('font-glyph')]+[r for r in placements if r['name'].startswith('font-glyph')]
m.update(version='0.4.83-dev',sha256=hashlib.sha256(cpu).hexdigest(),status='Native string candidate; tests pending',native_allocations=[r for r in placements if r['name'].startswith('native-word')],native_patches=patches,explicit_free_regions=[r for r in free if r[0]<r[1]],explicit_free_bytes=sum(b-a for a,b in free))
m['known_free_fragmented_bytes']=137-(126-m['explicit_free_bytes'])
s.update(ts);s.update({k:v for k,v in ss.items() if k.startswith(('NATIVE','NRRET','NTASCII'))})
(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(cpu)
(out/'symbols.json').write_text(json.dumps(s,indent=2));(out/'manifest.json').write_text(json.dumps(m,indent=2))
print('Native strings: free',m['explicit_free_bytes'],'token/serial end',hex(end),'sha',m['sha256'])
