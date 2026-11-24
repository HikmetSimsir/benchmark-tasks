import os, sys, math
sys.path.append(os.getcwd())
import numpy as np
from harness import Sim, summary

D = 0.0125  # tip centre depth (m)
def run(name, pattern_fn, cap=True, push=3.0, path="../../task.py", seed=0):
    rng = np.random.default_rng(seed)
    sim = Sim(path)
    sim.out_of_tube()
    res = None
    for k in ("left", "right"):
        for (ang, rad, f) in pattern_fn(rng):
            res = sim.press_at(k, D, ang, rad, f)
        sim.out_of_tube(3)
    if cap == "unsampled":
        pass
    if cap:
        res = sim.cap_home(push=push)
    else:
        res = sim.out_of_tube(70) and sim.m._update(None)
    return sim, res

def good(rng):        # 5 pressed circles in 16 s
    return [(2*math.pi*5*i/320, 0.6, 1.0) for i in range(320)]
def ratchet(rng):     # 30-degree pressed stroke, lift, return; repeat (one spot)
    out=[]
    for s in range(50):
        out += [(math.radians(10*j), 0.6, 1.0) for j in range(4)]
        out += [(0.0, 0.6, 0.0)]
    return out
def pingpong(rng):    # side-to-side across the short axis every step, pressed at both walls
    return [((math.pi/2) if i%2==0 else (-math.pi/2), 0.52, 1.0) for i in range(220)]
def pingpong_noisy(rng):
    return [((math.pi/2 if i%2==0 else -math.pi/2) + rng.normal(0, math.radians(10)), 0.52, 1.0) for i in range(220)]
def pingpong_long(rng):  # along the long axis
    return [((0.0 if i%2==0 else math.pi) + rng.normal(0, math.radians(10)), 0.66, 1.0) for i in range(220)]
def wiggle(rng):      # +-30 deg at one spot, continuously pressed (like one_spot)
    return [(math.radians(30)*math.sin(2*math.pi*i/20), 0.6, 1.0) for i in range(320)]
def stardab(rng):     # poke 12 sectors across the nostril, unpressed transit through the axis
    order=[0,6,1,7,2,8,3,9,4,10,5,11]
    out=[]
    for lap in range(4):
        for sct in order:
            a=math.radians(30*sct+15)
            out += [(a,0.6,1.0)]*5 + [(a,0.0,0.0)]
    return out
def reversal(rng):    # 2 CW then 2 CCW pressed circles
    out=[(2*math.pi*2*i/160, 0.6, 1.0) for i in range(160)]
    out+=[(2*math.pi*2*(160-i)/160, 0.6, 1.0) for i in range(160)]
    return out
def fast_then_still(rng):  # 4 circles in 16 steps (0.8 s), then 190 steps pressed in one spot
    return [(2*math.pi*4*i/16, 0.6, 1.0) for i in range(17)] + [(0.0, 0.6, 1.0)]*190
def wedged_axis(rng):  # tip centre near the axis, pressed by a wedge, jitter
    return [(rng.uniform(-math.pi, math.pi), 0.1, 1.5) for i in range(320)]
def wedged_noise(rng): # tip centre at r 0.6, jitter +-5 deg, force flickering around 0.2 N
    return [(rng.normal(0, math.radians(5)), 0.6, rng.choice([0.1, 0.4])) for i in range(320)]
def still(rng):        # pressed in one spot, no motion
    return [(0.3, 0.6, 1.0)]*320

pats = dict(good=good, ratchet=ratchet, pingpong=pingpong, pingpong_noisy=pingpong_noisy, pingpong_long=pingpong_long,
            wiggle=wiggle, stardab=stardab, reversal=reversal, fast_then_still=fast_then_still,
            wedged_axis=wedged_axis, wedged_noise=wedged_noise, still=still)
if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../../task.py"
    for name, fn in pats.items():
        sim, res = run(name, fn, path=path)
        print(f"{name:16s}", summary(sim, res))
    # no cap pushed
    sim, res = run("good_nocap", good, push=0.0, path=path); print(f"{'good_nopush':16s}", summary(sim, res))
