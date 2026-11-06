"""Exercise both flight games on the actual BASIC ROM, including paper fixes."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'studio/internal'), str(ROOT/'tools/examples')]
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from core import analyze, codec
from emulator_worker import backend
from build_flight_simulator import source, BODY, terrain_map, terrain_cell, VIEW_Y, KHELD, ASSET_PATH, INITIAL_FUEL

CLIMB, DESCEND, LEVEL, FASTER, SLOWER, RADAR = 52, 53, 60, 21, 20, 46


def decode(raw):
    return int(''.join(f'{b:02x}' for b in raw[:4]))/10**(raw[4]&7)*(-1 if raw[4]&128 else 1)


def generation_scenarios(CPU):
    """Run the production row routine on the ROM, capturing all 480 POKEs.

    The explicit harness substitutes only its caller, so three map seeds can be
    checked without printing three complete sheets or running three journeys.
    """
    hashes = []
    for seed in (1,42,999):
        lines = {1:f'S={seed}:M=10+S MOD 6:O=8+INT(S/6)MOD 5',
                 10:'FOR I=0 TO 19:GOSUB 1400:FOR J=0 TO 23',
                 20:'Q=ASC(MID$(M$,J+1,1))-65',
                 30:'POKE 7040,Q',40:'NEXT J:NEXT I',50:'END'}
        lines.update({n:line for n,line in BODY.items() if 1400 <= n <= 1910})
        lines.update({n:line for n,line in analyze(source()[0]).records if n == 600})
        text = ''.join(f'{n} {line}\n' for n,line in sorted(lines.items()))
        c = CPU(text)
        s = c.symbols
        actual = []
        write = c.write
        def capture(address,value):
            if address == 7040:actual.append(value)
            return write(address,value)
        c.write = capture
        for steps in range(120000000):
            assert c.pc not in (s['SYNTAX'],s['RANGEERROR'],s['PMEMERROR']), (seed,c.word(s['RLINE']),c.screen())
            if c.pc == s['GETC'] and not c.input:break
            c.step()
        else:raise AssertionError(('generation timeout',seed,len(actual)))
        expected = sum(terrain_map(seed),[])
        assert actual == expected, (seed,len(actual),next(((i,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),None))
        digest = hashlib.sha256(bytes(actual)).hexdigest()
        hashes.append(digest)
        print('GENERATION',seed,'PASS',steps,digest,flush=True)
    assert len(set(hashes)) == 3
    worlds = set()
    for seed in range(1,1000):
        cells = terrain_map(seed)
        for y,row in enumerate(cells):
            for x,q in enumerate(row):
                assert 0 <= q < 14
                if y < 4 or y > 16 or x < 4 or x > 20:
                    assert q in (0,10,11,12,13)
                if q == 8:assert x+1 < 24 and row[x+1] == 9
                if q == 9:assert x > 0 and row[x-1] == 8
        assert cells[18][21] == 12 and cells[2][2:6] == [13,11,11,13]
        assert {1,3,4,5,6,7,8,9}.issubset(set(sum(cells,[]))), seed
        worlds.add(bytes(sum(cells,[])))
    return dict(rom_seeds=[1,42,999],rom_cells=1440,map_sha256=hashes,
                host_seeds=999,distinct_terrains=len(worlds),protected_approaches=True,
                paired_peak_tiles=True,all_terrain_types=True,caller_fixture=True)


class Game:
    def __init__(self, CPU, language, native, renderer, quick=False, selection_only=False, capture_images=True):
        self.language = language
        self.capture_images = capture_images
        name = 'simulateur-de-vol' if language == 'fr' else 'flight-simulator'
        self.text = (ROOT/'examples/games'/f'{name}-{language}.bas').read_text(encoding='utf-8')
        expected,_,self.lines = source(language,labels=True)
        assert self.text == expected
        self.quick = quick
        execution_text = re.sub(rf'^{self.lines[6000]} .*$', f'{self.lines[6000]} GOTO {self.lines[6110]}', self.text, flags=re.M) if quick else self.text
        if selection_only:
            execution_text = re.sub(rf'^{self.lines[8044]} .*$', f'{self.lines[8044]} END',execution_text,flags=re.M)
        a = analyze(execution_text)
        assert not a.issues, a.issues
        self.packed = codec.pack(a.records)
        self.sha = hashlib.sha256(self.text.encode()).hexdigest()
        self.native, self.renderer = native, renderer
        self.c = CPU(execution_text)
        self.c.flight_rows = []
        self.c.flight_text = []
        self.c.instant_paper = True
        self.c.paper_origin_corrections = [(0, 0)]
        self.extra = 0
        self.steps = 0
        self.minimum = 5951
        self.wait()

    def wait(self, limit=180000000):
        c, s = self.c, self.c.symbols
        for i in range(limit):
            if c.pc == 0x8ef0 and c.word(s['RLINE']) in (self.lines[110],self.lines[8020]):
                return
            assert c.pc not in (s['SYNTAX'], s['RANGEERROR'], s['PMEMERROR']), (c.word(s['RLINE']), hex(c.pc), c.screen(), self.minimum)
            if c.pc == s['GETC'] and not c.input:
                return
            if c.pc == s.get('LPBUILD'):
                ptr, length = c.word(s['LPREAD']), c.m[s['LPREMAIN']]
                raw = bytes(c.m[ptr:ptr+length])
                if c.m[s['SGACTIVE']]:
                    c.flight_rows.append(list(raw))
                else:
                    c.flight_text.append(raw)
            if c.pc == s.get('YPPOST'):
                delta = c.word(s['PMTY'])-c.word(s['PMY'])
                if delta <= -2 and c.m[s['YPACC']]+s['YPGAIN'] >= 256:
                    self.extra += 2
                    c.paper_origin_corrections.append((len(c.paper_events), self.extra))
            c.step()
            self.steps += 1
            if self.steps % 4096 == 0:
                self.minimum = min(self.minimum, c.word(s['DHEAP'])-c.word(s['DFLOOR']))
            if i and i % 10000000 == 0:
                print('PROGRESS', self.language, self.steps, c.word(s['RLINE']), flush=True)
        raise AssertionError(('timeout', c.word(s['RLINE']), c.screen()))

    def key(self, key):
        assert self.c.pc == 0x8ef0, (hex(self.c.pc), self.c.screen())
        self.c.held_key = key
        self.c.step()
        self.c.held_key = 0
        self.wait()
        assert bytes(self.c.m[0x20c0:0x20c0+len(self.packed)]) == self.packed

    def answer(self, text):
        assert self.c.pc == self.c.symbols['GETC'], (hex(self.c.pc),self.c.screen())
        self.c.input.extend((str(text)+'\r').encode('ascii'))
        self.wait()
        assert bytes(self.c.m[0x20c0:0x20c0+len(self.packed)]) == self.packed

    def physical(self, raw, hold=0):
        """Exercise the actual ROM scanner, including ignored function keys.

        Hold until the game has consumed the press and awaits release at 100.
        This avoids a host-timed tap being shorter than a slow BASIC refresh.
        """
        c, s = self.c, self.c.symbols
        assert c.pc == 0x8ef0 and c.word(s['RLINE']) == self.lines[110]
        c.host_matrix([raw])
        for _ in range(3000000):
            c.step()
            self.steps += 1
            if c.pc == 0x8ef0 and c.word(s['RLINE']) == self.lines[100]:
                break
            assert c.pc not in (s['SYNTAX'], s['RANGEERROR'], s['PMEMERROR'])
        else:
            raise AssertionError(('physical key timeout', raw, c.screen()))
        assert c.m[KHELD] == raw, (raw, c.m[KHELD])
        before = self.vars()
        for _ in range(hold):
            c.step()
            self.steps += 1
        assert self.vars() == before, ('held key repeated', raw)
        c.host_matrix([])
        self.wait()
        assert c.m[KHELD] == 255
        assert bytes(c.m[0x20c0:0x20c0+len(self.packed)]) == self.packed

    def ignored_physical(self,raw):
        """An intentionally unused function key must leave the menu waiting."""
        c,s = self.c,self.c.symbols
        before = {k:self.vars()[k] for k in ('N','F','P','V','D')}
        c.host_matrix([raw])
        for _ in range(100000):
            c.step();self.steps += 1
        assert c.m[KHELD] == raw
        assert {k:self.vars()[k] for k in before} == before
        c.host_matrix([])
        for _ in range(100000):
            c.step();self.steps += 1
            if c.m[KHELD] == 255:break
        else:raise AssertionError(('key did not release',raw))
        self.wait()
        assert self.nav()

    def vars(self):
        c, s = self.c, self.c.symbols
        return {chr(c.m[p]):int(decode(c.m[p+1:p+6])) for p in range(c.word(s['DHEAP']), 0x3800, 6)}

    def set(self, **values):
        c, s = self.c, self.c.symbols
        for name, value in values.items():
            for p in range(c.word(s['DHEAP']), 0x3800, 6):
                if c.m[p] == ord(name):
                    c.m[p+1:p+6] = bytes.fromhex(f'{abs(value):08d}{128 if value<0 else 0:02x}')
                    break
            else:
                raise AssertionError(('missing variable', name))

    def nav(self):
        return bool(re.match(r'^[A-X]\d{1,2}~ C\d{1,3} H\d{1,3} V\d{1,3} F\d{1,2}', self.c.screen()))

    def advance(self):
        self.key(13)
        for _ in range(5):
            if self.vars()['Z'] > 0 or self.nav():break
            # Weather, boundary and tower bulletins all pause the flight.
            n = self.vars()['N']
            self.key(13)
            assert self.vars()['N'] == n
        assert self.vars()['Z'] > 0 or self.nav(), self.c.screen()
        if self.vars()['N'] % 10 == 0:
            print('FLIGHT', self.language, self.vars()['N'], self.c.screen(), flush=True)

    def capture(self, label):
        if not self.capture_images:return
        path = ROOT/'examples/guides/images'/f'flight-{label}-{self.language}.png'
        assert self.renderer(1600,168,self.c.snapshot(False),self.native,spaced=True,blink=False).save(str(path))

    def capture_paper(self):
        if self.quick or not self.capture_images:return
        from paper import PaperRaster
        from PIL import ImageChops
        raster = PaperRaster()
        events = []
        timeline = self.c.paper_origin_corrections
        j = 0
        for i,(x,y,bits) in enumerate(self.c.paper_events):
            while j+1 < len(timeline) and timeline[j+1][0] <= i:j += 1
            events.append((x,y-timeline[j][1],bits))
        raster.add(events)
        image = raster.output()
        bbox = ImageChops.invert(image.convert('L')).getbbox()
        image.crop((max(0,bbox[0]-20),max(0,bbox[1]-20),bbox[2]+20,bbox[3]+20)).save(ROOT/'examples/guides/images'/f'flight-paper-{self.language}.png')

    def palette(self):
        """Decode the actual numeric array, including packed DATA expansion."""
        c, s = self.c, self.c.symbols
        # The array header layout is shared with the existing paper diagnostics.
        p = c.word(s['PEND'])+1
        assert c.m[p] == ord('G'), (hex(p), bytes(c.m[p:p+12]))
        p += 9
        return [int(decode(c.m[p+5*i:p+5*i+5])) for i in range(88)]

    def array_set(self,index,value):
        p = self.c.word(self.c.symbols['PEND'])+10+5*index
        self.c.m[p:p+5] = bytes.fromhex(f'{abs(value):08d}{128 if value<0 else 0:02x}')

    def snapshot(self):
        return copy.deepcopy(self.c), self.extra

    def restore(self, state):
        self.c, self.extra = copy.deepcopy(state)


def weather_scenarios(g, initial):
    """Actual BASIC weather with explicit flight-state/PRNG fixtures.

    Identical random samples distinguish land from water. A second trace
    exercises expiration, variable recovery windows and repeated onsets.
    No production instruction or probability is replaced.
    """
    def rnd(state):
        while True:
            for _ in range(8):
                state = (state >> 1) ^ (0xb400 if state & 1 else 0)
            if state and state-1 < 60000:return state,(state-1)%10000/10000
    middle = next(s for s in range(1,65536) if .1 <= rnd(s)[1] < .3)
    certain = 73  # Real PRNG trace yields lengths 5, 5, 3 within 25 steps.
    assert rnd(certain)[1] < .1
    results = []
    for q in (0,1):
        g.restore(initial)
        g.set(H=200,V=100,P=0,W=0,Q=q)
        # Before this flight, Q is the chosen starting terrain. The real
        # endpoint is a safe runway; collision checks refresh Q normally.
        address = 0x1ec6  # src/decimal-random.inc, not exported in the map.
        g.c.m[address:address+2] = middle.to_bytes(2,'big')
        g.advance()
        active = g.vars()['T']
        assert bool(active) == (q == 1), (q,active,g.c.screen())
        if active:
            assert 2 <= active <= 5
            g.capture('orage')
            n,f,jobs = g.vars()['N'],g.vars()['F'],g.c.jobs
            g.physical(0x33)
            assert (g.vars()['N'],g.vars()['F'],g.c.jobs) == (n,f,jobs)
            assert not g.nav()
            g.key(13)
        results.append(active)
    g.restore(initial)
    g.set(H=200,V=100,P=0,W=0,Q=0)
    address = 0x1ec6
    g.c.m[address:address+2] = certain.to_bytes(2,'big')
    g.advance()
    assert 2 <= g.vars()['T'] <= 5  # Storms also occur over land.
    durations,windows = [g.vars()['T']],[]
    # Recenter only the fixture aircraft to avoid leaving the map during a
    # long weather trace. T/W/randomness remain wholly controlled by BASIC.
    for _ in range(24):
        old = g.vars()
        g.set(X=86,Y=70,D=0,H=200,V=100,F=99,Q=0,R=100)
        g.advance()
        now = g.vars()
        if old['T'] > 0 and now['T'] == 0:
            assert 3 <= now['W'] <= 6
            windows.append(now['W'])
        if old['T'] == 0 and now['T'] > 0:
            assert old['W'] <= 1 and 2 <= now['T'] <= 5
            durations.append(now['T'])
        if old['T'] == 0 and old['W'] > 1:
            assert now['T'] == 0 and now['W'] == old['W']-1
    assert len(durations) >= 3 and len(set(durations)) >= 2,(durations,windows)
    return dict(recurrent_weather=True,variable_storm_lengths=durations,
                calm_windows=windows,identical_sample_water_only=results,
                land_storms=True,storm_blocks_both_radars=True,
                flight_and_prng_state_fixtures=True)


def marker_scenarios():
    """At each quarter-cell offset, every repeated tile still gains ink."""
    tiles = json.loads(ASSET_PATH.read_text(encoding='utf-8'))['tiles'][:14]
    cross = [(3,y) for y in range(7)]+[(x,3) for x in range(7) if x != 3]
    visible = {}
    for tile in tiles:
        additions = []
        for cy in (0,2,4,6):
            for cx in (0,2,4,6):
                additions.append(sum(not(tile['rows'][(cy+y-3)%8] & (128>>((cx+x-3)%8))) for x,y in cross))
        assert min(additions) > 0,(tile['id'],additions)
        visible[tile['id']] = min(additions)
    assert tiles[1]['rows'] == [0,76,50,0,0,76,50,0]
    return dict(radar_cross_pixels=13,minimum_added_ink_by_tile=visible,
                quarter_cell_positioning=True,position_pitch_native_pixels=2)


def ordinary_flight(g, initial):
    """Use ordinary controls and two radar fixes to cross the actual terrain.

    The host pilot replans after each step; no game variable or instruction is
    changed. Its first-step wind prediction is checked against actual BASIC.
    """
    from evaluate_flight_routes import route, first_step_wind, terrain_map
    g.restore(initial)
    for _ in range(5):g.key(FASTER)
    g.physical(0x34)
    for _ in range(4):g.advance()
    assert g.vars()['H'] == 200 and g.vars()['T'] == 0
    g.capture('vol')
    fixes = 0
    trace = []
    seen_storm = False
    while g.vars()['Z'] == 0:
        v = g.vars()
        assert v['N'] < 90, ('route timeout',v)
        if v['T'] and not seen_storm:
            seen_storm = True
            g.capture('orage')
            fuel,jobs = v['F'],g.c.jobs
            g.key(RADAR)
            assert g.vars()['F'] == fuel and g.c.jobs == jobs
            g.key(13)
        if fixes < 2 and v['N'] >= 4+14*fixes and v['T'] == 0 and v['R'] == 0:
            if v['Q'] != 1 or v['H'] >= 150:
                g.physical(0x33 if fixes else 0x2e)
                g.key(13)
                assert g.vars()['F'] == v['F']-1
                g.key(13)
                fixes += 1
                v = g.vars()
        wind = first_step_wind(v['T'],v['W'],v['Q'],g.c.word(0x1ec6))
        fuel,actions = route(v['S'],(v['X'],v['Y'],v['H']),wind)
        assert fuel < v['F'], ('planned fuel exhausted',fuel,v)
        heading,p,expected = actions[0]
        while g.vars()['D'] != heading:
            g.key(19 if (heading-g.vars()['D'])%8 <= 4 else 18)
        if g.vars()['P'] != p:
            g.physical({1:0x34,0:0x3c,-1:0x35}[p])
        g.advance()
        v = g.vars()
        assert (v['X'],v['Y'],v['H']) == expected, (expected,v)
        assert v['Z'] in (0,1), v
        trace.append({k:v[k] for k in ('N','X','Y','H','F','T')})
    assert g.vars()['Z'] == 1 and fixes == 2 and seen_storm,g.vars()
    g.capture('arrivee')
    return dict(natural_landing=True,landing_fuel=g.vars()['F'],
                radar_fixes=fixes,weather_encountered=True,flight_trace=trace)


def feature_scenarios(g, initial):
    """New rules on actual ROM, with explicit state and PRNG fixtures."""
    from evaluate_flight_routes import next_random
    def prepare(**extra):
        g.restore(initial)
        fields=dict(X=72,Y=60,H=200,V=100,D=0,P=0,F=99,N=0,T=0,W=100,R=0,J=0,M=0,O=0,Q=0)
        fields.update(extra)
        g.set(**fields)
    seeds={}
    for state in range(1,65536):
        following,a=next_random(state)
        _,b=next_random(following)
        if a<=.5:seeds.setdefault('altitude' if b<.5 else 'radar',state)
        if len(seeds)==2:break
    def request(kind):
        prepare(N=7)
        g.c.m[0x1ec6:0x1ec8]=seeds[kind].to_bytes(2,'big')
        g.advance()
        assert g.vars()['J']==6 and g.vars()['M']==(300 if kind=='altitude' else 0),g.vars()

    prepare(X=86,Y=68,H=150,P=1,N=3,F=93,W=2,Q=10)
    g.advance();g.capture('vol')
    assert g.vars()['H']==200 and g.vars()['F']==91 and g.vars()['T']==0

    request('altitude');g.capture('tour-altitude')
    g.set(T=3)
    g.advance();g.advance()
    assert g.vars()['J']==6 and g.vars()['T']==1
    g.capture('orage')
    g.set(T=0,W=100)
    g.physical(0x34)
    g.advance()
    assert g.vars()['H']==250 and g.vars()['J']==5
    g.key(13)
    assert g.vars()['H']==300 and g.vars()['O']==1 and g.vars()['J']==0
    assert not g.nav()
    g.capture('tour-ok');g.key(13)

    request('radar');g.capture('tour-radar')
    fuel=g.vars()['F'];jobs=g.c.jobs
    g.physical(0x33);g.key(8)
    assert g.vars()['J']==6 and g.vars()['O']==0 and g.vars()['F']==fuel
    g.physical(0x2e);g.key(13)
    assert g.vars()['J']==0 and g.vars()['O']==1 and g.vars()['F']==fuel-1
    assert g.c.jobs==jobs+1 and g.vars()['B']==VIEW_Y
    g.capture('radar')
    g.key(13)
    g.capture_paper()

    prepare(N=9,J=1,M=400)
    g.key(13)
    assert g.vars()['J']==0 and g.vars()['O']==0 and g.vars()['Z']==0
    g.capture('tour-expire');g.key(13)
    assert g.nav()
    for fields in (dict(T=3),dict(H=100),dict(R=2),dict(Y=20)):
        prepare(N=7,**fields)
        g.advance()
        assert g.vars()['J']==0,fields

    prepare(X=78,Y=40,H=450,D=2)
    g.key(13)
    assert g.vars()['F']==96 and g.palette()[64]==1
    assert not g.nav()
    g.capture('vent');g.key(13)
    assert ('VENT+' if g.language=='fr' else 'WIND+') in g.c.screen()
    g.advance()
    assert g.vars()['F']==93
    for _ in range(4):g.key(19)
    g.advance();g.advance()
    assert g.vars()['X']==78 and g.vars()['F']==89 and g.palette()[64]==0

    prepare(X=86,Y=74)
    g.advance()
    assert g.vars()['F']==98 and g.palette()[64]==0
    prepare(X=24,Y=10,H=50,P=-1,D=6,N=10,O=2)
    g.key(13)
    assert g.vars()['Z']==1 and g.vars()['F']==98
    score=100+5*98-11+20*2
    assert str(score) in g.c.screen() and 'SCORE' in g.c.screen()
    g.capture('arrivee')
    for fields in (dict(X=0,D=6),dict(X=95,D=2),dict(Y=0,D=0),dict(Y=79,D=4)):
        prepare(H=450,**fields)
        jobs=g.c.jobs
        g.key(13)
        assert g.vars()['Z']==4 and g.c.jobs==jobs,fields
        assert ('carte' if g.language=='fr' else 'map') in g.c.screen()
    g.capture('sortie')
    prepare(H=500,D=7,V=160,J=6,M=400)
    g.key(FASTER)
    assert g.c.screen().endswith('H400/6'),g.c.screen()
    return dict(border_surcharge=2,border_entry_warning=True,border_exit_clears=True,
                runway_exemptions=True,all_four_map_exits_end_flight=True,
                altitude_request=True,radar_request=True,request_cancel_preserved=True,
                storm_pauses_deadline=True,expiry_is_nonfatal=True,
                request_eligibility=True,score=score,hud_fits_32_columns=True,
                explicit_state_and_prng_fixtures=True)


def scenarios(g, controls_only=False, seed=42, flight_only=False, features_only=False):
    g.key(13)
    for invalid in (-1,1000,'1.5'):
        g.answer(invalid)
        assert g.c.pc == g.c.symbols['GETC']
    g.answer(seed)  # Actual twenty-row print, then two startup messages.
    actual_seed = g.vars()['S']
    assert actual_seed == seed if seed else 1 <= actual_seed <= 999
    expected_map = terrain_map(actual_seed)
    if g.quick:
        assert g.c.tiles == g.c.jobs == 0
    else:
        assert g.c.flight_rows == expected_map, ('printed terrain differs',g.c.flight_rows,expected_map)
        assert g.c.tiles == 480+sum(map(len,g.c.flight_text)), (g.c.tiles,g.c.jobs)
        assert g.c.jobs == 42, g.c.jobs
        assert str(actual_seed).encode() in g.c.flight_text[0],g.c.flight_text[0]
    g.key(13)
    assert g.nav(), g.c.screen()
    assert all(g.vars()[k] == v for k,v in dict(X=86,Y=74,D=0,V=0,H=0,F=INITIAL_FUEL,P=0,N=0,T=0,R=0,Z=0,B=VIEW_Y,C=0).items()), g.vars()
    g.capture('depart')
    initial = g.snapshot()
    values = g.palette()
    for tile in json.loads(ASSET_PATH.read_text(encoding='utf-8'))['tiles'][:14]:
        rows = tile['rows']
        expected = [256*rows[i]+rows[i+1] for i in range(0,8,2)]
        assert values[4*tile['id']:4*tile['id']+4] == expected,(tile,values)
    assert values[56:64] == [16,16,16,254,16,16,16,0]
    if features_only:
        features=feature_scenarios(g,initial)
        return dict(map_printed=not g.quick,quick_print_fixture=g.quick,
                    printed_map_matches=not g.quick,seed=actual_seed,
                    source_sha256=g.sha,tokenized_bytes=len(g.packed),
                    minimum_free=g.minimum,instructions=g.steps,**features)
    if flight_only:
        flight = ordinary_flight(g, initial)
        return dict(map_printed=not g.quick,quick_print_fixture=g.quick,
                    seed=actual_seed,initial_fuel=INITIAL_FUEL,
                    source_sha256=g.sha,tokenized_bytes=len(g.packed),
                    minimum_free=g.minimum,instructions=g.steps,**flight)
    initial_jobs, initial_events = g.c.jobs, len(g.c.paper_events)

    # Matrix codes differ from INKEY values: margins become 20/21 while T+,
    # T-, TEXT and REPEAT need the game's debounced PEEK fallback.
    for raw, variable, value in [(0x34,'P',1), (0x35,'P',-1), (0x3c,'P',0),
                                  (0x39,'V',20), (0x38,'V',0),
                                  (0x31,'D',7), (0x32,'D',0)]:
        g.physical(raw,hold=50000)
        assert g.nav() and g.vars()[variable] == value, (raw,g.vars())
        assert g.vars()['N'] == 0 and g.vars()['F'] == INITIAL_FUEL
    for raw in (0x33,0x2e):
        g.physical(raw)
        assert not g.nav() and g.vars()['F'] == INITIAL_FUEL and g.c.jobs == initial_jobs
        g.key(8)
        assert g.nav()
    # Both speed limits use physical presses and leave flight time unchanged.
    g.set(V=160)
    g.physical(0x39)
    assert g.vars()['V'] == 160
    g.set(V=0)
    g.physical(0x38)
    assert g.vars()['V'] == 0 and g.vars()['N'] == 0

    # Radar requires explicit confirmation, consumes fuel once and freezes time.
    g.key(RADAR)
    g.key(8)
    assert g.nav() and g.c.jobs == initial_jobs and g.vars()['F'] == INITIAL_FUEL
    g.key(RADAR)
    g.key(13)
    assert g.vars()['N'] == 0 and g.vars()['F'] == INITIAL_FUEL-1 and g.vars()['R'] == 4
    assert g.c.jobs == initial_jobs+1 and len(g.c.paper_events) > initial_events
    assert g.vars()['B'] == VIEW_Y and g.vars()['C'] == 0
    g.capture('radar')
    g.key(13)
    jobs = g.c.jobs
    g.key(RADAR)  # Cooldown rejects repeat printing without charging fuel.
    assert g.c.jobs == jobs and g.vars()['F'] == INITIAL_FUEL-1
    g.key(13)
    assert g.nav()
    if controls_only:
        g.capture_paper()
        g.restore(initial)
        for _ in range(5):
            g.physical(0x39)
        g.physical(0x34)
        for height in (50,100,150,200):
            g.advance()
            assert g.vars()['V'] == 100 and g.vars()['H'] == height and g.vars()['T'] == 0
        g.capture('vol')
        g.physical(0x3c)
        assert g.vars()['P'] == 0
        g.key(32)
        for _ in range(3):
            assert g.vars()['N'] == 4
            g.key(13)
        assert g.nav()
        weather = weather_scenarios(g,initial)
        return dict(map_printed=not g.quick, quick_print_fixture=g.quick,
                    physical_controls=True, held_key_debounce=True,
                    speed_limits=True, both_radar_keys=True,
                    seed=actual_seed, printed_map_matches=not g.quick,
                    radar_confirmation=True, radar_cancel=True, radar_cooldown=True,
                    takeoff=True, paused_help=True, tokenized_bytes=len(g.packed),
                    minimum_free=g.minimum, source_sha256=g.sha, instructions=g.steps,
                    **weather,**marker_scenarios())

    flight = ordinary_flight(g,initial)
    natural = g.snapshot()
    natural_vars = g.vars()
    # Preserve the actual printed labels, map and three radar fixes for review.
    g.capture_paper()

    # Isolated failures: high terrain, wrong runway heading, overspeed,
    # hard stall, no fuel and crossing the edge. No production bytes change.
    cases = [
        ('terrain',dict(X=4*(10+actual_seed%6)+2,Y=4*(8+(actual_seed//6)%5)+2,D=2,H=500,V=80,P=0,F=90,N=0,T=0,Z=0),2),
        ('wrong_heading',dict(X=16,Y=10,D=0,H=50,V=80,P=-1,F=90,N=0,T=0,Z=0),2),
        ('overspeed',dict(X=16,Y=10,D=6,H=50,V=120,P=-1,F=90,N=0,T=0,Z=0),2),
        ('stall',dict(X=86,Y=74,D=0,H=100,V=60,P=0,F=90,N=0,T=0,Z=0),5),
        ('fuel',dict(X=86,Y=74,D=0,H=100,V=100,P=0,F=1,N=0,T=0,Z=0),3),
        ('edge',dict(X=0,Y=74,D=6,H=100,V=100,P=0,F=90,N=0,T=0,Z=0),4),
    ]
    g.restore(initial)
    # Allocate all flight temporaries through a genuine step once.
    for _ in range(5):
        g.key(FASTER)
    g.key(CLIMB);g.advance()
    fixture_ready = g.snapshot()
    for heading, (dx,dy) in enumerate([(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]):
        g.restore(fixture_ready)
        g.set(X=86,Y=74,D=heading,H=100,V=80,P=0,F=90,N=0,T=0,Z=0)
        g.advance()
        assert (g.vars()['X'],g.vars()['Y'],g.vars()['Z']) == (86+2*dx,74+2*dy,0), (heading,g.vars())
    for name, values, outcome in cases:
        g.restore(fixture_ready)
        g.set(**values)
        g.advance()
        assert g.vars()['Z'] == outcome, (name,g.vars(),g.c.screen())
    # The printed tile controls actual flight rules, not just decoration.
    forest = next((x,y) for y,row in enumerate(expected_map) for x,q in enumerate(row) if q in (3,4))
    water = next((x,y) for y,row in enumerate(expected_map) for x,q in enumerate(row) if q == 1)
    for height, fuel in ((100,88),(200,89)):
        g.restore(fixture_ready)
        g.set(X=4*forest[0],Y=4*forest[1]+2,D=2,H=height,V=80,P=0,F=90,N=0,T=0,Z=0)
        g.advance()
        assert g.vars()['Z'] == 0 and g.vars()['F'] == fuel,(height,g.vars())
    g.restore(fixture_ready)
    g.set(X=4*water[0]+2,Y=4*water[1]+2,H=100,F=90,N=0,T=0,R=0,Z=0)
    jobs = g.c.jobs
    g.key(RADAR)
    assert g.c.jobs == jobs and g.vars()['F'] == 90 and g.vars()['N'] == 0
    assert 'H150' in g.c.screen()
    g.key(13)
    g.set(H=150)
    g.key(RADAR);g.key(13)
    assert g.c.jobs == jobs+1 and g.vars()['F'] == 89 and g.vars()['R'] == 4
    g.key(13)
    g.restore(initial)
    g.key(32)
    for _ in range(3):
        assert g.vars()['N'] == 0 and g.vars()['F'] == INITIAL_FUEL
        g.key(13)
    assert g.nav()
    g.key(8)
    assert g.vars()['N'] == 0 and g.vars()['F'] == INITIAL_FUEL
    g.key(8)
    assert g.c.pc == g.c.symbols['GETC']
    g.restore(natural)
    g.key(13)  # Result -> replay menu.
    g.key(13)  # Replay clears allocations and offers a new map.
    assert '0.5' in g.c.screen()
    g.key(8)
    assert g.c.pc == g.c.symbols['GETC']
    return dict(map_printed=not g.quick, quick_print_fixture=g.quick, map_cells=480,
                physical_controls=True, held_key_debounce=True, both_radar_keys=True,
                seed=actual_seed, printed_map_matches=not g.quick,
                forest_fuel_cost=True, low_water_blocks_radar=True,
                speed_limits=True, radar_confirmation=True,
                radar_cancel=True, radar_cooldown=True, weather_blocks_radio=True,
                weather_recovery=True, natural_landing=True, landing_fuel=natural_vars['F'],
                ending_cases=[name for name,_,_ in cases], all_eight_headings=True,
                paused_help=True, status_quit=True, replay=True, clean_quit=True,
                tokenized_bytes=len(g.packed), minimum_free=g.minimum,
                source_sha256=g.sha, instructions=g.steps)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mask-rom', required=True, type=Path)
    p.add_argument('--language', choices=('fr','en'), default='fr')
    p.add_argument('--seed',type=int,default=42,choices=range(1000),metavar='0..999')
    p.add_argument('--quick', action='store_true', help='Explicitly skip map ink, retaining the real paper movement and all flight rules')
    p.add_argument('--controls-only', action='store_true', help='Test physical controls, hold/release, speed limits, radar, takeoff and help without a full journey')
    p.add_argument('--flight-only',action='store_true',help='Fly through the terrain using ordinary controls, two radar fixes and actual weather, without the isolated failure fixtures')
    p.add_argument('--features-only',action='store_true',help='Test border winds, both tower requests, paused deadlines, score and all four map exits with explicit fixtures')
    p.add_argument('--no-captures',action='store_true',help='Leave guide images unchanged when running parallel diagnostics')
    p.add_argument('--generation-only',action='store_true',help='Run the production BASIC row routine for three seeds in an explicit caller harness; check structural properties for 999 host-generated maps')
    p.add_argument('--randomness-only',action='store_true',help='Use an explicit END-after-selection fixture to verify that different opening-menu delays produce different random map numbers')
    args = p.parse_args()
    from PySide6.QtWidgets import QApplication
    from lcd_glass import render_glass
    app = QApplication.instance() or QApplication([])
    native = {int(k,16):v for k,v in json.loads((ROOT/'studio/internal/assets/lcd-font.json').read_text(encoding='utf-8'))['rows'].items()}
    CPU = backend(mask_path=args.mask_rom, firmware_path=ROOT/'firmware/0.4.100-dev/typestar-basic-32k.bin')
    started = time.monotonic()
    if args.randomness_only:
        selected = []
        for polls in (0,11,29):
            g = Game(CPU,args.language,native,render_glass,selection_only=True)
            for _ in range(polls):g.c.step();g.wait()
            g.key(13);g.answer(0)
            selected.append(g.vars()['S'])
        assert len(set(selected)) == 3,selected
        assert len({bytes(sum(terrain_map(seed),[])) for seed in selected}) == 3,selected
        result = dict(result='PASS',menu_polls=[0,11,29],seeds=selected,
                      different_terrains=True,end_after_selection_fixture=True,
                      source_sha256=g.sha,seconds=round(time.monotonic()-started,2))
        out = ROOT/'build/flight-simulator';out.mkdir(exist_ok=True)
        (out/'validation-randomness.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print('PASS randomness',result,flush=True)
        return
    if args.generation_only:
        result = generation_scenarios(CPU)
        result['seconds'] = round(time.monotonic()-started,2)
        out = ROOT/'build/flight-simulator'
        out.mkdir(exist_ok=True)
        (out/'validation-generation.json').write_text(json.dumps(dict(result='PASS',**result),indent=2)+'\n',encoding='utf-8')
        print('PASS generation',result,flush=True)
        return
    g = Game(CPU,args.language,native,render_glass,args.quick,capture_images=not args.no_captures)
    print('MENU',args.language,len(g.packed),flush=True)
    result = scenarios(g, args.controls_only,args.seed,args.flight_only,args.features_only)
    result['seconds'] = round(time.monotonic()-started,2)
    out = ROOT/'build/flight-simulator'
    out.mkdir(exist_ok=True)
    prefix = ('features-' if args.features_only else 'flight-' if args.flight_only else 'controls-' if args.controls_only else '')+('quick-' if args.quick else '')
    (out/f'validation-{prefix}{args.language}.json').write_text(json.dumps(dict(result='PASS',**result),indent=2)+'\n',encoding='utf-8')
    print('PASS',args.language,result,flush=True)


if __name__ == '__main__':
    main()
