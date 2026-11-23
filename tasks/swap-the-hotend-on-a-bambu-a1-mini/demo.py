"""Scripted demo: swap the A1 mini's hotend, and the failure / shortcut variants.

The right arm pinches the buckle's tab (at its left end) and swings the buckle open; the left arm takes the old hotend
by its heatsink from the side, pulls it straight down out of the pocket and stands it in the holder's empty (left)
slot; the right arm takes the new hotend from the holder's right slot, brings it under the toolhead, pushes it
straight up until it seats and lets go (the sprung retainer holds it, as the A1's magnet does), then swings the
buckle shut under its lug. Both hands pinch a heatsink 4 cm below its top: the YAM's finger plates are about 4 cm
tall there, so a higher pinch would run them into the toolhead's underside.

Variants: no_lock (the buckle is left open), half_in (the new hotend is pushed in 2.5 mm short of its seat and let go,
then the buckle is swung shut), drop_old (the old hotend is let go over the bed instead of in the holder),
drop_new (the new hotend is let go over the bed on its way to the toolhead).
"""

from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import democore as dc  # noqa: E402

VARIANTS = ("full", "no_lock", "half_in", "drop_old", "drop_new")
GRASP = np.array([0.0, -0.004, -0.040])  # TCP relative to a hotend's origin (side pinch on the heatsink)
TAB_BACK = 0.010  # m: the right TCP sits this far behind the tab's centre (fingertips 3 mm short of the toolhead)
OPEN_DEG = 90.0
OPEN_H = 0.33  # grip command for the hotend grasps: fingers about 3.1 cm apart, clear of the printer's base

SIDE_TILT = 5.0  # deg: each hand's side approach leans this far down from horizontal


def _R_side(sgn=1.0):
    """A side pinch on a heatsink: approach along +y (right hand, sgn 1) or -y (left hand, sgn -1), leaning
    SIDE_TILT degrees down, fingers closing along x."""
    a = math.radians(SIDE_TILT)
    z, x = np.array([0.0, sgn * math.cos(a), -math.sin(a)]), np.array([sgn, 0.0, 0.0])
    return np.column_stack([x, np.cross(z, x), z])


def _R_tab(phi_deg):
    """Right hand on the tab: approach toward the toolhead (turned with the buckle), fingers closing vertically on the
    tab's top and bottom."""
    ph = math.radians(phi_deg)
    z = np.array([math.cos(ph), math.sin(ph), 0.0])
    x = np.array([0.0, 0.0, 1.0])
    return np.column_stack([x, np.cross(z, x), z])


def build_plan(t, variant="full", params=None):
    from yam_arena import ik, station
    from yam_arena.constants import READY

    bases = station.BASES
    starts = {s: ik.tcp_pose(np.array(READY), bases[s]) for s in ("left", "right")}
    arms = {s: dc.Arm(s, bases[s], READY, *starts[s]) for s in ("left", "right")}
    L, Rt = arms["left"], arms["right"]
    TH, SEAT = np.asarray(t.TH), np.asarray(t.SEAT)
    hinge = TH + np.asarray(t.HINGE)
    tab_c = np.asarray(t.TAB["center"])
    Rr, Rl = _R_side(1.0), _R_side(-1.0)
    G_r, G_l = GRASP, GRASP * np.array([1.0, -1.0, 1.0])  # the left hand's pinch mirrors the right's

    def tab_tcp(phi_deg, back=TAB_BACK):
        Rz = dc.rot((0, 0, 1), math.radians(phi_deg))
        c = hinge + Rz @ tab_c
        R = _R_tab(phi_deg)
        return c - back * R[:, 2], R

    def swing(dur, a0, a1, grip, label):
        Rt.add(dur, grip=grip, label=label, path=lambda u: tab_tcp(a0 + (a1 - a0) * u))

    seat = TH + SEAT
    slot = {k: np.asarray(t.STAND_POS) + np.array([0.0, y, t.STAND_H + t.SINK[2]]) for k, y in t.SLOT_Y.items()}
    off_r, off_l = np.array([0.0, -0.050, 0.0]), np.array([0.0, 0.050, 0.0])

    # -- right arm: open the buckle (its tab is at the left end; the left end swings out to the front) ---------------
    p, R = tab_tcp(0.0, TAB_BACK + 0.030)
    Rt.add(3.0, p + [0, 0, 0.03], R, 1.0, "right: above the tab")
    Rt.add(1.2, p, R, 1.0, "right: before the tab")
    Rt.add(1.2, *tab_tcp(0.0), 1.0, "right: around the tab")
    Rt.add(0.8, *tab_tcp(0.0), 0.0, "right: grip tab")
    swing(3.0, 0.0, OPEN_DEG + 3.0, 0.0, "right: swing open")  # against the buckle's 90-degree stop
    Rt.add(0.6, grip=1.0, label="right: let go of the tab")
    p, R = tab_tcp(OPEN_DEG, TAB_BACK + 0.035)
    Rt.add(1.0, p, R, 1.0, "right: back off")
    Rt.add(1.5, p + [-0.04, -0.04, 0.04], R, 1.0, "right: clear")
    t_open = Rt.duration

    # -- left arm: the old hotend out and into the holder's empty (left) slot --------------------------------------
    L.add(max(t_open - 3.5, 0.5), label="left: wait")
    L.add(2.5, seat + G_l + off_l, Rl, OPEN_H, "left: beside the old hotend")
    L.add(1.5, seat + G_l, Rl, OPEN_H, "left: around the old hotend")
    L.add(1.0, seat + G_l, Rl, 0.0, "left: grip old")
    L.add(2.0, seat + G_l + [0, 0, -0.045], Rl, 0.0, "left: pull down")
    L.add(1.5, seat + G_l + [-0.10, 0, -0.045], Rl, 0.0, "left: out from under")
    if variant == "drop_old":
        L.add(0.8, grip=OPEN_H, label="left: let go over the bed")
        L.add(1.0, seat + G_l + [-0.10, 0.06, -0.045], Rl, OPEN_H, "left: away")
    else:
        L.add(2.0, slot["empty"] + G_l + [0, 0, 0.025], Rl, 0.0, "left: above the empty slot")
        L.add(1.5, slot["empty"] + G_l + [0, 0, 0.001], Rl, 0.0, "left: into the slot")
        L.add(0.8, grip=OPEN_H, label="left: let go old")
        L.add(1.0, slot["empty"] + G_l + off_l, Rl, OPEN_H, "left: out of the old one")
    L.add(2.0, *starts["left"], 1.0, "left: back")
    t_old_out = L.duration - 2.0 - 1.0  # the old hotend is stood in its slot and let go

    # -- right arm: the new hotend from the holder's right slot into the pocket ------------------------------------
    new_g = slot["new"] + G_r
    Rt.add(2.5, new_g + 1.4 * off_r + [0, 0, 0.10], Rr, OPEN_H, "right: above beside the new hotend")
    Rt.add(1.5, new_g + 1.4 * off_r, Rr, OPEN_H, "right: beside the new hotend")
    Rt.add(1.0, new_g + off_r, Rr, OPEN_H, "right: closer")
    Rt.add(1.2, new_g, Rr, OPEN_H, "right: around the new hotend")
    Rt.add(1.0, new_g, Rr, 0.0, "right: grip new")
    Rt.add(1.5, new_g + [0, 0, 0.040], Rr, 0.0, "right: lift new")
    below = TH + np.array([-0.00075, 0.0, t.POCKET[2]]) + G_r + [0.0, 0.0, -0.030]  # under the pocket, 0.75 mm forward
    Rt.add(max(t_old_out + 0.5 - Rt.duration, 0.5), new_g + [0, 0, 0.040], Rr, 0.0, "right: wait with it")
    Rt.add(2.5, below + [-0.10, 0, 0.0], Rr, 0.0, "right: toward the toolhead")
    if variant == "drop_new":
        Rt.add(0.8, grip=OPEN_H, label="right: let go over the bed")
        Rt.add(1.5, below + [-0.10, -0.06, 0.0], Rr, OPEN_H, "right: away")
        Rt.add(2.5, *starts["right"], 1.0, "right: back")
        end = max(L.duration, Rt.duration) + 3.0
        L.add(max(end - L.duration, 0.5), label="left: wait")
        Rt.add(max(end - Rt.duration, 0.5), label="right: wait")
        return L, Rt, {}
    Rt.add(1.5, below, Rr, 0.0, "right: under the pocket")
    if variant == "half_in":  # stops 2.5 mm short of the seat
        Rt.add(3.0, below + [0, 0, 0.0275], Rr, 0.0, "right: rise")
        top = below + [0, 0, 0.0275]
    else:  # rise to the seat (the joint integral still takes out the arm's sag), then push 6 mm past it
        Rt.add(3.0, below + [0, 0, 0.030], Rr, 0.0, "right: rise")
        Rt.add(1.0, below + [0, 0, 0.036], Rr, 0.0, "right: push home")
        top = below + [0, 0, 0.030]
    Rt.add(0.6, label="right: hold")
    Rt.add(0.8, grip=OPEN_H, label="right: let go new")
    Rt.add(1.2, top + off_r, Rr, OPEN_H, "right: out")

    # -- right arm: close the buckle ---------------------------------------------------------------------------------
    if variant != "no_lock":
        p, R = tab_tcp(OPEN_DEG, TAB_BACK + 0.035)
        Rt.add(2.0, p + [-0.03, -0.03, 0.03], R, 1.0, "right: to the tab again")
        Rt.add(1.2, p, R, 1.0, "right: before the tab again")
        Rt.add(1.2, *tab_tcp(OPEN_DEG), 1.0, "right: around the tab again")
        Rt.add(0.8, *tab_tcp(OPEN_DEG), 0.0, "right: grip tab again")
        swing(2.5, OPEN_DEG, -2.0, 0.0, "right: swing shut")
        Rt.add(0.5, *tab_tcp(-2.0), 0.0, "right: press shut")
        Rt.add(0.6, grip=1.0, label="right: let go of the tab")
        p, R = tab_tcp(0.0, TAB_BACK + 0.035)
        Rt.add(1.0, p, R, 1.0, "right: back off")
    Rt.add(2.5, *starts["right"], 1.0, "right: back")
    end = max(L.duration, Rt.duration) + 3.0
    L.add(max(end - L.duration, 0.5), label="left: wait")
    Rt.add(max(end - Rt.duration, 0.5), label="right: wait")
    return L, Rt, {}


def frozen(label: str) -> bool:
    return label.endswith(("grip tab", "grip old", "grip new", "grip tab again", "swing open", "swing shut",
                           "press shut", "pull down", "push home", "hold", "into the slot"))


def debug(k, t, kk, labL, labR):
    r = t.report()
    pads = []
    for arm in kk.ARMS:
        pts = kk.STATE.fingers.get(arm)
        if pts is None:
            continue
        n = len(pts) // 2
        a, b = pts[:n].mean(axis=0), pts[n:].mean(axis=0)
        c = 1000 * ((a + b) / 2 - np.asarray(t.TH))
        pads.append(f"{arm[0].upper()} gap {1000 * np.linalg.norm(a - b) - 8:.1f} c[{c[0]:.0f},{c[1]:.0f},{c[2]:.0f}] "
                    f"top {1000 * (pts[:, 2].max() - t.TH[2]):.0f}")
    print(f"  dbg {k}: buckle {r.get('buckle_deg')} new {r.get('new_local_mm')} seat {r.get('new_seated')} "
          f"old {r.get('old_local_mm')} slot {r.get('old_slot')} drop {r.get('old_dropped')}/{r.get('new_dropped')} "
          f"off {r.get('hands_off')} hold {r.get('hold_steps')} tilt {r.get('new_tilt')} "
          f"| {' | '.join(pads)} | {labL} | {labR}", flush=True)


def _quat_R(q):
    x, y, z, w = (float(v) for v in q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


class PointServo(dc.ObjectServo):
    """ObjectServo on a point of the held part (given in the part's frame) instead of its origin: here the old
    hotend's nozzle tip, so a hotend leaning in the grip still goes down the holder's hole."""

    def __init__(self, arm, obj, offset, point, **kw):
        super().__init__(arm, obj, offset, **kw)
        self.point = np.asarray(point, float)

    def update(self, kk, label: str) -> None:
        key = label.split(": ")[-1]
        if self.desired is None or self.obj not in kk.STATE.poses or key in self.hold:
            return
        if key in self.xyz or key in self.xy:
            p, q = kk.STATE.poses[self.obj]
            e = self.desired - (np.asarray(p, float) + _quat_R(q) @ self.point)
            if key in self.xy:
                e[2] = 0.0
            self.off = np.clip(self.off + self.gain * e, -self.clip, self.clip)
        else:
            self.off = np.zeros(3)


def servos_for(name, arm):
    """Steer each held hotend (not the gripper) along the plan: the left hand's old hotend into its slot, the right
    hand's new hotend under and up into the pocket."""
    if name == "left":
        R, G = _R_side(-1.0), GRASP * np.array([1.0, -1.0, 1.0])
        tip = np.array([0.0, 0.0, -(0.046 + 0.010 + 0.004)])  # the nozzle's end, hotend frame (upright as planned)
        return [PointServo(arm, "hotend_old", R.T @ (-G + tip), tip, xyz=("out from under", "above the empty slot"),
                           xy=("into the slot",), hold=("let go old",))]
    R, G = _R_side(1.0), GRASP
    return [dc.ObjectServo(arm, "hotend_new", R.T @ (-G), xyz=("wait with it", "toward the toolhead", "under the pocket", "rise"),
                           xy=("push home",), hold=("hold", "let go new"))]


if __name__ == "__main__":
    dc.main(build_plan, VARIANTS, servos_for, frozen, debug)
