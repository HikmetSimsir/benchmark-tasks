"""On the station table: a Bambu Lab A1 mini 3D printer (powered off and cold; front cover and silicone sock already
off, filament cut and unloaded), its toolhead parked 20 cm above the table. Under the toolhead, the installed hotend
(0.4 mm, heatsink 1.2 x 1.8 x 4.6 cm) sits in its pocket, its front lug just above the closed buckle's bar; a sprung
retainer in the pocket's back wall holds it the way the A1's magnet does. In front of the printer, a printed hotend
holder (a block with a slotted boss at each end): the new 0.2 mm hotend stands nozzle-down in the right slot, the left
slot is empty.

The job (Bambu's A1-series hotend replacement): open the buckle, pull the old hotend down out of the toolhead and stand
it in the holder's empty slot, push the new hotend up into the pocket until it seats against the pocket's top (its lug
up through the window in the pocket's front wall), and close the buckle under the lug.

Scored from part poses, the buckle's hinge angle and finger-pad points; see score().
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

INSTRUCTION = ("Change the 3D printer's hotend: open the buckle, take the old hotend out and stand it in the empty slot "
               "of the holder, then push the new hotend up into the toolhead until it seats and lock the buckle.")

WHITE, BED_C, FRAME_C = (0.86, 0.87, 0.89), (0.13, 0.13, 0.14), (0.24, 0.25, 0.27)
HEAD_C, GRILLE_C, BUCKLE_C = (0.82, 0.83, 0.85), (0.18, 0.18, 0.20), (0.72, 0.73, 0.76)
SINK_C, FIN_C, NOZ_C, TAG_C = (0.80, 0.81, 0.84), (0.55, 0.56, 0.60), (0.70, 0.66, 0.55), (0.20, 0.70, 0.30)
OLD_C, STAND_C = (0.30, 0.28, 0.26), (0.95, 0.55, 0.15)
C = (0.001, 0.0)  # (contact offset, rest offset) for the small parts

# -- the toolhead (frame "TH": origin at the centre of the hotend pocket's mouth on the toolhead's underside; +x away
#    from the robot, +z up). All toolhead geometry belongs to the printer body (the carriage is not simulated as free).
TH = np.array([0.375, 0.000, TOP + 0.200])
POCKET = (0.015, 0.021, 0.012)  # x, y, depth: 1.5 mm clearance each side round the 12 x 18 mm heatsink
WIN_W, WIN_H = 0.014, 0.011  # window in the pocket's front wall (y width, height from the mouth)
FRONT = -0.010  # the toolhead's front face (x, TH frame); the pocket's front wall is 2.5 mm thick
HINGE = np.array([-0.012, -0.012, 0.0])  # buckle hinge (TH frame): vertical axis at the window's right, in front
BAR_Z = (0.0020, 0.0050)  # the buckle bar's height band (TH frame z)

# -- the hotend (frame: centre of the heatsink's top face; +z up; its lug faces -x) ------------------------------------
SINK = (0.012, 0.018, 0.046)
LUG = dict(center=(-0.0095, 0.0, -0.0035), size=(0.007, 0.010, 0.004))  # x -13..-6 mm, z -5.5..-1.5 mm
NOZ_R, NOZ_H, TIP_R, TIP_H = 0.0035, 0.010, 0.0015, 0.004
HOTEND_MASS = 0.022
SEAT = np.array([-POCKET[0] / 2 + SINK[0] / 2, 0.0, POCKET[2]])  # hotend origin (TH frame) when seated (pressed
#   forward against the front wall by the retainer)


def _hotend_geoms(band_color, tag: bool):
    g = [kk.Geom("box", (0.0, 0.0, -SINK[2] / 2), SINK, color=SINK_C, contact=C),
         kk.Geom("box", LUG["center"], LUG["size"], color=SINK_C, contact=C),
         kk.Geom("cyl", (0.0, 0.0, -SINK[2] - NOZ_H / 2), (NOZ_R, NOZ_H), color=NOZ_C, contact=C),
         kk.Geom("cyl", (0.0, 0.0, -SINK[2] - NOZ_H - TIP_H / 2), (TIP_R, TIP_H), color=NOZ_C, contact=C)]
    for k in range(5):  # fins (visual)
        z = -0.020 - 0.0045 * k
        g.append(kk.Geom("box", (0.0, 0.0, z), (SINK[0] + 0.0012, SINK[1] + 0.0012, 0.0012), color=FIN_C,
                         collide=False))
    g.append(kk.Geom("box", (0.0, 0.0, -0.040), (SINK[0] + 0.0014, SINK[1] + 0.0014, 0.003), color=band_color,
                     collide=False))
    if tag:
        g.append(kk.Geom("box", (-SINK[0] / 2 - 0.0008, 0.0, -0.034), (0.0012, 0.010, 0.006), color=TAG_C,
                         collide=False))
    return g


# -- the printer: base with bed, Z tower, gantry arm and the toolhead (one 5.5 kg body, loose on the table) ----------
P0 = np.array([TH[0] + 0.040, TH[1], TOP])  # printer frame: on the table under the base's centre


def _printer_geoms():
    th = TH - P0  # the toolhead origin in the printer frame
    g = [kk.Geom("box", (0.0, 0.0, 0.035), (0.28, 0.24, 0.070), color=WHITE),
         kk.Geom("box", (-0.030, 0.0, 0.073), (0.18, 0.18, 0.006), color=BED_C),
         kk.Geom("box", (-0.141, -0.060, 0.040), (0.002, 0.070, 0.040), color=GRILLE_C, collide=False),  # screen
         kk.Geom("box", (0.080, -0.145, 0.225), (0.060, 0.050, 0.310), color=FRAME_C),  # Z tower (right, as on the A1 mini)
         kk.Geom("box", (th[0] + 0.075, -0.015, th[2] + 0.065), (0.030, 0.250, 0.030), color=FRAME_C),  # X arm
         kk.Geom("box", (th[0] + 0.0425, 0.0, th[2] + 0.065), (0.035, 0.040, 0.030), color=FRAME_C)]  # carriage

    def b(cx, cy, cz, sx, sy, sz, color=HEAD_C, **kw):
        g.append(kk.Geom("box", (th[0] + cx, th[1] + cy, th[2] + cz), (sx, sy, sz), color=color, contact=C, **kw))

    px, py, pz = POCKET
    b(0.0075, 0.0, pz + (0.075 - pz) / 2, 0.035, 0.054, 0.075 - pz)  # body above the pocket
    b(0.0075, (py / 2 + 0.027) / 2, pz / 2, 0.035, 0.027 - py / 2, pz)  # left of the pocket
    b(0.0075, -(py / 2 + 0.027) / 2, pz / 2, 0.035, 0.027 - py / 2, pz)  # right of the pocket
    b((px / 2 + 0.025) / 2, 0.0, pz / 2, 0.025 - px / 2, py, pz)  # behind the pocket
    jw = (py - WIN_W) / 2
    for s in (1, -1):  # the front wall's jambs either side of the window
        b((FRONT - px / 2) / 2, s * (WIN_W / 2 + jw / 2), pz / 2, -px / 2 - FRONT, jw, pz)
    b((FRONT - px / 2) / 2, 0.0, WIN_H + (pz - WIN_H) / 2, -px / 2 - FRONT, WIN_W, pz - WIN_H)  # lintel over the window
    b(FRONT - 0.0005, 0.0, 0.048, 0.001, 0.040, 0.040, color=GRILLE_C, collide=False)  # hotend fan grille
    b(0.0075, -0.0275, 0.050, 0.020, 0.002, 0.030, color=GRILLE_C, collide=False)  # cutter lever (right side)
    return g


PRINTER = kk.part("printer", tuple(P0), _printer_geoms(), mass=5.5, color=WHITE, friction=(0.8, 0.7),
                  rigid={"solver_position_iteration_count": 32, "solver_velocity_iteration_count": 4})

# -- the buckle: a bar on a vertical hinge at the window's right; closed, it lies under the hotend's lug; its left end
#    swings out to the front to open (hinge angle positive), as the A1's does. A tab at that free end is what a finger
#    or gripper takes.
BAR_LEN = 0.028
TAB = dict(center=(-0.006, 0.025, 0.0065), size=(0.012, 0.010, 0.007))  # buckle frame (origin on the hinge axis)
BUCKLE_POS = TH + HINGE
BUCKLE = kk.part("buckle", tuple(BUCKLE_POS), [
    kk.Geom("box", (0.0, BAR_LEN / 2, (BAR_Z[0] + BAR_Z[1]) / 2), (0.003, BAR_LEN, BAR_Z[1] - BAR_Z[0]),
            color=BUCKLE_C, contact=C),
    kk.Geom("box", TAB["center"], TAB["size"], color=BUCKLE_C, contact=C),
    kk.Geom("cyl", (0.0, 0.0, 0.006), (0.0022, 0.012), color=BUCKLE_C, collide=False)],
    mass=0.006, color=BUCKLE_C, friction=(0.6, 0.5),
    rigid={"solver_position_iteration_count": 32, "solver_velocity_iteration_count": 4})
kk.joint("buckle_hinge", "revolute", "buckle", tuple(BUCKLE_POS), "Z", parent="printer", limits=(0.0, 90.0),
         damping=5e-4)

# -- the retainer standing in for the A1's hotend magnet: a sprung wedge in the pocket's back wall that presses the
#    hotend forward against the front wall (about 0.4 N; friction then holds the hotend wherever it is pushed to).
RET_Z = 0.008
RET_X0 = POCKET[0] / 2 - 0.0005 + 0.00212  # wedge centre (TH frame x) at spawn: its front edge 0.5 mm in front of the back wall
RETAINER = kk.part("retainer", tuple(TH + np.array([RET_X0, 0.0, RET_Z])), [
    kk.Geom("box", (0.0, 0.0, 0.0), (0.003, 0.010, 0.003), kk.quat_axis((0, 1, 0), math.pi / 4), color=HEAD_C,
            contact=C, friction=(0.35, 0.30))], mass=0.010, color=HEAD_C,
    rigid={"solver_position_iteration_count": 32, "solver_velocity_iteration_count": 4})
kk.joint("retainer_slide", "prismatic", "retainer", tuple(TH + np.array([RET_X0, 0.0, RET_Z])), "X", parent="printer",
         limits=(-0.003, 0.001), stiffness=120.0, damping=0.05, target=-0.006)

# -- the hotends -------------------------------------------------------------------------------------------------
OLD = kk.part("hotend_old", tuple(TH + SEAT), _hotend_geoms(OLD_C, False), mass=HOTEND_MASS, color=SINK_C,
              friction=(0.8, 0.7), contact=C,
              rigid={"solver_position_iteration_count": 32, "solver_velocity_iteration_count": 4})

# -- the printed two-slot holder (frame: on the table under its centre); 9 x 9 mm slots in 1.1 x 1.8 cm bosses ----
STAND_POS = np.array([0.250, 0.030, TOP])
SLOT_Y = {"new": -0.065, "empty": 0.065}  # holder frame y of the two slots: the new hotend right, the empty one left
STAND_H, SLOT_W, STAND_X, STAND_Y = 0.100, 0.009, 0.040, 0.160  # printed block, 10 cm tall to the boss tops
BOSS_X, BOSS_Y, BOSS_H = 0.011, 0.018, 0.020  # a boss under each slot: the fingers pass either side of it


def _stand_geoms():
    """A block with a raised boss under each slot; the slot is a square hole down the boss for the nozzle."""
    hb = STAND_H - BOSS_H
    g = [kk.Geom("box", (0.0, 0.0, hb / 2), (STAND_X, STAND_Y, hb), color=STAND_C)]
    zc = hb + BOSS_H / 2
    wx, wy = (BOSS_X - SLOT_W) / 2, (BOSS_Y - SLOT_W) / 2
    for y in SLOT_Y.values():
        for s_ in (1, -1):
            g.append(kk.Geom("box", (s_ * (SLOT_W / 2 + wx / 2), y, zc), (wx, BOSS_Y, BOSS_H), color=STAND_C))
            g.append(kk.Geom("box", (0.0, y + s_ * (SLOT_W / 2 + wy / 2), zc), (SLOT_W, wy, BOSS_H), color=STAND_C))
    return g


STAND = kk.part("stand", tuple(STAND_POS), _stand_geoms(), mass=0.200, color=STAND_C, friction=(0.7, 0.6),
                contact=C)
NEW_IN_STAND = STAND_POS + np.array([0.0, SLOT_Y["new"], STAND_H + SINK[2]])  # heatsink resting on the holder's top
NEW = kk.part("hotend_new", tuple(NEW_IN_STAND), _hotend_geoms(SINK_C, True), mass=HOTEND_MASS, color=SINK_C,
              friction=(0.8, 0.7), contact=C,
              rigid={"solver_position_iteration_count": 32, "solver_velocity_iteration_count": 4})

OBJECTS = [PRINTER, BUCKLE, RETAINER, OLD, NEW, STAND]

# -- scoring -------------------------------------------------------------------------------------------------------
SEAT_TOL = 0.0015  # m: the new hotend's top within 1.5 mm of the pocket's top, its axis within 1.5 mm of the seat
SEAT_TILT = 4.0  # deg
LOCK_DEG = 3.0  # deg: the buckle within 3 degrees of its closed stop
SLOT_TOL, SLOT_TILT = 0.003, 8.0  # the old hotend standing in a slot: axis within 3 mm of the slot, upright to 8 deg
RELEASE = 0.010  # m: at the end no finger pad within 1 cm of the new hotend or the buckle's tab
HOLD_STEPS = 20  # 1 s at 20 Hz: the finished state, hands off and still
BED_TOP = 0.076  # printer frame z of the bed's top
_S: dict = {}


def _reset() -> None:
    _S.clear()
    _S.update(step=None, result=(0.0, False), last={}, dropped={"hotend_old": False, "hotend_new": False},
              falls={k: kk.FallWatch(0.02, 10) for k in ("hotend_old", "hotend_new")}, hold=0,
              still=kk.StillWatch(0.0015, HOLD_STEPS), open_seen=False, max_open=0.0)


_reset()
kk.RESET_CALLBACKS.append(_reset)


def _rel(pose_parent, pose_child):
    (pp, Rp), (pc, Rc) = pose_parent, pose_child
    return Rp.T @ (pc - pp), Rp.T @ Rc


def _sink_box(name):
    """The heatsink box of a hotend as (center, size, pose) for the finger checks."""
    return (0.0, 0.0, -SINK[2] / 2), SINK, kk.pose_of(name)


def _update(objects):
    st = kk.STATE.step
    if _S["step"] == st and _S["step"] is not None:
        return _S["result"]
    _S["step"] = st
    pr = kk.pose_of("printer", P0)
    th_pose = (pr[0] + pr[1] @ (TH - P0), pr[1])  # toolhead frame (TH) in the world
    # buckle hinge angle (deg; 0 closed, positive open)
    _, Rb = _rel(pr, kk.pose_of("buckle", BUCKLE_POS))
    ang = math.degrees(math.atan2(Rb[1, 0], Rb[0, 0]))
    _S["max_open"] = max(_S["max_open"], ang)
    if ang > 20.0:
        _S["open_seen"] = True
    locked = ang < LOCK_DEG
    # each hotend in the toolhead frame, and in the holder
    sp = kk.pose_of("stand", STAND_POS)
    res = {}
    for name in ("hotend_old", "hotend_new"):
        p, R = kk.pose_of(name)
        pl, Rl = _rel(th_pose, (p, R))
        tilt = kk.tilt_deg(R)
        seat_err = pl - SEAT
        seated = (abs(seat_err[2]) <= SEAT_TOL and float(np.linalg.norm(seat_err[:2])) <= SEAT_TOL + 0.001
                  and tilt <= SEAT_TILT)
        in_pocket = (abs(pl[0]) < 0.012 and abs(pl[1]) < 0.012 and pl[2] > -0.004)  # its top above the mouth
        ps, Rs = _rel(sp, (p, R))
        slot = None
        for k, y in SLOT_Y.items():
            if (abs(ps[0]) <= SLOT_TOL and abs(ps[1] - y) <= SLOT_TOL and abs(ps[2] - (STAND_H + SINK[2])) <= 0.003
                    and tilt <= SLOT_TILT):
                slot = k
        handled = any(kk.near(arm, *_sink_box(name), 0.015) for arm in kk.ARMS)
        # a drop: falls 2 cm in 0.5 s with no finger near, or its nozzle tip reaches the bed or the table
        tip_z = p[2] - (SINK[2] + NOZ_H + TIP_H) * float(R[2, 2])
        pp = pr[1].T @ (p - pr[0])
        over_bed = abs(pp[0] + 0.030) < 0.09 and abs(pp[1]) < 0.09
        on_bed = over_bed and (pr[1].T @ (np.array([p[0], p[1], tip_z]) - pr[0]))[2] < BED_TOP + 0.004
        on_table = slot is None and tip_z < TOP + 0.004 and not over_bed
        if _S["falls"][name].update(p[2], handled or in_pocket or slot is not None) or on_bed or on_table:
            _S["dropped"][name] = True
        res[name] = dict(local=pl, tilt=tilt, seated=seated, in_pocket=in_pocket, slot=slot, handled=handled)
    old, new = res["hotend_old"], res["hotend_new"]
    removed = old["slot"] is not None and not _S["dropped"]["hotend_old"]
    seated = new["seated"]
    lock_ok = seated and locked
    # hands off: no finger pad within 1 cm of the new hotend's heatsink or the buckle's tab
    bp = kk.pose_of("buckle", BUCKLE_POS)
    hands_off = not any(kk.near(arm, *_sink_box("hotend_new"), RELEASE) or
                        kk.near(arm, TAB["center"], TAB["size"], bp, RELEASE) for arm in kk.ARMS)
    still = _S["still"].update(kk.pose_of("hotend_new")[0], bp[0])
    finished = lock_ok and hands_off and still
    _S["hold"] = _S["hold"] + 1 if finished else 0
    veto = _S["dropped"]["hotend_new"]
    sc = 0.0 if veto else (0.2 * removed + 0.4 * seated + 0.3 * lock_ok + 0.1 * (_S["hold"] >= HOLD_STEPS))
    done = (not veto) and removed and _S["hold"] >= HOLD_STEPS
    _S["last"] = dict(buckle_deg=round(ang, 1), buckle_max_open_deg=round(_S["max_open"], 1), locked=bool(locked),
                      old_slot=old["slot"], old_dropped=_S["dropped"]["hotend_old"],
                      new_dropped=_S["dropped"]["hotend_new"],
                      new_local_mm=[round(1000 * float(v), 1) for v in new["local"]],
                      old_local_mm=[round(1000 * float(v), 1) for v in old["local"]],
                      new_tilt=round(new["tilt"], 1), new_seated=bool(seated), new_in_pocket=bool(new["in_pocket"]),
                      hands_off=bool(hands_off), hold_steps=_S["hold"],
                      printer_shift_mm=round(1000 * float(np.linalg.norm((pr[0] - P0)[:2])), 1))
    _S["result"] = (round(sc, 3), bool(done))
    return _S["result"]


def success(objects) -> bool:
    """The old hotend stands in a holder slot, the new hotend is seated and the buckle closed under its lug, both hands
    off and everything still for 1 s, and the new hotend was never dropped."""
    return _update(objects)[1]


def score(objects) -> float:
    """0.2 old hotend standing in a holder slot (axis within 3 mm of the slot, upright to 8 deg, not dropped on the way)
    + 0.4 new hotend seated (top within 1.5 mm of the pocket's top, within 2.5 mm of the seat sideways, tilt <= 4 deg)
    + 0.3 buckle closed (within 3 deg of its stop) with the new hotend seated + 0.1 that finished state held 1 s with
    no finger pad within 1 cm of the new hotend or the buckle's tab. 0 if the new hotend is dropped (falls 2 cm with no
    finger near it, or its nozzle reaches the bed or the table)."""
    return _update(objects)[0]


def report() -> dict:
    return dict(_S.get("last", {}))
