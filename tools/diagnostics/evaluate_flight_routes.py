"""Host navigation checks for Vol radar; no helper is needed by the game.

The perimeter bound deliberately grants free heading changes, free optional
east wind on every step, no altitude restrictions and no climb fuel, while charging the real outer-band surcharge and exempting runways. Even
that optimistic aircraft must run out of the selected reserve along the
protected border corridors. Interior routes include the guide's four-step
takeoff, terrain heights, climb fuel, low forest fuel and runway alignment.
"""
from functools import lru_cache
import heapq
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools/examples'), str(ROOT/'studio/internal')]
from build_flight_simulator import terrain_map, INITIAL_FUEL, BORDER_FUEL

DIRECTIONS = ((0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1))
HEIGHTS = (0,0,0,50,50,200,300,400,500,500,0,0,0,0)


def border_cost(x,y,q):
    return BORDER_FUEL if q < 10 and (x < 16 or x > 79 or y < 16 or y > 63) else 0


def next_random(state):
    """Independent copy of src/decimal-random.inc's integer generator."""
    while True:
        for _ in range(8):
            state = (state >> 1) ^ (0xb400 if state & 1 else 0)
        if state and state-1 < 60000:
            return state, ((state-1)%10000)/10000


def first_step_wind(t,w,q,state):
    """Predict only the imminent weather update; landings ignore this wind."""
    if t:
        return int(t > 1)
    if w > 1:
        return 0
    _, chance = next_random(state)
    return int(chance < (.3 if q == 1 else .1))


@lru_cache(maxsize=1000)
def world(seed):
    return terrain_map(seed)


def route(seed, start=(86,66,200), first_wind=0):
    """Shortest calm-air route at V100, optionally including imminent wind.

    Return (fuel, [(heading, climb_selection, resulting_position), ...]).
    At the default start, add eight fuel for the four initial takeoff steps.
    The ROM pilot can replan after each real step, using current coordinates
    and the actual PRNG state. Future weather remains outside this heuristic.
    """
    rows = world(seed)
    def estimate(node):
        x,y,h = node
        return max((max(8-x,x-23,0)+1)//2,
                   (max(8-y,y-11,0)+1)//2, h//50)
    pending = [(estimate(start),0,start)]
    costs, previous = {start:0}, {}
    while pending:
        _,cost,node = heapq.heappop(pending)
        if costs.get(node) != cost:
            continue
        x,y,h = node
        if h == 0:
            actions = []
            while node in previous:
                old,d,p = previous[node]
                actions.append((d,p,node))
                node = old
            return cost, list(reversed(actions))
        for p in (-1,0,1):
            hh = h+50*p
            if hh < 0 or hh > 450:
                continue
            for d,(dx,dy) in enumerate(DIRECTIONS):
                xx = x+2*dx+(first_wind if node == start and hh else 0)
                yy = y+2*dy
                if not (0 <= xx <= 95 and 0 <= yy <= 79):
                    continue
                q = rows[yy//4][xx//4]
                if hh == 0:
                    if not (8 <= xx <= 23 and 8 <= yy <= 11 and d in (2,6)):
                        continue
                elif hh <= HEIGHTS[q]:
                    continue
                fuel = cost+1+(p == 1)+(q in (3,4) and hh <= 150)+border_cost(xx,yy,q)
                nxt = (xx,yy,hh)
                if fuel < costs.get(nxt,999):
                    costs[nxt] = fuel
                    previous[nxt] = (node,d,p)
                    heapq.heappush(pending,(fuel+estimate(nxt),fuel,nxt))
    raise AssertionError(('no route', seed, start))


def perimeter_bound():
    """Optimistic fuel lower bound for staying in the clear outside band."""
    moves = set()
    # Include sub-stall travel too: relaxing constraints strengthens the proof.
    for u,cost in ((1,1),(2,1),(3,2),(4,2)):
        for d,(dx,dy) in enumerate(DIRECTIONS):
            span = int((u+1)*.7) if d%2 else u
            for wind in (0,1):
                moves.add((dx*span+wind,dy*span,cost))
    pending = [(0,86,74)]
    costs = {(86,74):0}
    while pending:
        fuel,x,y = heapq.heappop(pending)
        if costs.get((x,y)) != fuel:
            continue
        if 8 <= x <= 23 and 8 <= y <= 11:
            return fuel
        for dx,dy,c in moves:
            xx,yy = x+dx,y+dy
            outside = xx < 16 or xx >= 84 or yy < 16 or yy >= 68
            if 0 <= xx <= 95 and 0 <= yy <= 79 and outside:
                q = world(1)[yy//4][xx//4]  # Outer-band terrain is seed independent.
                amount = fuel+c+border_cost(xx,yy,q)
                if amount < costs.get((xx,yy),999):
                    costs[xx,yy] = amount
                    heapq.heappush(pending,(amount,xx,yy))
    raise AssertionError('no perimeter route')


def main():
    lower = perimeter_bound()
    assert lower > INITIAL_FUEL+1, (lower,INITIAL_FUEL)
    costs = []
    for seed in range(1,1000):
        fuel,actions = route(seed)
        fuel += 8  # Four northbound steps climbing to H200.
        assert fuel+2 < INITIAL_FUEL, (seed,fuel)  # Two radar fixes, calm air.
        costs.append(fuel)
    result = dict(result='PASS',model='independent host route search',
                  reserve=INITIAL_FUEL,border_surcharge_per_step=BORDER_FUEL,
                  perimeter_optimistic_lower_bound=lower,
                  maps=999,calm_route_fuel_min=min(costs),
                  calm_route_fuel_max=max(costs),takeoff_included=True,
                  two_radar_fixes_affordable_in_calm_air=True,
                  variable_weather_and_pilot_errors_not_bounded=True)
    out = ROOT/'build/flight-simulator/validation-routes.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)


if __name__ == '__main__':
    main()
