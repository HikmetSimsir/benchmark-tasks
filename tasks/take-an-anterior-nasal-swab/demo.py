"""Scripted demo: an anterior nasal swab of the training head, and the failure / cheating variants.

The right arm takes the swab out of its tube by the cap, samples the patient's left nostril (the robot's right) and
then the right one, each with the whole foam tip inside and the tip circled round the nostril's wall on a path
planned 4 mm into it (the compliant arm presses the foam on the wall), and puts the swab back and pushes the cap home. The
left arm holds the tube while the swab is pulled out and while the cap is pushed home.

Variants (see the README for their scores):
  full         the whole procedure
  one_spot     the tip pressed on one part of each nostril's wall and rubbed back and forth there (no circles)
  light        the circles run with the tip just clear of the wall (no press)
  one_nostril  only the patient's left nostril is sampled
  lip          the tip brushes the upper lip on its way to the first nostril (a contaminated swab)
  one_arm      the left arm never holds the tube: the cap cannot be pushed home
"""

from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import democore as dc  # noqa: E402

VARIANTS = ("full", "one_spot", "light", "one_nostril", "lip", "one_arm")
HERE = pathlib.Path(__file__).resolve().parent
GRASP_CACHE = HERE / "grasp.json"  # the grasp rotation found by the IK search (written on first use)
_CACHE: dict = {}

S_INS = 0.0125  # m: tip centre this deep in the nostril while circling (the 16 mm tip spans 4.5-20.5 mm)
DELTA = 0.004  # m: the planned circle runs this far into the wall; the compliant arm presses the foam on it
T_CIRC = 2.6  # s per circle
N_CIRC = 6.0  # circles commanded per nostril, 15.6 s (4 pressed circles required; 10-20% of the steps are not pressed)
D_C = 0.0  # TCP on the cap's axis
G_OFF = -0.005  # m: the fingers pinch the cap's grip this far behind its middle (clear of the tube's rim)
PULL = 0.155  # m: the swab comes out of the tube along -y
PUSH = 0.025  # m: the cap is commanded this far past its seat when pushed home (about 2-3 N with the tube held)
HOLD_TILT, HOLD_ROLL = -15.0, 180.0  # deg: the left hand's pinch on the tube, tilted about the tube's axis (IK search)


def wall_r(t, phi):
    """Radius of the elliptical nostril at angle phi (from its long axis)."""
    return t.A_SEMI * t.B_SEMI / math.sqrt((t.B_SEMI * math.cos(phi)) ** 2 + (t.A_SEMI * math.sin(phi)) ** 2)


def grasp_cands():
    """Grasp rotations of the TCP in the swab's frame: the fingers close across the cap's grip."""
    out = []
    for beta in range(-60, 61, 15):
        b = math.radians(beta)
        x = np.array([0.0, math.cos(b), math.sin(b)])
        z = np.array([0.0, math.sin(b), -math.cos(b)])
        for sgn in (1, -1):
            xs = sgn * x
            out.append(np.column_stack([xs, np.cross(z, xs), z]))
    return out


def find_grasp(t, tcp_fn, tube):
    """Search the grasp rotation (``grasp_cands``) and the swab's roll in the nostrils for the smallest worst IK error
    over the key poses at the tube and in both nostrils; writes ``grasp.json``."""
    from yam_arena import ik, station
    from yam_arena.constants import READY

    a, u, v = t.AX, t.UX, t.VX
    S_a = dc.rot((0, 1, 0), t.ALPHA)
    seeds = [np.array(READY, float), *dc.SEEDS[:6]]

    def err(p, R):
        e = np.inf
        for sd in seeds:
            q, pe, re = ik.solve(p, ik.matrix_to_quat_xyzw(R), sd, base_pos=station.BASES["right"], iters=150)
            e = min(e, pe + 0.05 * re)
            if e < 0.0005:
                break
        return e

    def nostril_poses(psi):
        S = dc.rot(a, math.radians(psi)) @ S_a
        out = []
        for k in ("left", "right"):
            O = t.NOSTRILS[k]
            out += [(O - 0.03 * a - t.TIP_X * a, S), (O + S_INS * a - t.TIP_X * a, S)]
            for ph in np.radians(np.arange(0, 360, 45)):
                rho = wall_r(t, ph) - t.TIP_R + DELTA
                out.append((O + S_INS * a + rho * (math.cos(ph) * u + math.sin(ph) * v) - t.TIP_X * a, S))
        return out

    best = (np.inf, None, None)
    for Rg in grasp_cands():
        w = 0.0
        for C, S in tube:
            w = max(w, err(*tcp_fn(C, S, Rg)))
            if w > max(0.002, best[0]):
                break
        if w > max(0.002, best[0]):
            continue
        for psi in range(-90, 91, 15):
            ww = w
            for C, S in nostril_poses(psi):
                ww = max(ww, err(*tcp_fn(C, S, Rg)))
                if ww >= best[0]:
                    break
            if ww < best[0]:
                best = (ww, Rg, psi)
    GRASP_CACHE.write_text(json.dumps({"Rg": best[1].tolist(), "psi_deg": best[2], "worst_ik": best[0]}))
    print(f"grasp: worst IK error {best[0]:.4f} (m + 0.05 rad), roll in the nostrils {best[2]} deg", flush=True)


def build_plan(t, variant="full", params=None):
    from yam_arena import ik, station
    from yam_arena.constants import READY

    bases = station.BASES
    starts = {s: ik.tcp_pose(np.array(READY), bases[s]) for s in ("left", "right")}
    arms = {s: dc.Arm(s, bases[s], READY, *starts[s]) for s in ("left", "right")}
    L, Rt = arms["left"], arms["right"]
    a, u, v = t.AX, t.UX, t.VX
    S_a = dc.rot((0, 1, 0), t.ALPHA)  # swab along the nostril axis
    S_t = dc.rot((0, 0, 1), math.pi / 2)  # swab along the tube (+y)
    C0 = np.array(t.SWAB_POS)  # cap centre at the start (seated in the tube)
    ey = np.array([0.0, 1.0, 0.0])
    C_seat = C0.copy()
    C_out = C0 - PULL * ey
    C_align = C0 - (t.TIP_END - t.GRIP_L / 2 + 0.020) * ey  # tip's end 2 cm outside the mouth

    def tcp(C, S, Rg):
        return C + S @ (np.array([G_OFF, 0.0, 0.0]) + Rg @ np.array([0.0, 0.0, D_C])), S @ Rg

    def swab_at_tip(T, S=None):
        S = S_n if S is None else S
        return T - t.TIP_X * (S @ np.array([1.0, 0.0, 0.0])), S

    delta = -0.001 if variant == "light" else DELTA

    def circle_pose(O, phi, rho_scale=1.0):
        rho = (wall_r(t, phi) - t.TIP_R + delta) * rho_scale
        return swab_at_tip(O + S_INS * a + rho * (math.cos(phi) * u + math.sin(phi) * v))

    order = ["left"] if variant == "one_nostril" else ["left", "right"]

    # -- the grasp: the TCP's rotation in the swab's frame, and the swab's roll about its own axis in the nostrils
    #    (the swab is round, so any roll samples alike); chosen for the smallest worst IK error (cached) ---------------
    if "Rg" not in _CACHE:
        if not GRASP_CACHE.exists():
            find_grasp(t, tcp_fn=tcp,
                       tube=[(C0, S_t), (C0 + [0, 0, 0.06], S_t), (C_out, S_t), (C_out + [0, 0, 0.05], S_t),
                             (C_align, S_t), (C_seat + PUSH * ey, S_t)])
        g = json.loads(GRASP_CACHE.read_text())
        _CACHE["Rg"], _CACHE["psi"] = np.array(g["Rg"]), float(g["psi_deg"])
    Rg = _CACHE["Rg"]
    S_n = dc.rot(a, math.radians(_CACHE["psi"])) @ S_a  # the swab in the nostrils
    _CACHE["Rg_used"] = Rg
    _CACHE["tip_x"], _CACHE["plug_x"] = t.TIP_X, t.GRIP_L / 2 + t.PLUG_W / 2
    _CACHE["right_arm"] = Rt

    def to(dur, C, S, grip, label):
        p, R = tcp(C, S, Rg)
        Rt.add(dur, p, R, grip, label)

    def along(dur, f, grip, label):
        Rt.add(dur, grip=grip, label=label, path=lambda uu: tcp(*f(uu), Rg))

    # -- right arm: the swab -------------------------------------------------------------------------------------------
    to(3.0, C0 + [0, 0, 0.06], S_t, 1.0, "swab: above the cap")
    to(1.5, C0, S_t, 1.0, "swab: around the cap")
    to(1.0, C0, S_t, 0.0, "swab: grip")
    t_pull = Rt.duration
    along(2.5, lambda uu: (C0 - uu * PULL * ey, S_t), 0.0, "swab: pull")
    t_pulled = Rt.duration
    to(1.0, C_out + [0, 0, 0.05], S_t, 0.0, "swab: lift")
    for i, k in enumerate(order):
        O = t.NOSTRILS[k]
        if variant == "lip" and i == 0:  # the tip's end dips onto the upper lip, below the nostrils
            hp = t.HEAD_POS
            xl, yl = -0.068, (O - hp)[1]
            end = hp + np.array([xl, yl, t._face_z(xl, yl) + t.TIP_R - 0.003])  # the tip's end 3 mm into the skin
            T_lip = end - (t.TIP_END - t.TIP_X - t.TIP_R) * a
            C, S = swab_at_tip(T_lip + [0, 0, 0.03])
            to(3.0, C, S, 0.0, "lip: above the lip")
            Rt.add(1.0, label="lip: settle")  # the tip servo settles 3 cm above the lip
            C, S = swab_at_tip(T_lip)
            to(1.2, C, S, 0.0, "lip: touch")
            C, S = swab_at_tip(T_lip + [0, 0, 0.03])
            to(1.0, C, S, 0.0, "lip: lift")
        C, S = swab_at_tip(O - 0.03 * a)
        to(3.0 if i == 0 else 2.0, C, S, 0.0, f"{k}: approach")
        C, S = swab_at_tip(O - 0.01 * a)
        to(1.5, C, S, 0.0, f"{k}: hover")  # the tip 1 cm outside the nostril, on its axis (the servo settles)
        along(1.5, lambda uu, O=O: swab_at_tip(O + (-0.01 + uu * (0.01 + S_INS)) * a), 0.0, f"{k}: insert")
        tot = N_CIRC * 2 * math.pi
        if variant == "one_spot":  # pressed on one part of the wall and rubbed back and forth over +-30 degrees
            along(0.6, lambda uu, O=O: circle_pose(O, 0.0, uu), 0.0, f"{k}: ramp out")
            along(T_CIRC * N_CIRC, lambda uu, O=O: circle_pose(O, math.radians(30.0) * math.sin(uu * N_CIRC * 2 * math.pi)),
                  0.0, f"{k}: circle")
            along(0.5, lambda uu, O=O: circle_pose(O, 0.0, 1.0 - uu), 0.0, f"{k}: ramp in")
        else:
            along(0.6, lambda uu, O=O: circle_pose(O, 0.0, uu), 0.0, f"{k}: ramp out")
            along(T_CIRC * N_CIRC, lambda uu, O=O: circle_pose(O, uu * tot), 0.0, f"{k}: circle")
            along(0.5, lambda uu, O=O: circle_pose(O, tot, 1.0 - uu), 0.0, f"{k}: ramp in")
        along(1.0, lambda uu, O=O: swab_at_tip(O + (S_INS - uu * (S_INS + 0.03)) * a), 0.0, f"{k}: withdraw")
    O = t.NOSTRILS[order[-1]]
    C, S = swab_at_tip(O - 0.06 * a)
    to(1.0, C + [0, 0, 0.02], S, 0.0, "tube: away")
    to(3.0, C_align + [0, 0, 0.05], S_t, 0.0, "tube: turn")
    to(2.0, C_align, S_t, 0.0, "tube: align")
    t_enter = Rt.duration
    along(3.0, lambda uu: (C_align + uu * (C_seat - 0.003 * ey - C_align), S_t), 0.0, "tube: enter")
    to(1.0, C_seat + PUSH * ey, S_t, 0.0, "tube: push")
    Rt.add(1.0, label="tube: press")
    Rt.add(0.6, grip=1.0, label="tube: release")
    t_released = Rt.duration
    to(0.6, C_seat + PUSH * ey + [0, 0, 0.06], S_t, 1.0, "tube: retreat")
    to(1.0, C_seat + np.array([0.0, -0.04, 0.15]), S_t, 1.0, "tube: clear")  # well away from the capped tube
    Rt.add(8.0, label="tube: wait")  # the cap must stay home 9 s (HOME_STEPS) before success

    # -- left arm: holds the tube while the swab is pulled out and while the cap is pushed home --------------------
    if variant != "one_arm":
        H = t.KIT_POS + np.array([0.0, t.HOLD_Y, t.TUBE_Z - t.TOP])
        R_h = dc.rot((0, 1, 0), math.radians(HOLD_TILT)) @ dc.R_approach(0.0, 0.0, HOLD_ROLL)  # fingers across the tube
        L.add(max(t_pull - 4.0, 0.5), label="left: wait")
        L.add(2.0, H + [0, 0, 0.06], R_h, 1.0, "left: above the tube")
        L.add(1.2, H, R_h, 1.0, "left: around the tube")
        L.add(0.8, H, R_h, 0.0, "left: grip")
        L.add(max(t_pulled - L.duration, 0.0) + 0.5, label="left: hold")
        L.add(0.6, grip=1.0, label="left: let go")
        L.add(1.5, H + [0, 0, 0.08], R_h, 1.0, "left: up")
        L.add(2.5, *starts["left"], 1.0, "left: back")
        L.add(max(t_enter - 4.5 - L.duration, 0.5), label="left: wait")
        L.add(2.5, H + [0, 0, 0.06], R_h, 1.0, "left: above the tube")
        L.add(1.2, H, R_h, 1.0, "left: around the tube")
        L.add(0.8, H, R_h, 0.0, "left: grip")
        L.add(max(t_released + 0.3 - L.duration, 0.5), label="left: hold")  # until the right hand has let go
        L.add(0.6, grip=1.0, label="left: let go")
        L.add(0.8, H + [0, 0, 0.08], R_h, 1.0, "left: up")
        L.add(1.6, *starts["left"], 1.0, "left: back")
        L.add(max(Rt.duration - L.duration, 0.5), label="left: wait")
    else:
        L.add(Rt.duration, label="left: wait")
    return L, Rt, {}


class SwabServo(dc.ObjectServo):
    """Servo a point of the held swab onto the plan (the tip in the nostrils, the plug at the tube): on the ``xyz``
    labels the error between the planned and the actual point is integrated into a TCP offset; on ``hold`` labels the
    offset is kept. On the ``orient`` labels the swab's axis is also turned onto the planned axis (the swab can turn a
    little in the fingers while it rubs the nostrils): the error is integrated into a rotation of the TCP, kept on
    ``hold`` labels."""

    def __init__(self, arm, points: dict, default_x: float, orient=(), o_gain=0.12, o_clip_deg=25.0, **kw):
        super().__init__(arm, "swab", np.zeros(3), **kw)
        self.points, self.default_x = points, default_x
        self.orient, self.o_gain, self.o_clip = set(orient), o_gain, math.radians(o_clip_deg)
        self.Roff = np.eye(3)
        self.R_plan = None

    def _x(self, key):
        return self.points.get(key, self.default_x)

    def correct(self, pos, R, label):
        key = label.split(": ")[-1]
        Rg = _CACHE["Rg_used"]
        self.offset = Rg.T @ np.array([self._x(key) - G_OFF, 0.0, 0.0]) - np.array([0.0, 0.0, D_C])
        self.R_plan = np.asarray(R, float)
        pos, R = super().correct(pos, R, label)
        if key in self.orient or (key in self.hold and key not in self.xyz):
            return pos, self.Roff @ np.asarray(R, float)
        return pos, R

    def update(self, kk, label: str) -> None:
        key = label.split(": ")[-1]
        if self.desired is None or self.obj not in kk.STATE.poses or key in self.hold:
            return
        p, q = kk.STATE.poses[self.obj]
        Rs = kk.rot_matrix(q)
        if key in self.xyz:
            pt = np.asarray(p, float) + Rs @ np.array([self._x(key), 0.0, 0.0])
            self.off = np.clip(self.off + self.gain * (self.desired - pt), -self.clip, self.clip)
        else:
            self.off = np.zeros(3)
        if key in self.orient and self.R_plan is not None:
            ax = Rs[:, 0]
            ax_des = self.R_plan @ _CACHE["Rg_used"].T @ np.array([1.0, 0.0, 0.0])
            w = np.cross(ax, ax_des)
            ang = math.atan2(float(np.linalg.norm(w)), float(ax @ ax_des))
            if ang > 1e-4:
                self.Roff = dc.rot(w, self.o_gain * ang) @ self.Roff
            tot = math.acos(max(-1.0, min(1.0, (np.trace(self.Roff) - 1.0) / 2.0)))
            if tot > self.o_clip:  # cap the correction
                wv = np.array([self.Roff[2, 1] - self.Roff[1, 2], self.Roff[0, 2] - self.Roff[2, 0],
                               self.Roff[1, 0] - self.Roff[0, 1]])
                self.Roff = dc.rot(wv, self.o_clip)
        elif key not in self.orient:
            self.Roff = np.eye(3)


def servos_for(name, arm):
    if name != "right":
        return []
    plug_x = _CACHE["plug_x"]  # set by build_plan, which runs first
    return [SwabServo(arm, {"align": plug_x, "enter": plug_x, "pull": plug_x}, _CACHE["tip_x"],
                      xyz=("approach", "hover", "insert", "above the lip", "settle", "align", "enter", "pull"),
                      hold=("ramp out", "circle", "ramp in", "withdraw", "touch", "lift", "push", "press", "release"),
                      orient=("align", "enter"), gain=0.15, clip=0.03)]


def frozen(label: str) -> bool:
    return label.endswith(("grip", "ramp out", "circle", "ramp in", "push", "press", "release"))


def debug(k, t, kk, labL, labR):
    r = t.report()
    n = r.get("nostrils", {})
    extra = ""
    if "kit" in kk.STATE.poses and "swab" in kk.STATE.poses:
        kp = np.asarray(kk.STATE.poses["kit"][0])
        sp = np.asarray(kk.STATE.poses["swab"][0])
        H = kp + np.array([0.0, t.HOLD_Y, t.TUBE_Z - t.TOP])
        fl = kk.STATE.fingers.get("left_robot")
        if fl is not None:
            f1, f2 = fl[:12].mean(0) - H, fl[12:].mean(0) - H
            extra = f" padsL {np.round(1000 * f1, 1)} {np.round(1000 * f2, 1)}"
        extra += f" swab {np.round(1000 * (sp - np.array(t.SWAB_POS)), 1)}"
    arm = _CACHE.get("right_arm")
    if arm is not None and "swab" in kk.STATE.poses:  # the held swab against the plan: axis angle, tip error (mm)
        p_cmd, R_cmd, _, _ = arm.target(k / dc.CONTROL_HZ)
        Rg = _CACHE["Rg_used"]
        ax_plan = R_cmd @ Rg.T @ np.array([1.0, 0.0, 0.0])
        C_plan = p_cmd - R_cmd @ Rg.T @ (np.array([G_OFF, 0.0, 0.0]) + Rg @ np.array([0.0, 0.0, D_C]))
        sp, sq = kk.STATE.poses["swab"]
        ax = kk.rot_matrix(sq)[:, 0]
        ang = math.degrees(math.acos(max(-1.0, min(1.0, float(ax @ ax_plan)))))
        tip_err = (np.asarray(sp) + t.TIP_X * ax) - (C_plan + t.TIP_X * ax_plan)
        extra += f" axis {ang:.1f}deg tip_err {np.round(1000 * tip_err, 1)}"
    print(f"  dbg {k}: L {n.get('left')} R {n.get('right')} wall {r.get('wall_force')} stray {r.get('tip_touched')} "
          f"gap {r.get('cap_gap_mm')} push {r.get('push_n')} latched {r.get('cap_latched')} held {r.get('swab_held')} "
          f"kit {r.get('kit_shift_mm')}{extra} | {labL} | {labR}", flush=True)


if __name__ == "__main__":
    dc.main(build_plan, VARIANTS, servos_for, frozen, debug)
