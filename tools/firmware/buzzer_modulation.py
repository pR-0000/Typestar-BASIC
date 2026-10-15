"""Experimental gate-rate conversion, not acoustic pitch control.

Interpolate delay count against period between measured envelope peaks.
No extrapolation; firmware/clock/IRQ changes require recalibration.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def recipe(hz,seconds=.25):
    if not math.isfinite(hz) or not math.isfinite(seconds) or hz<=0 or seconds<=0:
        raise ValueError('Positive finite modulation rate and duration required')
    data=json.loads((ROOT/'_local/development/analysis/buzzer-audio-calibration.json').read_text())
    points=sorted((1/o['modulation_peak_hz'],o['half_period_loops']) for o in data['observations'])
    period=1/hz
    if not points[0][0]<=period<=points[-1][0]:
        raise ValueError('Modulation rate outside measured interval')
    for (p0,n0),(p1,n1) in zip(points,points[1:]):
        if p0<=period<=p1:
            loops=round(n0+(n1-n0)*(period-p0)/(p1-p0)); break
    cycles=round(hz*seconds)
    if not 1<=cycles<=255: raise ValueError('Cycle count must fit the 8-bit gate driver')
    return dict(requested_modulation_hz=hz,half_period_loops=loops,cycles=cycles,
                nominal_duration_s=cycles/hz)
if __name__=='__main__':
    print(json.dumps([recipe(hz) for hz in (100,200,400)],indent=2))
