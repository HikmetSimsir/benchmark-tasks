"""Score a real trial of take-an-anterior-nasal-swab with task.py's per-nostril rules and constants.

The simulation reads the foam tip's wall force from PhysX contacts and the tip centre's angle round each nostril from
its pose. In a real trial the nose insert hangs on a two-axis load-cell stack (see README, 'Real-world trials'), so the
log gives the net force on the insert across the nostrils' common axis about 80 times a second:
    F_u along the nostrils' long axis (toward the nose tip; task.py's UX), F_v across the face (task.py's VX).
While the foam is the only thing touching the nose, that force is the foam's push on the wall. A tip pressed on the
wall at elliptical angle theta pushes it outward along the ellipse's normal there, whose direction phi satisfies
tan(phi) = (A/B) tan(theta); so theta = atan2(B sin(phi), A cos(phi)) recovers task.py's angle, and |F| >= 0.20 N is
the press. Anything else touching the nose while a tip is at depth (a gripper, the tube, a cable, the shaft bearing on
a rim) voids that nostril (--void-nostril, from the video): the log cannot tell it from the foam.

Deliberate differences from task.py (real_trial/README.md, 'Check against task.py'):
1. Circles are laps: all twelve 30-degree sectors pressed since the last lap, or at least 10 of them over a full turn
   of continuous pressed travel. task.py takes the larger of the signed travel and the laps, but rubbing friction tilts
   the measured force by atan(mu) (about 22 degrees at mu 0.4) whenever a stroke starts or reverses, which would add or
   remove apparent travel.
2. A pressed step is moving only if it turns the same way as the last second of pressed moves (the friction lead swings
   back when the tip pauses).
3. Friction adds to |F| while the tip slides (sqrt(1 + mu^2): 8% at mu 0.4), so a sliding step counts as pressed from
   about 0.19 N of wall force; a still one from 0.20 N, as in task.py.
4. There is one net force, so task.py's exclusion of a tip wedged across the nostril's axis has no counterpart: a wedged
   swab loads the insert only as hard as the robot pushes it sideways.
5. A turn of more than 60 degrees between pressed steps (task.py: 90) is a hop across the nostril and starts a new lap,
   as a lift does: the HX711's 50 ms settling and the 0.05 s steps can hide a one-step lift between dabs.
6. Anything but the foam touching the nose while a tip is at depth voids that nostril (--void-nostril, from the video);
   task.py reads only the foam's own contact points.

The video gives, for each nostril, the intervals with the tip at sampling depth: the line 1.6 cm from the tip's end
hidden in that nostril and the line at 2.5 cm still outside it.

    python score_real_trial.py trial_01.csv --sync 12.40 --left 15.2 33.0 --right 37.1 55.6 [--cap-home] [--void]
        [--void-nostril left right]

trial_01.csv: columns t_s, f_u_n, f_v_n, led (from the logger) and pc_s (record_log.py's PC clock).
--sync: the video time of the logger's start flash (the log's t_s = 0), so video time = t_s + sync. When pc_s is
  present the logger's clock is rescaled to the PC's (an Uno's ceramic resonator may run up to 0.5% off).
--left/--right: one or more at-depth intervals (video seconds, in pairs) for the patient's left / right nostril.
The log must run at 80 samples/s, be in newtons, and start and end with nothing touching the nose (check_log).
"""
import argparse
import csv
import json
import math

# -- the same constants as task.py ------------------------------------------------------------------------------------
A_SEMI, B_SEMI = 0.0070, 0.0050  # elliptical nostril half-widths (m)
F_WALL = 0.20  # N: a step is pressed
F_MAX = 5.0  # N: reported, not scored
CIRCLES = 4.0
SHARE = 0.70
MIN_PRESSED = 200  # moving pressed steps (10 s at 20 Hz)
MOVE_MIN = math.radians(1.0)  # per 0.05 s step
SECTORS = 10
DT = 0.05  # the simulation's control step; the log is averaged over each one
JUMP = math.radians(60.0)  # a larger turn between pressed steps is a hop across the nostril, not a slide (difference 5)
CAP_FACTOR = 0.4  # an unsealed specimen keeps 40%
MAX_DT = 0.015  # s: the largest median sample interval (both HX711s at 80 samples/s, not their 10/s default)
F_ZERO = 0.05  # N: the log's first and last second, with nothing touching the nose, must read below this
F_SANE = 50.0  # N: a larger force means an uncalibrated log (raw counts)
F_RATED = 9.0  # N: just under the 1 kg cells' 9.8 N rating; a larger peak calls for the in-place check before the next trial


def check_log(ts, fus, fvs) -> None:
    """Refuse a log the rules cannot be applied to: too slow, not in newtons, or not at zero at its start and end."""
    dts = sorted(b - a for a, b in zip(ts, ts[1:]))
    if not dts or dts[len(dts) // 2] > MAX_DT:
        raise SystemExit(f"log rate below 80 samples/s (median interval {dts[len(dts) // 2] if dts else 0:.3f} s): "
                         "set both HX711 boards to 80 samples/s")
    if ts[-1] - ts[0] < 3.0:
        raise SystemExit("log shorter than 3 s")
    if max(max(map(abs, fus)), max(map(abs, fvs))) > F_SANE:
        raise SystemExit("forces above 50 N: enter the calibration (COUNTS_PER_N_U/V) in force_logger.ino")
    for name, keep in (("first", lambda t: t <= ts[0] + 1.0), ("last", lambda t: t >= ts[-1] - 1.0)):
        f = sorted(math.hypot(u, v) for t, u, v in zip(ts, fus, fvs) if keep(t))
        if f[len(f) // 2] > F_ZERO:
            raise SystemExit(f"the insert reads {f[len(f) // 2]:.3f} N in the log's {name} second: start the log with "
                             "nothing touching the nose and stop it 2 s after the swab is out; if the insert was "
                             "knocked, repeat the in-place check")


def sector(ang: float) -> int:
    return int(((ang + 2 * math.pi) % (2 * math.pi)) // (math.pi / 6))


def wall_angle(fu: float, fv: float) -> float:
    """Elliptical angle (task.py's atan2(v / B, u / A)) of the wall point pushed along force direction (fu, fv)."""
    phi = math.atan2(fv, fu)
    return math.atan2(B_SEMI * math.sin(phi), A_SEMI * math.cos(phi))


class Nostril:
    """task.py's per-nostril tally (_update, '-- sampling in each nostril'), fed one 0.05 s step at a time."""

    def __init__(self):
        self.depth_steps = self.contact_steps = self.moving = self.laps = 0
        self.travel, self.fmax = 0.0, 0.0
        self.ang = self.prev = None
        self.lap_travel = 0.0  # signed travel since the current lap began (reset by a jump across the nostril)
        self.sectors, self.cur, self.forces = set(), set(), []
        self.hard = False
        self.recent = []  # the last second (20 steps) of continuous pressed moves, for the turning direction

    def step(self, at_depth: bool, fu: float, fv: float) -> None:
        if not at_depth:
            self.ang = None
            self.recent = []
            return
        self.depth_steps += 1
        f = math.hypot(fu, fv)
        if f > F_MAX:
            self.hard = True
        if f < F_WALL:
            self.ang = None
            self.recent = []
            return
        self.contact_steps += 1
        self.fmax = max(self.fmax, f)
        self.forces.append(f)
        ang = wall_angle(fu, fv)
        self.sectors.add(sector(ang))
        if self.ang is not None:
            dlt = (ang - self.ang + math.pi) % (2 * math.pi) - math.pi
            if abs(dlt) <= JUMP:  # a continuous move: its travel and the sectors it swept count
                self.travel += dlt
                self.lap_travel += dlt
                # moving: as in task.py (>= 1 degree in the step), and the same way round as the last second of pressed
                # moves, so the friction lead's swing back when the tip pauses (about 22 degrees) is not a move
                turning = sum(self.recent)
                self.moving += abs(dlt) >= MOVE_MIN and (turning == 0 or (dlt > 0) == (turning > 0))
                self.recent = (self.recent + [dlt])[-20:]
                for fr in (0.25, 0.5, 0.75, 1.0):
                    self.cur.add(sector(self.ang + fr * dlt))
            else:  # pressed on both sides of a jump across the nostril: a lift too short for the log to show
                self.cur = set()
                self.lap_travel = 0.0
                self.recent = []
            self.cur.add(sector(ang))
        else:
            jump = None if self.prev is None else (ang - self.prev + math.pi) % (2 * math.pi) - math.pi
            if jump is not None and abs(jump) <= math.pi / 2:
                self.travel += jump  # lifted and pressed again: the way back off the wall counts against travel
                self.lap_travel += jump
            elif jump is not None:
                self.cur = set()  # a jump across the nostril: a new lap starts
                self.lap_travel = 0.0
            self.cur.add(sector(ang))
        if len(self.cur) == 12 or (len(self.cur) >= SECTORS and abs(self.lap_travel) >= 2 * math.pi):
            # a lap, either direction: all twelve sectors pressed since the last lap, or at least 10 of them over a
            # full turn of continuous pressed travel (task.py's signed travel also tolerates an unpressed arc)
            self.laps += 1
            self.cur = {sector(ang)}
            self.lap_travel = 0.0
        self.ang = self.prev = ang

    def result(self) -> dict:
        laps = self.laps + max(len(self.cur) - 1, 0) / 12
        # Circles are the laps only (difference 1 in the docstring): a measured force direction leads the contact point
        # by atan(mu) while the tip slides, so every start or reversal of a stroke would add or remove about 22 degrees
        # of apparent signed travel.
        circles = laps
        share = self.contact_steps / max(self.depth_steps, 1)
        credit = (min(circles, CIRCLES) / CIRCLES * min(1.0, share / SHARE)
                  * min(1.0, self.moving / MIN_PRESSED) * min(1.0, len(self.sectors) / SECTORS))
        fs = sorted(self.forces)
        return dict(circles=round(circles, 2), travel_turns=round(self.travel / (2 * math.pi), 2), share=round(share, 2), moving_s=round(self.moving * DT, 2),
                    moving_steps=self.moving, sectors=len(self.sectors), depth_s=round(self.depth_steps * DT, 2),
                    pressed_s=round(self.contact_steps * DT, 2), credit=round(credit, 3),
                    f_median=round(fs[len(fs) // 2], 2) if fs else 0.0, f_max=round(self.fmax, 2), too_hard=self.hard)


def bin_force(ts, fus, fvs, t, i0=0):
    """Mean logged force over the 0.05 s step ending at log time t (the HX711 at 80 samples/s settles in 50 ms, so
    each step holds about 4 samples); the nearest sample if the step holds none. Returns (fu, fv, next index)."""
    n = len(ts)
    i = i0
    while i < n and ts[i] <= t - DT:
        i += 1
    j, su, sv = i, 0.0, 0.0
    while j < n and ts[j] <= t:
        su += fus[j]
        sv += fvs[j]
        j += 1
    if j > i:
        return su / (j - i), sv / (j - i), i
    k = min(range(max(i - 1, 0), min(i + 1, n - 1) + 1), key=lambda q: abs(ts[q] - t))
    return fus[k], fvs[k], i


def score_log(ts, fus, fvs, intervals: dict, sync: float = 0.0, cap_home: bool = True, void: bool = False,
              void_nostrils=()) -> dict:
    """intervals: {'left': [(t0, t1), ...], 'right': [...]} in video seconds; log time = video time - sync.
    void_nostrils: nostrils in which something other than the foam touched the nose while the tip was at depth."""
    check_log(ts, fus, fvs)
    lo, hi = ts[0] + sync, ts[-1] + sync  # the log's span on the video's clock
    for k, spans in intervals.items():
        for a, b in spans:
            if not lo <= a < b <= hi:
                raise SystemExit(f"{k} interval {a}-{b} s is not inside the log ({lo:.2f}-{hi:.2f} s on the video's "
                                 "clock): check --sync and the interval times")
    f_peak = max(math.hypot(u, v) for u, v in zip(fus, fvs))
    per = {}
    for k in ("left", "right"):
        tally = Nostril()
        spans = intervals.get(k, [])
        if spans:
            t0, t_end = min(a for a, _ in spans), max(b for _, b in spans)
            i, n_steps = 0, int(round((t_end - t0) / DT)) + 1
            for q in range(n_steps):
                t = t0 + q * DT
                at_depth = any(a - 1e-9 <= t <= b + 1e-9 for a, b in spans)
                fu, fv, i = bin_force(ts, fus, fvs, t - sync, i)
                tally.step(at_depth, fu, fv)
        per[k] = tally.result()
        per[k]["voided"] = k in void_nostrils
        if per[k]["voided"]:
            per[k]["credit"] = 0.0
    swab = (per["left"]["credit"] + per["right"]["credit"]) / 2
    score = 0.0 if void else swab * (1.0 if cap_home else CAP_FACTOR)
    full = (not void and cap_home and all(p["circles"] >= CIRCLES and p["share"] >= SHARE
                                          and p["moving_steps"] >= MIN_PRESSED and p["sectors"] >= SECTORS
                                          and not p["voided"] for p in per.values()))
    return dict(score=round(score, 3), full_credit=full, nostrils=per, cap_home=cap_home, voided=void,
                log_peak_n=round(f_peak, 2), recheck_rig=f_peak > F_RATED)  # above the cells' rating: re-check the rig


def read_log(path):
    """(t_s, f_u_n, f_v_n) from a logger CSV; with record_log.py's pc_s column the logger's clock is rescaled to the
    PC's by a least-squares fit over the whole log (USB delivery jitter averages out)."""
    ts, fus, fvs, pcs = [], [], [], []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            ts.append(float(row["t_s"]))
            fus.append(float(row["f_u_n"]))
            fvs.append(float(row["f_v_n"]))
            if row.get("pc_s") not in (None, ""):
                pcs.append(float(row["pc_s"]))
    if len(pcs) == len(ts) > 1:
        mt, mp = sum(ts) / len(ts), sum(pcs) / len(pcs)
        rate = sum((t - mt) * (q - mp) for t, q in zip(ts, pcs)) / sum((t - mt) ** 2 for t in ts)
        if abs(rate - 1.0) > 0.02:
            raise SystemExit(f"the logger's clock runs {100 * (1 / rate - 1):+.1f}% against the PC's: check the board")
        ts = [t * rate for t in ts]
    return ts, fus, fvs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log")
    ap.add_argument("--sync", type=float, required=True, help="video time (s) of the logger's start flash")
    ap.add_argument("--left", type=float, nargs="+", default=[], help="at-depth intervals, video s: t0 t1 [t0 t1 ...]")
    ap.add_argument("--right", type=float, nargs="+", default=[])
    ap.add_argument("--cap-home", action="store_true", help="cap flush on the rim (photo), pushed while the other hand held the tube (video)")
    ap.add_argument("--void-nostril", nargs="+", default=[], choices=["left", "right"],
                    help="something other than the foam (a gripper, the tube, a cable, the shaft bearing on a rim) touched "
                         "the nose while this nostril's tip was at depth (video)")
    ap.add_argument("--void", action="store_true", help="green on the foam (lip, skin beyond the rims, the tube's outside or the stand), a gripper on the foam, "
                         "the 2.5 cm line inside a nostril, or the swab dropped")
    a = ap.parse_args()
    if len(a.left) % 2 or len(a.right) % 2:
        ap.error("intervals come in pairs")
    iv = {"left": list(zip(a.left[::2], a.left[1::2])), "right": list(zip(a.right[::2], a.right[1::2]))}
    ts, fus, fvs = read_log(a.log)
    print(json.dumps(score_log(ts, fus, fvs, iv, a.sync, a.cap_home, a.void, a.void_nostril), indent=1))


if __name__ == "__main__":
    main()
