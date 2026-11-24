"""On the station table: a nasal-swab practice head (printed shell; simplified face, adult-size nose and nostrils) lying
face up (crown away from the robot), fixed to the table; in front of its chin, a dry transport tube on a small stand,
its mouth toward the robot's right, holding a sterile foam swab on the tube's plug-style blue cap (in place as
shipped), modelled on the Puritan 25-1506 1PF BT BL (15.19 cm overall; foam tip 0.48 cm across and 1.6 cm long). The
tube and its stand are one free 100 g piece.

The CDC's anterior nasal (nares) swab: take the swab out by its cap; put the entire foam tip in one nostril (1 to
1.5 cm) and firmly sample the wall by rotating the swab in a circular path against it at least 4 times (about 15 s);
repeat in the other nostril with the same swab; put the swab back in its tube and push the cap home, holding the
tube. The tip may touch only the insides of the nostrils and of the tube; no finger may touch the foam.

Scored each step from poses, finger-pad points and PhysX contact points with per-point normal forces; see score().
"""

from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from yam_arena.task_file import TABLE_TOP  # noqa: E402

import kitchenkit as kk  # noqa: E402

SCENE = "station"
SCORE_OVER = "end"
TOP = TABLE_TOP[SCENE]

INSTRUCTION = ("Take an anterior nasal swab from both nostrils of the training head with the swab in the tube: put the "
               "whole foam tip in each nostril and rub it round the inside wall at least 4 times, then put the swab "
               "back in its tube and push the cap home.")

SKIN = (0.90, 0.74, 0.62)
LIP_C, EYE_C, BROW_C = (0.74, 0.42, 0.40), (0.22, 0.15, 0.12), (0.38, 0.27, 0.19)
SHADOW_C = (0.82, 0.65, 0.55)  # eye sockets
CAP_C, SHAFT_C, TIP_C = (0.15, 0.35, 0.80), (0.96, 0.96, 0.96), (0.98, 0.98, 0.92)
TUBE_C, TRAY_C = (0.88, 0.92, 0.95), (0.55, 0.60, 0.68)

# -- the training head (one printed shell; mesh in assets/training_head.obj, head frame: origin on the bench under the
#    head's centre, +x toward the crown, +z up) ------------------------------------------------------------------------
HEAD_POS = np.array([0.370, -0.050, TOP])
HEAD_MESH = str(pathlib.Path(__file__).resolve().parent / "assets" / "training_head.obj")
ALPHA = math.radians(30.0)  # nostril axis, below the horizontal (into the nose: toward the crown and down)
AX = np.array([math.cos(ALPHA), 0.0, -math.sin(ALPHA)])  # nostril axis, into the nose
UX = np.array([math.sin(ALPHA), 0.0, math.cos(ALPHA)])  # nostril's long axis (toward the nose tip)
VX = np.array([0.0, 1.0, 0.0])  # nostril's short axis (across the face)
A_SEMI, B_SEMI, NOSTRIL_DEPTH = 0.0070, 0.0050, 0.026  # elliptical nostril, 14 x 10 mm, 26 mm deep to its end
_O_HEAD = {"left": (-0.040, -0.007, 0.156), "right": (-0.040, 0.007, 0.156)}  # patient's left is the robot's right
NOSTRILS = {k: HEAD_POS + np.array(v) for k, v in _O_HEAD.items()}  # opening centres (world)


def _face_z(x, y):
    """Height of the head shell's ellipsoid surface (head frame) at (x, y), for placing the painted features."""
    r = 1.0 - (x / 0.110) ** 2 - (y / 0.075) ** 2
    return 0.085 + 0.085 * math.sqrt(max(r, 0.0)) - 0.024


_ASSETS = pathlib.Path(__file__).resolve().parent / "assets"
# Visual-only face details (no collision, not part of the printable shell): eye sockets, closed eyelids, brows, lips
# and mouth line follow the face surface 0.5-0.9 mm above it; ears, cheeks and chin are shallow skin-coloured shapes
# well away from the nose and the swab's path.
_FEAT = [kk.Geom("mesh", (0.0, 0.0, 0.0), (0.0,), mesh=str(_ASSETS / f"face_{name}.obj"), color=col, collide=False)
         for name, col in (("skin", SKIN), ("shadow", SHADOW_C), ("dark", EYE_C), ("brow", BROW_C), ("lips", LIP_C))]
HEAD = kk.part("head", tuple(HEAD_POS), [kk.Geom("mesh", (0.0, 0.0, 0.0), (0.0,), mesh=HEAD_MESH, color=SKIN),
                                         *_FEAT],
               mass=1.5, color=SKIN, friction=(0.45, 0.40), contact=(0.001, 0.0), rigid={"kinematic_enabled": True})

# -- the swab (frame: centre of the cap's grip; +x along the shaft toward the tip) -----------------------------------
GRIP_L, GRIP_W = 0.025, 0.013  # the cap's grip (octagonal, 1.3 cm across, 2.5 cm long)
PLUG_L, PLUG_W = 0.0100, 0.0100  # the cap's plug (round, 10 mm) in the tube's 11.2 mm mouth (no friction fit)
SHAFT_W = 0.0026
OVERALL = 0.15187  # Puritan 25-1506 1PF BT, overall length
TIP_R, TIP_LEN = 0.0047750 / 2, 0.0160  # foam tip: 4.775 mm across, 16.0 mm long
TIP_END = OVERALL - GRIP_L / 2  # the tip's end, swab frame x
TIP_X = TIP_END - TIP_LEN / 2  # the tip's centre
TIP_XS = tuple(float(x) for x in np.linspace(TIP_END - TIP_LEN + TIP_R, TIP_END - TIP_R, 5))
SHAFT_X0 = GRIP_L / 2 + PLUG_L
SWAB_MASS = 0.005


def _octagon(x0, length, width, color, contact=None):
    return [kk.Geom("box", (x0 + length / 2, 0.0, 0.0), (length, width, width), color=color, contact=contact),
            kk.Geom("box", (x0 + length / 2, 0.0, 0.0), (length, width, width), kk.quat_axis((1, 0, 0), math.pi / 4),
                    color=color, contact=contact)]


SWAB_GEOMS = [
    *_octagon(-GRIP_L / 2, GRIP_L, GRIP_W, CAP_C, (0.003, 0.0)),
    *[kk.Geom("sph", (GRIP_L / 2 + PLUG_W / 2 + dx, 0.0, 0.0), (PLUG_W / 2,), color=CAP_C, friction=(0.25, 0.20))
      for dx in (0.0, 0.002)],
    kk.Geom("box", (SHAFT_X0 + (TIP_END - TIP_LEN + 0.002 - SHAFT_X0) / 2, 0.0, 0.0),
            (TIP_END - TIP_LEN + 0.002 - SHAFT_X0, SHAFT_W, SHAFT_W), color=SHAFT_C),
    *[kk.Geom("sph", (x, 0.0, 0.0), (TIP_R,), color=TIP_C, friction=(0.45, 0.40)) for x in TIP_XS],
]

# -- the transport tube on its stand (one free body) ---------------------------------------------------------------
TUBE_X, TUBE_Z = 0.200, TOP + 0.030  # tube axis (along world y), held 3 cm above the bench by its stand
TUBE_OD, TUBE_ID, TUBE_L = 0.0140, 0.0112, 0.165  # OD/ID estimates; the real tube is 153.975 mm (spacer: README)
Y_MOUTH = -0.130  # the tube's mouth faces -y (toward the robot's right arm); its closed end is at Y_MOUTH + TUBE_L
KIT_POS = np.array([TUBE_X, Y_MOUTH + TUBE_L / 2, TOP])  # kit frame: under the tube's middle, at the bench
SADDLES_Y = (-0.040, 0.010)  # kit frame y of the stand's two saddles
HOLD_Y = 0.050  # kit frame y where a hand can pinch the tube (clear of the saddles)


def _tube_geoms():
    out, n = [], 12
    zc = TUBE_Z - TOP
    wall = (TUBE_OD - TUBE_ID) / 2
    rm = TUBE_ID / 2 + wall / 2
    w = 2 * math.pi * (TUBE_ID / 2 + wall) / n * 1.2
    for i in range(n):
        th = 2 * math.pi * i / n
        c = (rm * math.cos(th), 0.0, zc + rm * math.sin(th))
        q = kk.quat_axis((0, 1, 0), -th)  # box x radial, z tangent ... rotate about the tube (y) axis
        out.append(kk.Geom("box", c, (wall, TUBE_L, w), q, color=TUBE_C, contact=(0.001, 0.0)))
    out.append(kk.Geom("box", (0.0, TUBE_L / 2 - 0.001, zc), (TUBE_OD, 0.002, TUBE_OD), color=TUBE_C))  # closed end
    # the stand: a base plate (from the mouth back) and two saddles under the tube; an end stop behind the closed end
    y0, y1 = -TUBE_L / 2 + 0.005, TUBE_L / 2 + 0.011
    out.append(kk.Geom("box", (0.0, (y0 + y1) / 2, 0.003), (0.050, y1 - y0, 0.006), color=TRAY_C))
    h = zc - TUBE_OD / 2 - 0.006
    for yy in SADDLES_Y:
        out.append(kk.Geom("box", (0.0, yy, 0.006 + h / 2), (0.020, 0.012, h), color=TRAY_C))
    out.append(kk.Geom("box", (0.0, TUBE_L / 2 + 0.008, 0.006 + (zc + TUBE_OD / 2 - 0.006) / 2),
                       (0.020, 0.006, zc + TUBE_OD / 2 - 0.006), color=TRAY_C))
    return out


KIT = kk.part("kit", tuple(KIT_POS), _tube_geoms(), mass=0.10, color=TRAY_C, friction=(0.6, 0.5),
              contact=(0.001, 0.0), rigid={"solver_position_iteration_count": 32, "solver_velocity_iteration_count": 4})

# the swab starts in the tube: plug in the mouth, grip just outside it
SWAB_POS = (TUBE_X, Y_MOUTH - GRIP_L / 2, TUBE_Z)
SWAB = kk.part("swab", SWAB_POS, SWAB_GEOMS, mass=SWAB_MASS, color=CAP_C, yaw=math.pi / 2, friction=(0.9, 0.8),
               contact=(0.001, 0.0), rigid={"solver_position_iteration_count": 32, "solver_velocity_iteration_count": 4})

OBJECTS = [HEAD, KIT, SWAB]
kk.watch_points("swab", "head")
kk.watch_points("swab", "kit")

# -- scoring -------------------------------------------------------------------------------------------------------------
F_WALL = 0.20  # N: the tip is pressed on the wall (about 20 g; real trials log it from load cells under the insert)
F_STRAY = 0.05  # N: any tip contact elsewhere counts as a touch
RIM = 0.008  # m: tip contacts up to this far outside a nostril's opening (on its rim) are not touches of the face
DEPTH_MIN = TIP_LEN / 2  # m: tip centre this deep: the whole foam tip is inside the nostril
DEPTH_MAX = 0.025 - TIP_LEN / 2  # m: the tip's end no deeper than 2.5 cm
CIRCLES = 4.0  # full circles round the wall per nostril
SHARE = 0.70  # share of the time at sampling depth that the tip is pressed on the wall
PUSH_N = 2.0  # N: push on the seated cap that counts as pushed home (a free tube and stand slide under less)
PUSH_STEPS = 5  # consecutive steps (0.25 s) at that push
SEAT_TOL = 0.0015  # m: the grip's face this close to the tube's mouth: plug fully in
RELEASE = 0.015  # m: no finger pad within this distance of the cap's grip at the end
F_MAX = 5.0  # N: a wall force above this at sampling depth is reported (too_hard), not scored
MIN_PRESSED = 200  # moving pressed steps (10 s at 20 Hz) per nostril for full credit (CDC: about 15 s)
R_MIN = 0.25  # the tip centre's elliptical radius below which a pressed step's angle is not used (swab wedged across)
TIP_TOUCH = 0.002  # m: a finger pad's face this close to the foam (tip outside the tube) touches it
HOME_STEPS = 180  # steps (9 s): the cap stays home and let go this long before the swab counts as done
MOVE_MIN = math.radians(1.0)  # a pressed step counts toward the 10 s only if the tip moved this far round the wall
SECTORS = 10  # of the twelve 30-degree sectors pressed (real trials: from the logged force's direction)
TUBE_HOLD = 0.012  # m: a pad of the hand not on the cap this close to the tube's outside holds the tube
_S: dict = {}


def _reset() -> None:
    _S.clear()
    _S.update(step=None, result=(0.0, False), last={}, stray=None, deep=False, dropped=False, latched=False, removed=False,
              hard=False, push_max=0.0, push_run=0, push_run_max=0, home=0, home_step=None,
              nost={k: dict(depth_steps=0, contact_steps=0, moving=0, travel=0.0, ang=None, fmax=0.0, dmax=0.0, sectors=set(),
                            laps=0, cur=set(), forces=[], prev=None)
                    for k in NOSTRILS})


_reset()
kk.RESET_CALLBACKS.append(_reset)


def _tip_points(pts, fs, sp, sR):
    """Contact points on the foam tip (axially past the tip's rear end, less 2 mm)."""
    ax = sR[:, 0]
    out = []
    for p, f in zip(pts, fs):
        if float((p - sp) @ ax) >= TIP_XS[0] - TIP_R - 0.002:
            out.append((np.asarray(p, float), float(f)))
    return out


def _nostril_coords(p, k, hp, hR):
    """(depth along the nostril's axis, elliptical radius: 1.0 on the wall) of point p for nostril k."""
    O = hp + hR @ (NOSTRILS[k] - HEAD_POS)
    d = p - O
    u, v = float(d @ (hR @ UX)), float(d @ (hR @ VX))
    return float(d @ (hR @ AX)), math.hypot(u / A_SEMI, v / B_SEMI)


def _which_nostril(p, hp, hR):
    """The nostril whose inside or rim (up to RIM outside the opening, 1.6 x its half-widths across) contains contact
    point p, or None (the face)."""
    best = None
    for k in NOSTRILS:
        s, r = _nostril_coords(p, k, hp, hR)
        if -RIM <= s <= NOSTRIL_DEPTH + 0.002 and r <= 1.6 and (best is None or r < best[1]):
            best = (k, r)
    return None if best is None else best[0]


def _sector(ang: float) -> int:
    return int(((ang + 2 * math.pi) % (2 * math.pi)) // (math.pi / 6))


def _in_bore(p, kp, kR):
    d = kR.T @ (p - kp)
    r = math.hypot(d[0], d[2] - (TUBE_Z - TOP))
    return r <= TUBE_ID / 2 + 0.0015 and -TUBE_L / 2 - 0.003 <= d[1] <= TUBE_L / 2


def _tube_held(sp, kp, kR) -> bool:
    """A finger pad of a hand that is not on the cap is on the tube (within TUBE_HOLD of its outside)."""
    for pp in kk.STATE.fingers.values():
        pp = np.asarray(pp, float)
        if float(np.min(np.linalg.norm(pp - sp, axis=1))) < RELEASE:
            continue  # this hand is on the cap
        d = (pp - kp) @ kR  # kit frame
        r = np.hypot(d[:, 0], d[:, 2] - (TUBE_Z - TOP))
        if np.any((r < TUBE_OD / 2 + kk.PAD_OUT + TUBE_HOLD) & (np.abs(d[:, 1]) <= TUBE_L / 2)):
            return True
    return False


def _update(objects):
    if _S["step"] == kk.STATE.step and kk.STATE.step >= 0:
        return _S["result"]
    _S["step"] = kk.STATE.step
    hp, hR = kk.pose_of("head", HEAD_POS)
    sp, sR = kk.pose_of("swab", SWAB_POS)
    kp, kR = kk.pose_of("kit", KIT_POS)
    ax = sR[:, 0]
    tip = sp + TIP_X * ax
    # -- stray touches by the tip ----------------------------------------------------------------------------------
    pts, fs = kk.STATE.points.get(("swab", "head"), (np.zeros((0, 3)), np.zeros(0)))
    wall = {k: 0.0 for k in NOSTRILS}
    for p, f in _tip_points(pts, fs, sp, sR):
        hit = _which_nostril(p, hp, hR)
        if hit is None:
            if f >= F_STRAY and _S["stray"] is None:
                _S["stray"] = "face"
        else:
            wall[hit] += f
    pts, fs = kk.STATE.points.get(("swab", "kit"), (np.zeros((0, 3)), np.zeros(0)))
    for p, f in _tip_points(pts, fs, sp, sR):
        if f >= F_STRAY and not _in_bore(p, kp, kR) and _S["stray"] is None:
            _S["stray"] = "tube or tray outside"
    if kk.STATE.fingers and not _in_bore(tip, kp, kR) and _S["stray"] is None:
        seg0 = sp + (TIP_END - TIP_LEN) * ax
        for pp in kk.STATE.fingers.values():
            rel = np.asarray(pp, float) - seg0
            t_ax = np.clip(rel @ ax, 0.0, TIP_LEN)
            if float(np.min(np.linalg.norm(rel - np.outer(t_ax, ax), axis=1))) < TIP_R + kk.PAD_OUT + TIP_TOUCH:
                _S["stray"] = "gripper"
                break
    tip_low = float(tip[2]) - TOP - TIP_R
    if tip_low < 0.0015 and _S["stray"] is None:
        _S["stray"] = "bench"
    # -- sampling in each nostril ----------------------------------------------------------------------------------
    for k in NOSTRILS:
        O = hp + hR @ (NOSTRILS[k] - HEAD_POS)
        d = tip - O
        s = float(d @ (hR @ AX))
        u, v = float(d @ (hR @ UX)), float(d @ (hR @ VX))
        st = _S["nost"][k]
        inside = math.hypot(u / A_SEMI, v / B_SEMI) <= 1.0 and s > -0.005  # the tip's centre within the opening
        if not inside:
            st["ang"] = None
            continue
        st["dmax"] = max(st["dmax"], s)
        if s > DEPTH_MAX:  # the tip's end deeper than 2.5 cm
            _S["deep"] = True
        if DEPTH_MIN <= s <= DEPTH_MAX:
            st["depth_steps"] += 1
            if wall[k] > F_MAX:
                _S["hard"] = True
            if wall[k] >= F_WALL:
                st["contact_steps"] += 1
                st["fmax"] = max(st["fmax"], wall[k])
                st["forces"].append(wall[k])
                ang = math.atan2(v / B_SEMI, u / A_SEMI)
                if math.hypot(u / A_SEMI, v / B_SEMI) < R_MIN:  # tip centre near the axis: its angle is noise
                    st["ang"] = None
                    continue
                st["sectors"].add(_sector(ang))
                if st["ang"] is not None:
                    dlt = (ang - st["ang"] + math.pi) % (2 * math.pi) - math.pi
                    if abs(dlt) <= math.pi / 2:  # a continuous move: its travel and the sectors it swept count
                        st["travel"] += dlt
                        st["moving"] += abs(dlt) >= MOVE_MIN
                        for fr in (0.25, 0.5, 0.75, 1.0):
                            st["cur"].add(_sector(st["ang"] + fr * dlt))
                else:
                    jump = None if st["prev"] is None else (ang - st["prev"] + math.pi) % (2 * math.pi) - math.pi
                    if jump is not None and abs(jump) <= math.pi / 2:
                        st["travel"] += jump  # lifted and pressed again: the way back off the wall counts against travel
                    elif jump is not None:
                        st["cur"] = set()  # a jump across the nostril: a new lap starts
                    st["cur"].add(_sector(ang))
                if len(st["cur"]) == 12:  # every 30-degree sector pressed since the last lap: one lap, either direction
                    st["laps"] += 1
                    st["cur"] = {_sector(ang)}
                st["ang"] = st["prev"] = ang
            else:
                st["ang"] = None
        else:
            st["ang"] = None
    # -- the cap ---------------------------------------------------------------------------------------------------
    dk = kR.T @ (sp - kp)  # cap centre in the kit frame
    if float((kR.T @ (sp + TIP_END * ax - kp))[1]) < -TUBE_L / 2 - 0.005:
        _S["removed"] = True  # the whole swab has been out of the tube
    tube_dir = kR @ np.array([0.0, 1.0, 0.0])
    gap = (-TUBE_L / 2) - (dk[1] + GRIP_L / 2)  # from the grip's front face to the tube's mouth (> 0: still outside)
    aligned = float(ax @ tube_dir) >= math.cos(math.radians(6.0)) and math.hypot(dk[0], dk[2] - (TUBE_Z - TOP)) < 0.003
    seated = aligned and gap <= SEAT_TOL
    push = float(kk.STATE.contacts.get(("swab", "kit"), 0.0))
    if seated and _S["removed"]:  # pushes on the cap once the swab is back (not while it is first taken out)
        _S["push_max"] = max(_S["push_max"], push)
        _S["push_run"] = _S["push_run"] + 1 if push >= PUSH_N and _tube_held(sp, kp, kR) else 0
        _S["push_run_max"] = max(_S["push_run_max"], _S["push_run"])
        if _S["push_run"] >= PUSH_STEPS and _S["removed"]:
            _S["latched"] = True
    else:
        _S["push_run"] = 0
        if gap > 0.004:
            _S["latched"] = False  # pulled out again
    held = any(float(np.min(np.linalg.norm(pp - sp, axis=1))) < RELEASE for pp in kk.STATE.fingers.values()) \
        if kk.STATE.fingers else True
    if float(sp[2]) - TOP < 0.012 and not seated and not held:  # the cap lying on the table (its grip is 1.3 cm)
        _S["dropped"] = True
    # -- score -----------------------------------------------------------------------------------------------------
    per = {}
    for k, st in _S["nost"].items():
        laps = st["laps"] + max(len(st["cur"]) - 1, 0) / 12
        circles = max(abs(st["travel"]) / (2 * math.pi), laps)  # signed travel, or laps in either direction
        share = st["contact_steps"] / max(st["depth_steps"], 1)
        credit = (min(circles, CIRCLES) / CIRCLES * min(1.0, share / SHARE)
                  * min(1.0, st["moving"] / MIN_PRESSED) * min(1.0, len(st["sectors"]) / SECTORS))
        per[k] = dict(circles=round(circles, 2), share=round(share, 2), credit=round(credit, 3),
                      sectors=len(st["sectors"]), depth_steps=st["depth_steps"], contact_steps=st["contact_steps"],
                      moving_steps=st["moving"], f_median=round(float(np.median(st["forces"])), 2) if st["forces"] else 0.0,
                      f_max=round(st["fmax"], 2), depth_max_mm=round(1000 * st["dmax"], 1))
    cap_ok = _S["latched"] and seated and not held
    _S["home"] = _S["home"] + 1 if cap_ok else 0
    if cap_ok and _S["home_step"] is None:
        _S["home_step"] = int(kk.STATE.step)
    veto = _S["stray"] is not None or _S["deep"] or _S["dropped"]  # too_hard (> 5 N) is reported only
    swab = (per["left"]["credit"] + per["right"]["credit"]) / 2
    sc = 0.0 if veto else swab * (1.0 if cap_ok else 0.4)  # an unsealed specimen keeps 40%; a capped unsampled swab 0
    done = (not veto and cap_ok and _S["home"] >= HOME_STEPS
            and all(p["circles"] >= CIRCLES and p["share"] >= SHARE and p["moving_steps"] >= MIN_PRESSED
                    and p["sectors"] >= SECTORS for p in per.values()))
    _S["last"] = dict(nostrils=per, tip_touched=_S["stray"], too_deep=_S["deep"], dropped=_S["dropped"],
                      too_hard=_S["hard"],
                      cap_gap_mm=round(1000 * gap, 1), cap_aligned=bool(aligned), cap_seated=bool(seated),
                      cap_latched=_S["latched"], swab_removed=_S["removed"], push_n=round(push, 2), push_max_n=round(_S["push_max"], 2),
                      push_steps_max=_S["push_run_max"], cap_home_step=_S["home_step"], cap_home_steps=_S["home"],
                      swab_held=bool(held), wall_force={k: round(v, 2) for k, v in wall.items()},
                      kit_shift_mm=round(1000 * float(np.linalg.norm((kp - KIT_POS)[:2])), 1))
    _S["result"] = (round(sc, 3), bool(done))
    return _S["result"]


def success(objects) -> bool:
    """Both nostrils sampled (each: >= 4 circles, pressed on >= 70% of the steps at sampling depth, >= 200 moving
    pressed steps (10 s) and >= 10 of the 12 sectors), the cap pushed home on the held tube, let go and still home 9 s
    later, and the swab never voided."""
    return _update(objects)[1]


def score(objects) -> float:
    """Per nostril, with the tip's centre 0.8-1.7 cm in and a step pressed at >= 0.2 N on that wall: circles = the larger
    of the signed angle travelled round the wall over consecutive pressed steps (moves of up to 90 degrees) and the
    laps through all twelve 30-degree sectors; share = pressed / at-depth steps; moving = pressed steps that moved >= 1
    degree round; steps with the tip's centre within 0.25 of the axis count for neither circles nor sectors. Credit = min(circles, 4)/4 x min(1, share/0.7) x min(1, moving/200) x min(1, sectors/10). Score =
    the mean credit, x 1.0 if the cap is home (seated, pushed >= 2 N for 0.25 s after the swab was out while a finger
    pad of the other hand is on the tube, then let go), else x 0.4. After a lift, a pressed step within 90 degrees of the
    last one adds that angle too (an unpressed return cancels its stroke); a larger jump starts a new lap. 0 if the swab is voided: the tip touched anything but the nostrils' insides or rims and the tube's inside, a
    finger pad touched the foam, the tip's end went deeper than 2.5 cm, or the swab was dropped. A wall force above 5 N
    is reported, not scored."""
    return _update(objects)[0]


def report() -> dict:
    return dict(_S.get("last", {}))
