""".97: inline command catalogue funds a native, cached tile-row producer.

Repack audited BASIC sound/font/keyboard blocks, command data, ORIGIN, CLEAR,
KEYS and glyph staging/rendering. Every newly retired body is compared with
the existing image. Canon startup, math and motor code remains in place.
Keyword spellings, compressed font streams and keyboard maps retain their bytes.
"""
from pathlib import Path
import hashlib,json,random,re,sys
import build_sound_synth as base
ROOT=base.ROOT
OUT=ROOT/'build/tile-stream'
BASE_SHA='f2804c2a09c95483584246c01e918050d944326eaad8a8622b28027368ec5ab8'

def main(*, continuous_sound=False, paper_grid=False, release_audit=False):
    global OUT
    version='0.4.100-dev' if release_audit else ('0.4.99-dev' if paper_grid else ('0.4.98-dev' if continuous_sound else '0.4.97-dev'))
    OUT=ROOT/'build'/('release-candidate' if release_audit else ('paper-grid' if paper_grid else ('sound-continuous' if continuous_sound else 'tile-stream')))
    OUT.mkdir(exist_ok=True);base.OUT=OUT
    old=(ROOT/'build/sound-steady/EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    assert hashlib.sha256(old).hexdigest()==BASE_SHA
    s=json.loads((ROOT/'build/sound-steady/symbols.json').read_text());old_symbols=s.copy()
    m=json.loads((ROOT/'build/sound-steady/manifest.json').read_text())
    b=bytearray(old);retired=[[v['origin'],v['origin']+v['bytes']] for v in m['allocations']]
    commands=[];p=s['CMDTABLE'];start=p
    while p:
        key=int.from_bytes(old[p-0x4000:p-0x4000+2],'big');handler=int.from_bytes(old[p-0x4000+2:p-0x4000+4],'big')
        if key:
            commands.append(dict(oldkey=key,name=old[key-0x4000:].split(b'\0',1)[0],handler=handler));p+=4
        else:retired.append([start,p+4]);p=handler;start=p
    retired += [[s['CMDENTRY'],s['CMDEND']],[s['SGSELECT'],s['SGSELECTRAW']+3]]
    if release_audit:
        banner_at=old.index(b'Typestar BASIC 0.4.96-dev')+0x4000
        banner_end=old.index(b'\0',banner_at-0x4000)+0x4001
        assert old[s['FORPAIRMSG']-0x4000:s['FORPAIRMSG']-0x4000+5]==b'?FOR/'
        # The old NEXT suffix is already owned by repacked data. Reclaim
        # only the five-byte prefix and replace the message independently.
        retired += [[s['FORPAIRMSG'],s['FORPAIRMSG']+5],[banner_at,banner_end]]
    # HFDECODE is used only by this font adapter. Decode directly into the
    # native C,B,A order, removing the separate 31-column swap pass.
    lp=(ROOT/'src/paper-lprint-cache.asm').read_text().split('LPDECODEONE STX LPDEST',1)[1].split('LPFAIL SEC',1)[0]
    at=s['LPDECODEONE'];data,_=base.assemble('font-adapter-old','LPDECODEONE STX LPDEST'+lp,at,s)
    assert old[at-0x4000:at-0x4000+len(data)]==data
    retired.append([at,at+len(data)])
    keys=(ROOT/'src/console.inc').read_text().split('KEYDIAG JSR',1)[1].split('HEXDIGIT CMPA',1)[0]
    keys='KEYDIAG JSR'+keys
    keys=re.sub(r'KEYDIAGLOOP LDAA \$11.*?KEYDIAGSCAN JSR','KEYDIAGLOOP EQU *\nKEYDIAGSCAN JSR',keys,flags=re.S)
    at=s['KEYDIAG'];data,_=base.assemble('keys-old',keys,at,s)
    assert old[at-0x4000:at-0x4000+len(data)]==data
    retired.append([at,at+len(data)])
    keys=keys.replace('        PSHA\n        LSRA\n        LSRA\n        LSRA\n        LSRA\n        JSR HEXDIGIT\n        PULA\n        ANDA #15\n        JSR HEXDIGIT','        JSR SSTATUSHEX')
    statushex=(ROOT/'src/basic-serial.inc').read_text().split('SSTATUSHEX PSHA',1)[1].split('STXMSG FCC',1)[0]
    statushex='SSTATUSHEX PSHA'+statushex
    at=s['SSTATUSHEX'];data,_=base.assemble('hexbyte-old',statushex,at,s)
    assert old[at-0x4000:at-0x4000+len(data)]==data
    retired.append([at,at+len(data)])
    hexold=(ROOT/'src/console.inc').read_text().split('HEXDIGIT CMPA',1)[1]
    at=s['HEXDIGIT'];data,_=base.assemble('hex-old','HEXDIGIT CMPA'+hexold,at,s)
    assert len(data)==11 and old[at-0x4000:at-0x4000+len(data)]==data
    retired.append([at,at+len(data)])
    keys+=statushex.replace('        JMP HEXDIGIT\n','')+'HEXDIGIT CMPA'+hexold
    keys=keys.replace('JSR HEXDIGIT','BSR HEXDIGIT').replace('JSR SSTATUSHEX','BSR SSTATUSHEX')
    stage=(ROOT/'src/paper-glyph-pair.asm').read_text()
    at=s['SGSTAGE'];data,_=base.assemble('stage-old',stage,at,s)
    assert old[at-0x4000:at-0x4000+len(data)]==data
    retired.append([at,at+len(data)])
    # Both pointers are validated five-byte array-cell boundaries. Testing
    # the next-cell pointer against the exact array end is sufficient.
    stage=stage.replace('SGREAD LDD SGSRC\n        ADDD #5\n        SUBD SGENDPTR\n        BHI SGRANGE\n        LDX SGSRC','SGREAD LDX SGSRC\n        CPX SGENDPTR\n        BCC SGRANGE')
    stage=stage.replace('        LDX #16\n        XGDX\n        SUBB SGWIDTH\n        STAB SGCOL\n        XGDX','        PSHA\n        LDAA #16\n        SUBA SGWIDTH\n        STAA SGCOL\n        PULA')
    render=(ROOT/'src/paper-glyph-repeat.asm').read_text().split('; @island render\n',1)[1].split('; @island pixels\n',1)[0]
    at=s['SGRENDER'];data,_=base.assemble('render-old',render,at,s)
    assert old[at-0x4000:at-0x4000+len(data)]==data
    retired.append([at,at+len(data)])
    render=render.replace('SGRENDER STX SGOUT','SGRENDER STX SGDEST\n        STX SGOUT')
    at=s['MCORIGIN'];assert old[at-0x4000:at-0x4000+9]==b'\x7e'+s['OCENTRY'].to_bytes(2,'big')+b'\xbd'+s['MCFREE'].to_bytes(2,'big')+b'\x7e'+s['PMORIGIN'].to_bytes(2,'big')
    retired.append([at,at+9])
    # Coalesce the previously split ORIGIN/CLEAR implementations. Verify each
    # retired instruction fragment against its source before returning it.
    origin=(ROOT/'src/paper-origin-coordinate.asm').read_text()
    origin=origin.replace('OCVALIDATE JSR EOS','OCVALIDATE JMP OYENTRY')
    origin=origin.replace('JMP OCSTORE','JMP OYSTORE')
    clear=(ROOT/'src/basic-clear.asm').read_text()
    for prefix,source in [('origin-old',origin),('clear-old',clear)]:
        bits=re.split(r'; @island [\w-]+\n',source)
        for i,body in enumerate(bits):
            labels=re.findall(r'^([A-Z][A-Z0-9_]*)\s+(?!EQU\b)',body,re.M)
            if not labels:continue
            at=s[labels[0]];data,_=base.assemble(prefix+str(i),body,at,s)
            assert old[at-0x4000:at-0x4000+len(data)]==data,(prefix,hex(at))
            retired.append([at,at+len(data)])
    at=s['OYENTRY'];data,_=base.assemble('origin-y-old',(ROOT/'src/paper-origin-y.asm').read_text(),at,s)
    assert old[at-0x4000:at-0x4000+len(data)]==data
    retired.append([at,at+len(data)])
    free=[]
    for a,z in sorted(retired+m['explicit_free_regions']):
        if free and a<=free[-1][1]:free[-1][1]=max(z,free[-1][1])
        else:free.append([a,z])
    initial=[v[:] for v in free]
    def inside(a):return any(lo<=a<hi for lo,hi in initial)
    for a,z in free:b[a-0x4000:z-0x4000]=b'\xff'*(z-a)
    words={c['oldkey']:c['name']+b'\0' for c in commands}
    word_sites=set(s['TOKENPTRS']+2*i for i in range(37))
    for p in word_sites:
        a=int.from_bytes(old[p-0x4000:p-0x4000+2],'big');words[a]=old[a-0x4000:].split(b'\0',1)[0]+b'\0'
    bodies={
        'keyboard':(ROOT/'src/keyboard-normalized.asm').read_text(),
        'font':(ROOT/'src/paper-font-relative.asm').read_text(),
        'dispatch':(ROOT/'src/statement-inline.asm').read_text(),
        'keys':keys,
        'stage':stage,
        'render':render,
        'origin':(ROOT/'src/paper-origin-compact.asm').read_text(),
        'clear':re.sub(r'^        JMP CL(?:CHECK|RESET|APPLY)\n','',clear,flags=re.M)}
    bodies['clear']=bodies['clear'].replace('CLAPPLY JSR DECIMAL_INIT\n        CLR DFDEPTH\n        RTS','CLAPPLY CLR DFDEPTH\n        JMP DECIMAL_INIT')
    if paper_grid:
        # Small CLEAR gateways make use of seven-byte islands, leaving the
        # larger blocks available for the extended graphics selector.
        clear_body=bodies.pop('clear')
        bodies['clear-entry']='CLENTRY JSR EOS\n        JMP CLCHECK\n'
        bodies['clear-check']='CLCHECK JSR MCFREE\n        JMP CLRESET\n'
        bodies['clear-reset']='CLRESET'+clear_body.split('CLRESET',1)[1]
    text=(ROOT/'src/sound-synth.asm').read_text().replace('SUBD #60','SUBD #50').replace('SUBD #31190','SUBD #31200')
    bits=re.split(r'; @island (\w+)\n',text)
    for n,body in zip(bits[1::2],bits[2::2]):bodies['snd-'+n]=bits[0]+body
    # The compiler and delay generator are adjacent, allowing local calls.
    bodies['snd-compiler']+=bodies.pop('snd-delaycode')[len(bits[0]):]
    bodies['snd-compiler']=bodies['snd-compiler'].replace('        JMP SNDDELAYCODE\n','        BRA SNDDELAYCODE\n')
    bodies['snd-compiler']=bodies['snd-compiler'].replace('JSR SNDEMIT','BSR SNDEMIT')
    bodies['snd-compiler']=bodies['snd-compiler'].replace('SNDNOPS TSTB\n        BEQ','SNDNOPS BEQ')
    # Keep short independent helpers separate to use six/seven-byte holes.
    bodies['snd-break']='SNDBREAK'+bodies['snd-parse'].split('SNDBREAK',1)[1]
    bodies['snd-parse']=bodies['snd-parse'].split('SNDBREAK',1)[0]
    begin=bodies['snd-parse'].index('SNDARG JSR')
    end=bodies['snd-parse'].index('SNDSTOP ',begin)
    bodies['snd-arg']=bodies['snd-parse'][begin:end]
    bodies['snd-parse']=bodies['snd-parse'][:begin]+bodies['snd-parse'][end:]
    bodies['snd-parse']=bodies['snd-parse'].replace('BASICBEEP CLR SNDMODE','BASICBEEP LDAA #64\n        STAA SNDMODE')
    bodies['snd-prepare']=bodies['snd-prepare'].replace('        LDAA #2\n        STAA SNDMODE','        CLR SNDMODE')
    bodies['snd-pwm']=bodies['snd-pwm'].replace('LDD #0','CLRA\n        CLRB')
    bodies['snd-prepare']=bodies['snd-prepare'].replace('        BNE SNDOTHERJUMP\n        JMP SNDMAKEPWM\nSNDOTHERJUMP JMP SNDMAKEOTHER\n','        BEQ SNDOTHERJUMP\n')
    bodies['snd-prepare']+=bodies.pop('snd-other')[len(bits[0]):]+'SNDOTHERJUMP JMP SNDMAKEPWM\n'
    bodies['snd-prepare']=bodies['snd-prepare'].replace('        CMPA #2\n        BEQ SNDONESTAGE\n        LDAA #64\n        STAA SNDLEVEL','        STAA SNDLEVEL')
    bodies['snd-prepare']=bodies['snd-prepare'].replace('        CLR SNDLEVEL\n','')
    bodies['snd-pwm']=bodies['snd-pwm'].replace('        XGDX\n        SUBD #5\n        BCC SNDONVALID\n        CLRA\n        CLRB\nSNDONVALID ADDD #5\n        STD SNDON','        CPX #5\n        BCC SNDONVALID\n        LDX #5\nSNDONVALID STX SNDON')
    bodies['font']=bodies['font'].replace('LDD #0','CLRA\n        CLRB').replace('HFBAD SEC\n        RTS\n','')
    bodies['font']=bodies['font'].replace('        DEX\n'*6,'        XGDX\n        SUBD #6\n        XGDX\n')
    bodies['font']=bodies['font'].replace('HFDECODE STX HFDEST','HFDECODE INX\n        INX\n        STX HFDEST')
    bodies['font']=bodies['font'].replace('        INX\n        STX HFDEST','        DEX\n        STX HFDEST')
    bodies['font']=bodies['font'].replace('HFDECODE INX\n        DEX','HFDECODE INX\n        INX')
    bodies['font']=bodies['font'].replace('        BPL HFCHANNEL','        BMI HFCHANNEL').replace('        SUBD #6','        ADDD #6')
    bodies['font']=bodies['font'].replace('JSR HFGETBIT','BSR HFGETBIT')
    bodies['font']=bodies['font'].replace('HFZERO CLC\n        RTS','HFZERO RTS')
    # The cache's ASCII preflight is the sole caller of this private decoder.
    bodies['font']=bodies['font'].replace('        CMPA #94\n        BLS HFVALID\n        SEC\n        RTS\n','')
    bodies['snd-play']=(ROOT/'src/sound-steady.asm').read_text()
    bodies['snd-play']=bodies['snd-play'].replace('        LSRD\n'*7,'        ASLB\n        ROLA\n        TAB\n')
    if continuous_sound:
        sound=re.split(r'; @island (\w+)\n',(ROOT/'src/sound-continuous.asm').read_text())
        sound=dict(zip(sound[1::2],sound[2::2]))
        bodies['snd-compiler']=bodies['snd-compiler'].split('SNDDELAYCODE SUBD',1)[0]+sound['delaycode']
        bodies['snd-compiler']=bodies['snd-compiler'].replace('SNDTAIL LDD #$5A27','SNDTAIL LDD #$0927')
        bodies['snd-prepare']=bodies['snd-prepare'].replace('        SUBD #512\n','        SUBD #672\n')
        # Match v3's round-to-nearest, ties-to-even duty quantization.
        bodies['snd-pwm']=bodies['snd-pwm'].replace('        JSR SNDDIV\n        CPX #5',
            '        JSR SNDDIV\n        SUBD #50\n        BCS SNDPWMROUNDED\n        BNE SNDPWMROUNDUP\n        XGDX\n        BITB #1\n        XGDX\n        BEQ SNDPWMROUNDED\nSNDPWMROUNDUP INX\nSNDPWMROUNDED CPX #5')
        mul_end=bodies['snd-pwm'].index('        LDD #100\n',bodies['snd-pwm'].index('SNDMAKEPWM'))
        bodies['snd-pwm']=bodies['snd-pwm'][:bodies['snd-pwm'].index('SNDMAKEPWM')]+\
            'SNDMAKEPWM LDX #SNDPER\n        LDAA SNDDUTY\n        JSR SNDMUL8\n'+bodies['snd-pwm'][mul_end:]
        bodies['snd-play']=sound['play']
        for name,body in sound.items():
            if name.startswith('multiply'):bodies['snd-'+name]=body
        del bodies['snd-break']
    tile_source=(ROOT/'src/paper-tile-stream.asm').read_text()
    if not paper_grid:
        # Reproduce the published .97/.98 candidates, including their selector.
        tile_source=tile_source.replace('        LDAB SGWIDTH\n        CMPB #32\n        BHI TMBAD\n','')
        tile_source=tile_source.replace('        BEQ TMSELECTSCENE\n','').replace('TMSELECTSCENE PULA\n        JMP SBBAND\n','')
    bits=re.split(r'; @island (\w+)\n',tile_source)
    for n,body in zip(bits[1::2],bits[2::2]):bodies['tile-'+n]=bits[0]+body
    route,old_route=bodies['tile-route'].split('        JMP TMINIT\nTMOLD\n')
    bodies['tile-route']=route+bodies.pop('tile-init')[len(bits[0]):]+'TMOLD '+old_route.lstrip()
    own=set()
    for body in bodies.values():own.update(re.findall(r'^([A-Z][A-Z0-9_]*)\b',body,re.M))
    links=s|{n:0x4000 for n in own}|dict(KDDATA=0x4000,KDTABLE=0x4000,HFTABLES=0x4000,CMDTABLE=0x4000)
    groups=[]
    for name,body in bodies.items():
        data,_=base.assemble(name,body,0x4000,links);groups.append(dict(name='code-'+name,data=data,members={}))
    if release_audit:
        groups += [dict(name='error-for-pair',data=b'?FOR/NEXT\0',members={'FORPAIRMSG':0}),
                   dict(name='version-banner',data=('Typestar BASIC '+version+'\r\n\0').encode(),members={'AUDITBANNER':0})]
    command_names={c['name'] for c in commands}
    for a,data in words.items():
        if data[:-1] not in command_names:groups.append(dict(name='word-'+str(a),data=data,members={'word-'+str(a):0}))
    glyphs={};fontdata={}
    for i in range(95):
        q=s['HFGLYPHS']-0x4000+3*i;a=int.from_bytes(old[q:q+2],'big');n=old[q+2]
        glyphs[i]=(a,n)
        if n&127:fontdata[a]=old[a-0x4000:a-0x4000+(n&127)]
    for a,data in fontdata.items():groups.append(dict(name='font-'+str(a),data=data,members={'font-'+str(a):0}))
    for v in m['allocations']:
        if v['name'].startswith(('key-','hf-')):
            a=v['origin'];groups.append(dict(name=v['name'],data=old[a-0x4000:a-0x4000+v['bytes']],members={}))
    # Share exact/suffix overlaps in immutable data, as in .95.
    def mergeable(v):return v['members'] and not (v['name'].startswith('word-') and len(v['data'])<=8)
    imm=[v for v in groups if mergeable(v)];groups=[v for v in groups if not mergeable(v)]
    while True:
        best=(0,None,None,0)
        for i,a in enumerate(imm):
            for j,c in enumerate(imm):
                if i==j:continue
                offset=a['data'].find(c['data'])
                if offset>=0:score=len(c['data'])
                else:
                    score=next((n for n in range(min(len(a['data']),len(c['data'])),0,-1) if a['data'][-n:]==c['data'][:n]),0);offset=len(a['data'])-score
                if score>best[0]:best=(score,i,j,offset)
        score,i,j,offset=best
        if not score:break
        a,c=imm[i],imm[j]
        imm=[v for k,v in enumerate(imm) if k not in (i,j)]+[dict(name=a['name'],data=a['data']+c['data'][max(0,len(a['data'])-offset):],members=a['members']|{n:o+offset for n,o in c['members'].items()})]
    groups+=imm
    total=sum(len(g['data']) for g in groups)+sum(len(c['name'])+2 for c in commands)
    print('packing',total,'available',sum(z-a for a,z in free),'before fragment links',flush=True)
    (OUT/'packing-input.json').write_text(json.dumps(dict(bins=initial,items=[dict(name=g['name'],size=len(g['data'])) for g in groups])))
    # Short catalogues occupy seven/eight-byte holes. Two larger chunks hold
    # the remaining commands; subset-sum fills the other audited fragments.
    solution=None
    best_failure=10**9
    def repair_two_bins(placed,holes,pending):
        """Reuse scattered residual bytes by repacking a pair of ROM islands."""
        remaining=[]
        for item in pending:
            fixed=False
            for i,(a,z) in enumerate(initial):
                if z-a<len(item['data']):continue
                for j,(b,y) in enumerate(initial):
                    if i==j or sum(holes[k][1]-holes[k][0] for k in (i,j))<len(item['data']):continue
                    pool=[g for g in placed if a<=g['origin']<z or b<=g['origin']<y]
                    cap=z-a-len(item['data']);choices={0:[]}
                    for k,g in enumerate(pool):
                        for n,ks in sorted(list(choices.items()),reverse=True):
                            nn=n+len(g['data'])
                            if nn<=cap and nn not in choices:choices[nn]=ks+[k]
                    n=max(choices)
                    if sum(len(g['data']) for g in pool)-n>y-b:continue
                    selected=set(choices[n]);addresses=[a,b];updated=[]
                    for g,which in [(item,0)]+[(g,0 if k in selected else 1) for k,g in enumerate(pool)]:
                        updated.append(g|dict(origin=addresses[which]));addresses[which]+=len(g['data'])
                    placed=[g for g in placed if not(a<=g['origin']<z or b<=g['origin']<y)]+updated
                    holes[i]=[addresses[0],z];holes[j]=[addresses[1],y];fixed=True;break
                if fixed:break
            if not fixed:remaining.append(item)
        return placed,holes,remaining
    short=[c for c in commands if len(c['name'])<=3]
    if continuous_sound and not paper_grid:short=short[:-2]
    if release_audit:short=short[:-1]
    rest=[c for c in commands if c not in short]
    for cut in range(12,len(rest)-10):
        chunks=[[c] for c in short]+[rest[:cut],rest[cut:]]
        cg=[dict(name='catalogue-'+str(i),data=bytes(sum(len(c['name'])+2 for c in rows)+3),members={},commands=rows) for i,rows in enumerate(chunks)]
        for trial in range(100):
            rng=random.Random(trial);holes=[v[:] for v in initial];pending=groups+cg;pending=pending[:];rng.shuffle(pending)
            pending.sort(key=lambda g:-(len(g['data'])+rng.randrange(1+trial//5)));placed=[]
            for k in sorted(range(len(holes)),key=lambda i:holes[i][1]-holes[i][0]):
                a,z=holes[k];choices={0:[]}
                for j,g in enumerate(pending):
                    for n,js in sorted(list(choices.items()),reverse=True):
                        nn=n+len(g['data'])
                        if nn<=z-a and nn not in choices:choices[nn]=js+[j]
                selected=choices[max(choices)]
                for j in selected:
                    g=pending[j];placed.append(g|dict(origin=a));a+=len(g['data'])
                pending=[g for j,g in enumerate(pending) if j not in selected];holes[k]=[a,z]
            if continuous_sound and len(pending)<=2:
                placed,holes,pending=repair_two_bins(placed,holes,pending)
            if not pending:
                tables=[]
                for g in sorted((g for g in placed if g['name'].startswith('catalogue-')),key=lambda g:int(g['name'].split('-')[1])):
                    at=g['origin'];rows=[]
                    for c in g['commands']:rows.append((at,c));at+=len(c['name'])+2
                    tables.append((g['origin'],at,rows))
                solution=(placed,holes,tables);seed=trial;break
            elif continuous_sound and sum(len(g['data']) for g in pending)<best_failure:
                best_failure=sum(len(g['data']) for g in pending)
                print('packing remainder',cut,trial,[(g['name'],len(g['data'])) for g in pending],flush=True)
                (OUT/'packing-remainder.json').write_text(json.dumps(dict(placed=[dict(name=g['name'],origin=g['origin'],size=len(g['data'])) for g in placed],holes=holes,pending=[dict(name=g['name'],size=len(g['data'])) for g in pending])))
        if solution:break
    assert solution,('No tile-stream fit',total,sum(z-a for a,z in initial))
    placed,free,tables=solution
    positions={name:g['origin']+off for g in placed for name,off in g['members'].items()}
    locations={g['name']:g['origin'] for g in placed}
    links.update(KDDATA=locations['key-data'],KDTABLE=locations['key-table'],HFTABLES=locations['hf-table'],CMDTABLE=tables[0][0])
    for g in placed:
        if g['name'].startswith('code-'):
            _,ls=base.assemble(g['name'],bodies[g['name'][5:]],g['origin'],links);links.update(ls)
    for g in placed:
        data=g['data']
        if g['name'].startswith('code-'):data,_=base.assemble(g['name'],bodies[g['name'][5:]],g['origin'],links)
        assert len(data)==len(g['data']);b[g['origin']-0x4000:g['origin']-0x4000+len(data)]=data
    p=locations['hf-table'];b[p-0x4000:p-0x4000+6]=b''.join(locations['hf-'+str(i)].to_bytes(2,'big') for i in range(3))
    relocation={}
    def handler(c):
        if c['handler']==old_symbols['MCORIGIN']:return links['OCENTRY']
        return next((links[n] for n in ('BASICBEEP','BASICSOUND','OCENTRY','CLENTRY','KEYDIAG') if c['handler']==old_symbols[n]),c['handler'])
    for i,(a,end,rows) in enumerate(tables):
        for at,c in rows:
            h=handler(c);assert 0x4000<=h<0xc000
            b[at-0x4000:at-0x4000+len(c['name'])+2]=c['name']+((h-0x4000)|0x8000).to_bytes(2,'big')
            relocation[c['oldkey']]=at
        b[end-0x4000:end-0x4000+3]=b'\0'+(tables[i+1][0] if i+1<len(tables) else 0).to_bytes(2,'big')
    for a,data in words.items():
        if a not in relocation:
            match=next((v for _,_,rows in tables for v,c in rows if c['name']==data[:-1]),None)
            relocation[a]=match if match is not None else positions['word-'+str(a)]
    patches=[]
    def patch(at,new):
        assert not inside(at),hex(at)
        b[at-0x4000:at-0x4000+len(new)]=new;patches.append([at,len(new)])
    # Three private keyword readers accept both NUL and a negative tagged
    # handler byte as the end marker. BASIC strings and tokens stay unchanged.
    assert old[s['MATCH1']-0x4000:s['MATCH1']-0x4000+7]==b'\xfe'+s['KEY'].to_bytes(2,'big')+b'\xe6\x00\x27'+old[s['MATCH1']-0x4000+6:s['MATCH1']-0x4000+7]
    patch(s['MATCH1']+5,b'\x2f') # BLE: zero or negative
    assert old[s['TEWORD']-0x4000:s['TEWORD']-0x4000+3]==b'\xa6\x00\x27'
    patch(s['TEWORD']+2,b'\x2f')
    at=old.index(b'\x6d\x00\x26',s['TKMATCH']-0x4000)
    assert at+0x4000<s['TKMISS'];patch(at+0x4002,b'\x2e') # BGT: positive bytes remain
    for a,new in relocation.items():
        needle=b'\xce'+a.to_bytes(2,'big')
        for i in range(len(old)-2):
            if old[i:i+3]==needle and not inside(i+0x4000):word_sites.add(i+0x4001)
    for p in word_sites:patch(p,relocation[int.from_bytes(old[p-0x4000:p-0x4000+2],'big')].to_bytes(2,'big'))
    for i,(a,n) in glyphs.items():patch(s['HFGLYPHS']+3*i,positions.get('font-'+str(a),0).to_bytes(2,'big')+bytes([n]))
    # Incoming calls to moved private functions and statement reset gateway.
    links['MCORIGIN']=links['OCENTRY'];links['LPDECODEONE']=links['TMDECODE'];links['SGSELECT']=links['TMSELECT']
    for name in ('HFDECODE','KDENTRY','CMDENTRY','OCENTRY','CLENTRY','MCORIGIN','LPDECODEONE','SGSELECT','KEYDIAG','HEXDIGIT','SSTATUSHEX','SGSTAGE','SGREAD','SGRENDER'):
        for offset in ((0,3) if name=='CMDENTRY' else (0,)):
            needle=(s[name]+offset).to_bytes(2,'big')
            for i in range(len(old)-2):
                if old[i] in (0x7e,0xbd) and old[i+1:i+3]==needle and not inside(i+0x4000):patch(i+0x4001,(links[name]+offset).to_bytes(2,'big'))
    assert old[s['SGARGSEND']-0x4000:s['SGARGSEND']-0x4000+6]==b'\xbd'+s['EOS'].to_bytes(2,'big')+b'\x7e'+s['SGLAYOUT'].to_bytes(2,'big')
    patch(s['SGARGSEND']+4,links['TMROUTE'].to_bytes(2,'big'))
    q=old.index(b'\xc1\x04\x22',s['SGPARSE']-0x4000)
    assert q+0x4000<s['SGARGSEND'];patch(q+0x4001,b'\x05')
    if paper_grid:
        # Tile rows use the 64-byte line staging buffer. Ordinary glyphs
        # retain their 32-pixel limit in TMROUTE; tile rows accept 40 columns.
        q=old.index(b'\xc1\x20\x22',s['SGPARSE']-0x4000)
        assert q+0x4000<s['SGARGSEND'];patch(q+0x4001,b'\x28')
        # .95's keyboard end marker included 30 bytes of the old LINE
        # validator. Scene records already validate coordinates and width.
        # Enter the intact rasterizer after that redundant check.
        reference=(ROOT/'build/glyph-pair/EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
        a,z=s['PLVALID']-0x4000,s['PLMASKS']-0x4000+32
        assert old[a:z]==reference[a:z]
        sites=[i for i in range(len(old)-2) if old[i] in (0xbd,0x7e)
               and old[i+1:i+3]==s['PLLINE'].to_bytes(2,'big') and not inside(i+0x4000)]
        assert sites==[s['PCLINE']-0x4000+27],sites
        for i in sites:patch(i+0x4001,s['PLVALID'].to_bytes(2,'big'))
    # PETAIL was installed at the former LPFORMAT call site.
    hits=[i for i in range(len(old)-2) if old[i] in (0x7e,0xbd) and old[i+1:i+3]==s['PETAIL'].to_bytes(2,'big') and not inside(i+0x4000)]
    assert len(hits)==1,hits
    patch(hits[0]+0x4001,links['TMFORMAT'].to_bytes(2,'big'))
    # Cache records are 96 bytes apart; graphics guards follow each rendered
    # block's own base, rather than the beginning of the free heap.
    q=old.index(b'\xb3'+s['DFLOOR'].to_bytes(2,'big'),s['SGRCOLUMN']-0x4000)
    assert q+0x4000<s['SGRENDEREND'];patch(q+0x4001,s['SGDEST'].to_bytes(2,'big'))
    if release_audit:
        for before,after,sites in [(old_symbols['FORPAIRMSG'],positions['FORPAIRMSG'],
                                    [old_symbols['FORPAIRERROR']-0x4000,old_symbols['GLOOPERROR']-0x4000]),
                                   (banner_at,positions['AUDITBANNER'],None)]:
            refs=[i for i in range(len(old)-2) if old[i:i+3]==b'\xce'+before.to_bytes(2,'big') and not inside(i+0x4000)]
            assert refs==sorted(sites) if sites is not None else len(refs)==1,(hex(before),refs)
            for i in refs:patch(i+0x4001,after.to_bytes(2,'big'))
    else:
        patch(old.index(b'Typestar BASIC 0.4.96-dev')+0x4000,('Typestar BASIC '+version).encode())
    assert all(x==y or inside(i+0x4000) or any(a<=i+0x4000<a+n for a,n in patches) for i,(x,y) in enumerate(zip(old,b)))
    s={k:relocation.get(v,v) for k,v in old_symbols.items()}
    for k in own|{'KDDATA','KDTABLE','HFTABLES','CMDTABLE','MCORIGIN','LPDECODEONE','SGSELECT'}:
        s[k]=links[k]
    s['SNDHOLDMODE']=64
    if release_audit:
        s['FORPAIRMSG']=positions['FORPAIRMSG'];s['BANNER']=positions['AUDITBANNER']
    if continuous_sound:
        s['SNDCONTINUOUS']=1
        s['SNDBREAK']=s['BREAK']
    m.update(version=version,base_cpu_sha256=BASE_SHA,sha256=hashlib.sha256(b).hexdigest(),
             explicit_free_regions=[h for h in free if h[0]<h[1]],explicit_free_bytes=sum(z-a for a,z in free),
             allocations=[dict(name=g['name'],origin=g['origin'],bytes=len(g['data'])) for g in placed],
             reclaimed=initial,
             patches=[dict(address=a,old=old[a-0x4000:a-0x4000+n].hex(),new=b[a-0x4000:a-0x4000+n].hex()) for a,n in patches],
             command_layout='inline-tagged',command_dispatch=[dict(name=c['name'].decode(),key=relocation[c['oldkey']],handler=handler(c)) for c in commands],
             tile_stream=dict(palette_tiles=16,source_words_per_tile=4,maximum_columns=40 if paper_grid else 32),
             native_font_cache_order='CBA',sound_constant_gate_mode=64,
             status='Streaming tile candidate; validation pending')
    if continuous_sound:
        m['sound'].update(heap_noise_reserve=672,break_during_sound=False,
                          duty_rounding='nearest, ties to even',duration_rounding='whole cycles, floor, minimum one')
        m.pop('steady_sound',None)
        m['sound_playback']='Continuous counted periods; no BREAK/timer polling during a sound, requested duration <= 2000 ms'
    (OUT/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').write_bytes(b)
    (OUT/'symbols.json').write_text(json.dumps(s,indent=2)+'\n');(OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    (ROOT/('studio/internal/profiles/basic-'+version.removesuffix('-dev')+'-symbols.json')).write_text(json.dumps(s,indent=2)+'\n')
    print('PASS build',m['sha256'],'free',m['explicit_free_bytes'],'seed',seed)

if __name__=='__main__':main()
