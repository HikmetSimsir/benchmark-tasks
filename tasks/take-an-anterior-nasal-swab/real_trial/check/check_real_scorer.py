"""Equivalence check: probe scenarios through task.py (stubbed state) vs. real_trial/score_real_trial.py fed a synthetic
80 Hz load-cell log of the same presses (wall normal force + friction mu along the travel + 3 mN noise per axis), with
2 s of nothing touching before and 1.5 s after, as the logging protocol requires. Run from this folder:
    python check_real_scorer.py      (writes check_real_scorer_results.json)"""
import os, sys, math, importlib.util
sys.path.insert(0, os.getcwd())
import numpy as np
import scenarios as S
spec = importlib.util.spec_from_file_location("srt", "../score_real_trial.py")
srt = importlib.util.module_from_spec(spec); spec.loader.exec_module(srt)
A, B = srt.A_SEMI, srt.B_SEMI
MU, NOISE, HZ = 0.4, 0.003, 80

def real_log(seq, rng, mu=MU, noise=NOISE, hx711=False):
    """seq: [(ang, rad, f)] per 0.05 s step -> 80 Hz samples (t, fu, fv) of the force the insert feels. Friction mu*f
    acts while the tip touches (f > 0) and slides along the wall, in the direction it moved since the last step (none
    on a step that follows a lift, where the tip arrived radially); a wedged tip (centre near the axis) presses
    opposite walls, so the net force is +-10% of f."""
    ts, fu, fv = [], [], []
    n = len(seq)
    for i in range(n):
        ang, rad, f = seq[i]
        nrm = np.array([math.cos(ang) / A, math.sin(ang) / B]); nrm /= np.linalg.norm(nrm)
        F = f * nrm
        wedged = rad < 0.25
        if wedged:
            F = F * rng.uniform(-0.1, 0.1)
        if i > 0 and f > 0 and seq[i - 1][2] > 0 and not wedged and seq[i - 1][1] >= 0.25:
            d = (ang - seq[i - 1][0] + math.pi) % (2 * math.pi) - math.pi
            if abs(d) > 1e-6:
                tan = np.array([-A * math.sin(ang), B * math.cos(ang)]); tan /= np.linalg.norm(tan)
                F = F + mu * f * math.copysign(1.0, d) * tan
        for q in range(HZ // 20):  # samples inside this step, the last one at the step's end
            G = F + rng.normal(0, noise, 2)
            ts.append(i * 0.05 - 0.05 + (q + 1) * 0.05 / (HZ // 20)); fu.append(G[0]); fv.append(G[1])
    if hx711:  # the HX711's own settling at 80 samples/s (about 50 ms): a (1, 3, 3, 1)/8 average over its last 4 outputs
        k = np.array([1.0, 3.0, 3.0, 1.0]) / 8
        fu = list(np.convolve(np.r_[[fu[0]] * 3, fu], k, "valid")); fv = list(np.convolve(np.r_[[fv[0]] * 3, fv], k, "valid"))
    return ts, fu, fv

LEAD, TAIL = 40, 30  # steps of nothing touching before and after the pressing (the log's zero checks)
DEG = math.pi / 180


def mklog(seq, mu=MU, seed=1, hx711=False):
    full = [(0.0, 0.6, 0.0)] * LEAD + list(seq) + [(0.0, 0.6, 0.0)] * TAIL
    ts, fu, fv = real_log(full, np.random.default_rng(seed), mu=mu, hx711=hx711)
    return ts, fu, fv, (LEAD * 0.05, (LEAD + len(seq) - 1) * 0.05)


def real(ts, fu, fv, span, **kw):
    try:
        return srt.score_log(ts, fu, fv, {"left": [span], "right": []}, sync=0.0, **kw)["nostrils"]["left"]
    except SystemExit as e:
        return {"refused": str(e)}


def sim_left(fn, basic=False, name=""):
    sim, res = S.run(name, fn) if basic else P.run2("../../task.py", fn)
    return sim.report()["nostrils"]["left"]


ROWS = []


def row(group, name, p, r, note=""):
    ROWS.append(dict(group=group, probe=name, task_py=p, real_log=r, note=note))
    a = f"{p['credit']:.3f}" if p else "  -  "
    b = f"{r['credit']:.3f}" if "credit" in r else "refused: " + r["refused"][:60]
    print(f"{group:8s} {name:46s} task.py {a:6s} real {b} {note}")


def nrm_at(ang):
    v = np.array([math.cos(ang) / A, math.sin(ang) / B]); return v / np.linalg.norm(v)


import probes as P

# 1. basic scenarios and 2. the exploit suite: the same tip pattern through both scorers
names = ["good", "reversal", "still", "fast_then_still", "wiggle", "ratchet", "stardab", "pingpong", "pingpong_noisy",
         "pingpong_long", "wedged_axis", "wedged_noise"]
for name in names:
    fn = getattr(S, name); ts, fu, fv, span = mklog(fn(np.random.default_rng(0)))
    row("basic", name, sim_left(fn, True, name), real(ts, fu, fv, span))
for name, fn in P.SUITE:
    ts, fu, fv, span = mklog(fn(np.random.default_rng(0)))
    row("exploit", name, sim_left(fn), real(ts, fu, fv, span))


# 3. circles with an unpressed arc every lap (task.py tolerates up to two unpressed sectors through its signed travel)
def gap(W, a0, c=6, n=320):
    return lambda rng: [(2 * math.pi * c * i / n, 0.6, 0.1 if (360 * c * i / n - a0) % 360 < W else 1.0)
                        for i in range(n)]


for W, a0 in [(30, 15), (45, 0), (60, 10), (90, 100), (120, 200)]:
    fn = gap(W, a0); ts, fu, fv, span = mklog(fn(np.random.default_rng(0)))
    row("gap", f"6 circles, unpressed {W} deg arc each lap", sim_left(fn), real(ts, fu, fv, span))

# 4. friction of foam on printed PLA (0.4 assumed above)
for mu in (0.8, 1.0):
    for name, fn in (("good 5c/16s", P.good_slow()), ("demo-like stick.15 drop.12", P.demo_like(0.15, 0.12))):
        ts, fu, fv, span = mklog(fn(np.random.default_rng(0)), mu=mu)
        row("friction", f"{name}, mu {mu}", sim_left(fn), real(ts, fu, fv, span))
worst_mu = []
for name, fn in P.SUITE:
    ts, fu, fv, span = mklog(fn(np.random.default_rng(0)), mu=0.8)
    r = real(ts, fu, fv, span); p = sim_left(fn); worst_mu.append(r["credit"] - p["credit"])
print("exploit suite at mu 0.8: real minus task.py at most %+.3f" % max(worst_mu))

# 5. other contacts on the insert: the log cannot tell them from the foam, so the video voids that nostril
good = P.good_slow(); seq = good(np.random.default_rng(0)); ts, fu, fv, span = mklog(seq)
fv2 = [v + (1.0 if span[0] + 8.0 <= t <= span[1] else 0.0) for t, v in zip(ts, fv)]
row("void", "5 circles + 1.0 N other contact from 8 s", sim_left(good), real(ts, fu, fv2, span), "void rule (video)")
row("void", "  same, nostril voided (--void-nostril)", sim_left(good), real(ts, fu, fv2, span, void_nostrils=("left",)))
n = 320; angs = [2 * math.pi * 5 * i / n for i in range(n)]
free = lambda rng: [(a, 0.3, 0.0) for a in angs]
seqF = [(0.0, 0.6, 0.0)] * LEAD + [(a, 0.6, 0.5) for a in angs] + [(0.0, 0.6, 0.0)] * TAIL  # 0.5 N on the rim, rotating
ts, fu, fv = real_log(seqF, np.random.default_rng(1), mu=0.0)
row("void", "tip free, shaft pressed on a rim 0.5 N, x5", sim_left(free), real(ts, fu, fv, (LEAD * 0.05, (LEAD + n - 1) * 0.05)),
    "void rule (video)")

# 6. logs the rules cannot be applied to are refused
ts, fu, fv, span = mklog(seq)
k = 8; m = len(ts) // k * k
row("refused", "logged at 10 samples/s", None, real(list(np.asarray(ts[:m]).reshape(-1, k)[:, -1]),
    list(np.asarray(fu[:m]).reshape(-1, k).mean(1)), list(np.asarray(fv[:m]).reshape(-1, k).mean(1)), span))
row("refused", "raw counts (not calibrated)", None, real(ts, [u * 2000 for u in fu], [v * 2000 for v in fv], span))
row("refused", "0.3 N on the insert when the log starts", None, real(ts, [u + 0.3 for u in fu], fv, span))
row("refused", "0.3 N left on the insert at the end", None, real(ts, [u + (0.3 if t > span[1] else 0) for t, u in zip(ts, fu)], fv, span))

# 7. the logger's clock 0.5% slow: corrected from record_log.py's PC times
import csv, os, tempfile
long_seq = [(0.0, 0.6, 0.0)] * 2400 + list(seq)  # the nostril starts 2 min into the log
tsL, fuL, fvL, spanL = mklog(long_seq)
spanL = (spanL[0] + 2400 * 0.05, spanL[1])
tmp = os.path.join(tempfile.mkdtemp(), "log.csv")
with open(tmp, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["t_s", "f_u_n", "f_v_n", "led", "pc_s"])
    for t, u, v in zip(tsL, fuL, fvL):
        w.writerow([f"{t * 0.995:.4f}", f"{u:.4f}", f"{v:.4f}", int(t < 0.5), f"{t + 0.004:.4f}"])
for name, args in (("uncorrected", ([t * 0.995 for t in tsL], fuL, fvL)), ("corrected (pc_s)", srt.read_log(tmp))):
    r = real(*args, spanL)
    row("clock", f"logger clock 0.5% slow, {name}", sim_left(good), r, f"share {r['share']:.2f}, pressed {r['pressed_s']} s")

# 8. an unpressed arc at every phase (36 starting angles, 10 degrees apart), friction 0.4 and 0.8
for W in (30, 45, 60, 75, 90):
    for mu in (0.4, 0.8):
        cr, tp = [], []
        for a0 in range(0, 360, 10):
            fn = gap(W, a0); ts, fu, fv, span = mklog(fn(np.random.default_rng(0)), mu=mu)
            cr.append(real(ts, fu, fv, span)["credit"]); tp.append(sim_left(fn)["credit"])
        r = dict(credit=min(cr), median=float(np.median(cr)), below_0_9=int(sum(x < 0.9 for x in cr)))
        row("phases", f"6 circles, unpressed {W} deg arc, 36 phases, mu {mu}", dict(credit=min(tp)), r,
            f"real median {r['median']:.3f}, {r['below_0_9']}/36 phases below 0.9; task.py {min(tp):.3f}-{max(tp):.3f}")
# 9. the exploit suite with the HX711's own 50 ms settling and/or the 0.05 s steps half a step off the robot's
for mu in (0.4, 0.8, 1.0):
    for hx, sh in ((True, 0.0), (False, 0.025), (True, 0.025)):
        worst = (-9.0, "")
        for name, fn in P.SUITE:
            ts, fu, fv, span = mklog(fn(np.random.default_rng(0)), mu=mu, hx711=hx)
            d = real(ts, fu, fv, (span[0] + sh, span[1] + sh))["credit"] - sim_left(fn)["credit"]
            worst = max(worst, (d, name))
        print("exploit suite, mu %.1f, HX711 settling %s, steps offset %.3f s: real minus task.py at most %+.3f (%s)"
              % (mu, hx, sh, worst[0], worst[1]))
# 11. star-order micro-dabs with one-step lifts when the log cannot show the lift: the HX711's 50 ms settling, or the
#     0.05 s steps half a step off the robot's; and the same dabs with no lift at all (the tip hops across in one step)
def nolift(fn):
    return lambda rng: [x for x in fn(rng) if x[2] > 0]
for name, fn in (("microdab star 6x1.2deg", P.microdab(6, 1.2, 4)), ("microdab star 6x2deg", P.microdab())):
    for label, kw, sh in (("HX711 settling", dict(hx711=True), 0.0), ("steps half a step off", {}, 0.025)):
        ts, fu, fv, span = mklog(fn(np.random.default_rng(0)), **kw)
        row("dabs", f"{name}, {label}", sim_left(fn), real(ts, fu, fv, (span[0] + sh, span[1] + sh)))
    ts, fu, fv, span = mklog(nolift(fn)(np.random.default_rng(0)))
    row("dabs", f"{name}, no lift", sim_left(nolift(fn)), real(ts, fu, fv, span))

# 12. dabs that hop about 120 degrees at a time (one-step lifts): the residual the 60-degree rule does not close when
#     the HX711's settling and a half-step offset blur a hop into two 60-degree steps
def stride(rng, hop=120, n_dabs=60):
    out, a = [], 5.0
    for k in range(n_dabs):
        out += [((a + 2.0 * j) * DEG, 0.6, 1.0) for j in range(6)] + [(a * DEG, 0.0, 0.0)]
        a = (a + hop) % 360
    return out
for mu, hx, sh in ((0.4, False, 0.0), (0.8, True, 0.025)):
    ts, fu, fv, span = mklog(stride(None), mu=mu, hx711=hx)
    row("dabs", f"120-degree hops, 6 x 2 deg, mu {mu}, HX711 {hx}, offset {sh}", sim_left(stride),
        real(ts, fu, fv, (span[0] + sh, span[1] + sh)))

# 10. an at-depth interval outside the log (a wrong --sync) is refused
ts, fu, fv, span = mklog(seq)
row("refused", "at-depth interval 30 s after the log ends", None, real(ts, fu, fv, (span[0] + 30.0, span[1] + 30.0)))

sc = [r for r in ROWS if r["group"] in ("basic", "exploit", "gap", "friction") and "credit" in r["real_log"]]
d = [r["real_log"]["credit"] - r["task_py"]["credit"] for r in sc if r["task_py"]]
print("real minus task.py credit over basic, exploit, gap and friction probes: at most %+.3f, at least %+.3f" % (max(d), min(d)))
full = [r for r in sc if r["task_py"] and r["task_py"]["credit"] >= 0.999]
print("probes task.py scores 1.0: real credit %s" % sorted({round(r["real_log"]["credit"], 3) for r in full}))
import json
json.dump(ROWS, open("check_real_scorer_results.json", "w"), indent=1)
