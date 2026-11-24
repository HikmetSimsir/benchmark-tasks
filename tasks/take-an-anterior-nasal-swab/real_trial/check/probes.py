"""Scorer probes for take-an-anterior-nasal-swab (stubbed simulator state; no Isaac Sim).
Usage (from this folder):
    python probes.py ../../task.py
"""
import os, sys, math
sys.path.insert(0, os.getcwd())
import numpy as np
import harness
from harness import Sim
import scenarios as S0
D, DEG = 0.0125, math.pi / 180

def left_on_tube(sim):
    m = sim.m; H = m.KIT_POS + np.array([0.0, m.HOLD_Y, m.TUBE_Z - m.TOP])
    return np.array([H + np.array([s * 0.011, -0.01 + 0.02 * j / 11, 0.0]) for s in (-1, 1) for j in range(12)])

def run2(path, fn, cap="held", push=3.0, seed=0, release_steps=190):
    rng = np.random.default_rng(seed); sim = Sim(path); sim.out_of_tube(); res = None
    for k in ("left", "right"):
        if fn is not None:
            for (a, r, f) in fn(rng): res = sim.press_at(k, D, a, r, f)
        sim.out_of_tube(3)
    m = sim.m; R = harness.frame_from_axis(np.array([0.0, 1.0, 0.0]))
    sp = np.array([m.TUBE_X, m.Y_MOUTH - m.GRIP_L / 2 + 0.0002, m.TUBE_Z])
    for i in range(10):
        res = sim.step(sp, R, push=push, fingers_right=sim.holding(sp), fingers_left=left_on_tube(sim) if cap == "held" else None)
    for i in range(release_steps): res = sim.step(sp, R, push=0.05)
    return sim, res

def good_slow(n=320, c=5): return lambda rng: [(2 * math.pi * c * i / n, 0.6, 1.0) for i in range(n)]
def demo_like(stick=0.25, fdrop=0.15):
    def f(rng):
        out = []; a = 0.0; rate = 6 * 360 / 312
        for i in range(312):
            if rng.random() > stick: a += rate / (1 - stick) * DEG
            out.append((a, 0.6, 1.0 if rng.random() > fdrop else 0.1))
        return out
    return f
def microdab(n=6, step=2.0, laps=5):
    order = [0, 6, 1, 7, 2, 8, 3, 9, 4, 10, 5, 11]
    def f(rng):
        out = []
        for lap in range(laps):
            for s in order:
                a0 = (30 * s + 5) * DEG
                out += [(a0 + j * step * DEG, 0.6, 1.0) for j in range(n)] + [(a0, 0.0, 0.0)]
        return out
    return f
def fast_wiggle40(nw=200, amp=1.5):
    return lambda rng: [(i * 40 * DEG, 0.6, 1.0) for i in range(37)] + [((amp if i % 2 else -amp) * DEG, 0.6, 1.0) for i in range(nw)]
def fwd_ratchet2(cycles=80):
    def f(rng):
        out = []; a = 0.0
        for c in range(cycles):
            for j in range(3): a += 10 * DEG; out.append((a, 0.6, 1.0))
            a -= 20 * DEG; out.append((a, 0.6, 0.1))
        return out
    return f
def ratchet_plus_circle(strokes=70):
    def f(rng):
        out = []
        for s in range(strokes): out += [(10 * j * DEG, 0.6, 1.0) for j in range(4)] + [(0.0, 0.6, 0.0)]
        return out + [(i * 7 * DEG, 0.6, 1.0) for i in range(52)]
    return f
def ratchet_plus_wedge(strokes=70):
    def f(rng):
        out = []
        for s in range(strokes): out += [(10 * j * DEG, 0.6, 1.0) for j in range(4)] + [(0.0, 0.6, 0.0)]
        return out + [((30 * s + 15) * DEG, 0.15, 1.0) for s in range(12)]
    return f

SUITE = [("good 5c/16s", good_slow()), ("reversal 2CW+2CCW", S0.reversal), ("demo-like stick.15 drop.12", demo_like(0.15, 0.12)),
         ("demo-like stick.25 drop.15", demo_like(0.25, 0.15)), ("ratchet one spot", S0.ratchet),
         ("ratchet + 1 circle", ratchet_plus_circle()), ("ratchet + wedge sectors", ratchet_plus_wedge()),
         ("microdab star 6x2deg", microdab()), ("microdab star 6x1.2deg", microdab(6, 1.2, 4)), ("fast4 + wiggle", fast_wiggle40()),
         ("fwd ratchet 3f/1b x80", fwd_ratchet2(80)), ("pingpong noisy", S0.pingpong_noisy), ("wiggle +-30", S0.wiggle),
         ("fast then still", S0.fast_then_still), ("wedged axis", S0.wedged_axis), ("still", S0.still),
         ("light/no press", lambda rng: [(2 * math.pi * 5 * i / 320, 0.6, 0.1) for i in range(320)])]

def fmt(sim, res):
    n = sim.report()["nostrils"]["left"]
    return f"{res[0]:.3f}/{'S' if res[1] else '-'} ({n['circles']:.2f}c mv{n['moving_steps']} sec{n['sectors']})"

if __name__ == "__main__":
    paths = sys.argv[1:] or ["../../task.py"]
    for name, fn in SUITE:
        print(f"{name:28s}", " | ".join(fmt(*run2(p, fn)) for p in paths))
    for p in paths:
        print(p, "cap 2.5 N no other hand:", run2(p, good_slow(), cap="free", push=2.5)[1],
              "| other hand:", run2(p, good_slow(), cap="held", push=2.5)[1], "| capped unsampled:", run2(p, None)[1])
